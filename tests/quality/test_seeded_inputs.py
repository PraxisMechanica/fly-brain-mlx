import inspect
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

from tests.quality.support import PROJECT
from tools.architecture.compiler import Compiler
from tools.architecture.inventory import Finding, discover
from tools.architecture.seeded_inputs import Scope, analyze, check, select
from tools.architecture.symbols import Location, SemanticModel, Symbol

pytestmark = pytest.mark.unit

PROVIDER = (
    'def uniforms(seed: int) -> float:\n    return 0.25\n'
    'class Sampler:\n    def __init__(self) -> None: pass\n'
)
SCOPES = (
    Scope('provider.py', '<module>', 'provider', 'module'),
    Scope('provider.py', 'uniforms', 'provider', 'external_adapter'),
    Scope('provider.py', 'Sampler', 'provider', 'external_adapter'),
    Scope('provider.py', 'Sampler.__init__', 'provider', 'external_adapter'),
    Scope('rule.py', '<module>', 'experiment', 'module'),
    Scope('rule.py', 'calculate', 'experiment', 'rules'),
    Scope('facade.py', '<module>', 'provider', 'module'),
    Scope('helper.py', '<module>', 'experiment', 'module'),
    Scope('helper.py', 'acquire', 'experiment', 'service'),
)


def resolved(root: Path, rule: str) -> SemanticModel:
    files = {
        'provider.py': PROVIDER,
        'facade.py': 'from provider import uniforms as read\n',
        'helper.py': 'from facade import read\ndef acquire() -> float:\n    return read(7)\n',
        'rule.py': rule,
    }
    for name, source in files.items():
        (root / name).write_text(source)
    with Compiler(root, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        return analyze(root, discover(root, tuple(files)), compiler)


def checked(model: SemanticModel) -> tuple[Finding, ...]:
    return check(
        model,
        SCOPES,
        (select(model, 'provider.py', 'uniforms'),),
        (select(model, 'provider.py', 'Sampler'),),
    )


@pytest.mark.parametrize(
    'body',
    (
        'from provider import uniforms\ndef calculate() -> float:\n    return uniforms(7)\n',
        'from provider import uniforms as get\ndef calculate() -> float:\n    return get(7)\n',
        'from facade import read\ndef calculate() -> float:\n    return read(7)\n',
        'from helper import acquire\ndef calculate() -> float:\n    return acquire()\n',
        'from provider import uniforms\ndef calculate() -> float:\n    alias = uniforms\n    return alias(7)\n',
    ),
)
def test_resolved_effect_paths_reject_alias_reexport_wrapper_and_local_alias(
    tmp_path: Path, body: str
) -> None:
    findings = checked(resolved(tmp_path, body))
    assert any(
        f.rule == 'STATE001'
        and f.path.endswith('rule.py')
        and f.line > 1
        and 'uniforms' in f.message
        and 'completed values' in f.message
        for f in findings
    )
    repaired = resolved(
        tmp_path, 'def calculate(value: float) -> float:\n    return value + 1\n'
    )
    assert checked(repaired) == ()


def test_constructor_and_hidden_default_have_located_diagnostics(
    tmp_path: Path,
) -> None:
    model = resolved(
        tmp_path,
        'from provider import Sampler\ndef calculate(draw: Sampler = Sampler()) -> int:\n    return 7\n',
    )
    findings = checked(model)
    assert any(
        f.rule == 'DI002' and f.line == 2 and 'default' in f.message for f in findings
    )
    near = resolved(
        tmp_path, 'def calculate(value: int = 7) -> int:\n    return value\n'
    )
    assert checked(near) == ()


@pytest.mark.parametrize(
    'source',
    (
        'from typing import Callable\ndef calculate(draw: Callable[[], float]) -> float:\n    return draw()\n',
        'def calculate(draw) -> float:\n    return draw()\n',
        'def calculate() -> float:\n    return missing()\n',
        'def calculate() -> float:\n    return (lambda: 7)()\n',
    ),
)
def test_unknown_callback_target_and_unsupported_scope_fail_closed(
    tmp_path: Path, source: str
) -> None:
    with pytest.raises(ValueError, match='COV002'):
        checked(resolved(tmp_path, source))


def test_empty_unmapped_and_changed_scopes_cannot_pass(tmp_path: Path) -> None:
    model = resolved(tmp_path, 'def calculate(value: int) -> int:\n    return value\n')
    effect = select(model, 'provider.py', 'uniforms')
    with pytest.raises(ValueError, match='COV002'):
        check(model, (), (effect,))
    with pytest.raises(ValueError, match='COV002'):
        check(model, SCOPES[:-1], (effect,))
    with pytest.raises(ValueError, match='COV002'):
        check(model, SCOPES, ())
    (tmp_path / 'rule.py').write_text('def changed(): pass\n')
    with pytest.raises(ValueError, match='COV002'):
        checked(model)


def test_weakening_resolved_effect_reachability_hides_the_same_defect(
    tmp_path: Path,
) -> None:
    model = resolved(
        tmp_path,
        'from helper import acquire\ndef calculate() -> float:\n    return acquire()\n',
    )
    assert any(f.rule == 'STATE001' for f in checked(model))
    source = inspect.getsource(check)
    original = 'graph.forbidden_paths(rules, tuple((*effects, *constructors)))'
    assert original in source
    namespace = dict(check.__globals__)
    exec(source.replace(original, '()'), namespace)
    weakened = cast(Callable[..., tuple[Finding, ...]], namespace['check'])
    assert weakened(model, SCOPES, (select(model, 'provider.py', 'uniforms'),)) == ()


def test_direct_constructor_is_not_mistaken_for_an_owned_value(tmp_path: Path) -> None:
    model = resolved(
        tmp_path,
        'from provider import Sampler\ndef calculate() -> int:\n    draw = Sampler()\n    return 7\n',
    )
    assert {item.rule for item in checked(model)} == {'STATE001', 'DI002'}


def test_one_line_body_call_is_not_a_hidden_default(tmp_path: Path) -> None:
    model = resolved(
        tmp_path,
        'from provider import uniforms\ndef calculate(value: int = 7) -> float: return uniforms(value)\n',
    )
    assert {item.rule for item in checked(model)} == {'STATE001'}


def test_weakening_default_scope_loses_the_same_hidden_sampler(tmp_path: Path) -> None:
    model = resolved(
        tmp_path,
        'from provider import uniforms\ndef calculate(draw=uniforms) -> int:\n    return 7\n',
    )
    assert any(item.rule == 'DI002' for item in checked(model))
    namespace = dict(check.__globals__)
    exec(inspect.getsource(check), namespace)

    def omit_default(symbol: Symbol, location: Location) -> bool:
        return False

    namespace['_in_default'] = omit_default
    weakened = cast(Callable[..., tuple[Finding, ...]], namespace['check'])
    assert weakened(model, SCOPES, (select(model, 'provider.py', 'uniforms'),)) == ()


def test_weakening_constructor_rejection_keeps_the_effect_finding(
    tmp_path: Path,
) -> None:
    model = resolved(
        tmp_path,
        'from provider import Sampler\ndef calculate() -> int:\n    draw = Sampler()\n    return 7\n',
    )
    assert {item.rule for item in checked(model)} == {'STATE001', 'DI002'}
    namespace = dict(check.__globals__)
    source = inspect.getsource(check)
    assert 'call.target in constructors' in source
    exec(source.replace('call.target in constructors', 'False'), namespace)
    weakened = cast(Callable[..., tuple[Finding, ...]], namespace['check'])
    findings = weakened(
        model,
        SCOPES,
        (select(model, 'provider.py', 'uniforms'),),
        (select(model, 'provider.py', 'Sampler'),),
    )
    assert {item.rule for item in findings} == {'STATE001'}
