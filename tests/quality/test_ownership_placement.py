import inspect
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType
from typing import cast

import pytest

from tests.quality.ownership_placement_support import (
    ROOTS,
    SOURCE,
    native_inputs,
    policy_binding,
    without_policy_scope,
)
from tools.architecture import ownership_placement
from tools.architecture.inventory import Finding
from tools.architecture.policy import Owner, Role
from tools.architecture.semantic_policy_records import Placement
from tools.architecture.semantic_policy_validation import (
    ValidatedSemanticInputs,
    validate_semantic_inputs,
)

pytestmark = pytest.mark.unit


def test_violation_has_native_identity_location_and_a_real_move_repairs_it(
    tmp_path: Path,
) -> None:
    bad, _ = native_inputs(tmp_path / 'bad', {'shared/value.py': SOURCE})
    finding = next(
        f for f in ownership_placement.check(bad) if ':policy:function:0]' in f.message
    )
    assert (finding.rule, finding.path, finding.line) == (
        'OWN001',
        'shared/value.py',
        3,
    )
    assert 'shared/value.py:3:4 [active:policy:function:0]' in finding.message
    assert "('src/owned', 'tests/owned', 'docs/owned')" in finding.message
    repaired, _ = native_inputs(tmp_path / 'repaired', {'src/owned/value.py': SOURCE})
    assert ownership_placement.check(repaired) == ()
    assert (
        policy_binding(bad).anchor.source_sha256
        == policy_binding(repaired).anchor.source_sha256
    )
    with pytest.raises(ValueError, match='COV002:.*not executed 37-rule'):
        repaired.require_semantic_compliance()


@pytest.mark.parametrize('root', ROOTS)
def test_reviewed_source_test_and_documentation_roots_include_descendants(
    tmp_path: Path, root: str
) -> None:
    inputs, _ = native_inputs(tmp_path, {root + '/nested/value.py': SOURCE})
    assert ownership_placement.check(inputs) == ()


@pytest.mark.parametrize(
    'role',
    (
        'entrypoint',
        'composition',
        'infrastructure',
        'external_adapter',
        'tooling',
        'system_test',
        'typing_contract',
    ),
)
def test_exact_reviewed_outside_role_is_allowed_but_is_not_a_global_grant(
    tmp_path: Path, role: Role
) -> None:
    inputs, _ = native_inputs(
        tmp_path, {'shared/value.py': SOURCE}, role=role, outside_role=role
    )
    assert ownership_placement.check(inputs) == ()
    unapproved = replace(
        inputs,
        document=inputs.document.model_copy(
            update={
                'placement': (Placement(owner='example', roots=ROOTS),),
            }
        ),
    )
    assert {f.rule for f in ownership_placement.check(unapproved)} == {'OWN001'}


def test_prefix_alias_and_reexport_cannot_move_the_original_declaration(
    tmp_path: Path,
) -> None:
    inputs, observation = native_inputs(
        tmp_path,
        {
            'src/owned_extra.py': SOURCE,
            'src/owned/api.py': 'from src.owned_extra import Value as Public\n',
        },
    )
    findings = ownership_placement.check(inputs)
    assert any(
        f.path == 'src/owned_extra.py' and ':Value:class:0]' in f.message
        for f in findings
    )
    assert not any(f.path == 'src/owned/api.py' for f in findings)
    assert any(
        r.target.name == 'Value' and r.kind == 'import'
        for r in observation.model.references
    )


@pytest.mark.parametrize(
    'root', ('../owned', '/owned', 'src/own*', 'src//owned', 'src/../owned')
)
def test_root_escapes_and_nonexact_paths_remain_analysis_failures(
    tmp_path: Path, root: str
) -> None:
    inputs, observation = native_inputs(tmp_path, {'src/owned/value.py': SOURCE})
    document = inputs.document.model_copy(
        update={'placement': (Placement(owner='example', roots=(root,)),)}
    )
    with pytest.raises(ValueError, match='COV002:.*not exact and relative'):
        validate_semantic_inputs(tmp_path, document, {'active': observation})


@pytest.mark.parametrize(
    'defect',
    ('binding', 'context', 'scope', 'partial_scope', 'placement', 'hash', 'capability'),
)
def test_incomplete_validated_inputs_cannot_be_used_as_clean_placement(
    tmp_path: Path, defect: str
) -> None:
    inputs, _ = native_inputs(tmp_path, {'src/owned/value.py': SOURCE})
    binding = policy_binding(inputs)
    altered = dict(inputs.bindings)
    altered.pop(binding.symbol)
    documents = {
        'context': inputs.document.model_copy(update={'contexts': ()}),
        'scope': inputs.document.model_copy(
            update={
                'applicability': tuple(
                    r for r in inputs.document.applicability if r.rule != 'OWN001'
                )
            }
        ),
        'placement': inputs.document.model_copy(update={'placement': ()}),
    }
    variants = {
        'binding': replace(inputs, bindings=MappingProxyType(altered)),
        'partial_scope': without_policy_scope(inputs),
        'hash': replace(inputs, input_hashes=MappingProxyType({})),
        'capability': replace(inputs, missing_capabilities=('declaration_identity',)),
        **{
            name: replace(inputs, document=document)
            for name, document in documents.items()
        },
    }
    with pytest.raises(ValueError, match='COV002: OWN001.*value.py:'):
        ownership_placement.check(variants[defect])


def test_unknown_owner_is_located_and_empty_domain_scope_is_not_compliance(
    tmp_path: Path,
) -> None:
    inputs, _ = native_inputs(tmp_path, {'src/owned/value.py': SOURCE})
    binding = policy_binding(inputs)
    bad = binding.model_copy(update={'owner': 'absent'})
    altered = {**inputs.bindings, binding.symbol: bad}
    document = inputs.document.model_copy(
        update={'semantic_bindings': tuple(altered.values())}
    )
    with pytest.raises(
        ValueError,
        match='COV002: OWN001 src/owned/value.py:3:4.*unknown reviewed owner',
    ):
        ownership_placement.check(
            replace(inputs, document=document, bindings=MappingProxyType(altered))
        )
    document = inputs.document.model_copy(
        update={
            'owners': {
                'example': Owner(
                    kind='tooling', responsibility='Reviewed absence of domain symbols'
                )
            }
        }
    )
    with pytest.raises(
        ValueError, match='COV002: OWN001.*domain placement scope is empty'
    ):
        ownership_placement.check(replace(inputs, document=document))


def test_independent_path_and_outside_permission_weakening_lose_real_defects(
    tmp_path: Path,
) -> None:
    inputs, _ = native_inputs(tmp_path, {'src/owned_extra.py': SOURCE}, role='tooling')
    assert ownership_placement.check(inputs)
    source = inspect.getsource(ownership_placement.check)
    guards = (
        ('path.is_relative_to(root)', 'str(path).startswith(root)'),
        ('binding.role != placement.outside_role', 'False'),
    )
    for guard, replacement in guards:
        assert guard in source
        namespace = dict(ownership_placement.__dict__)
        exec(source.replace(guard, replacement), namespace)
        weakened = cast(
            Callable[[ValidatedSemanticInputs], tuple[Finding, ...]], namespace['check']
        )
        assert weakened(inputs) == ()


@pytest.mark.parametrize('defect', ('observation', 'inventory', 'anchor'))
def test_upstream_native_observation_and_anchor_failures_never_become_placement_success(
    tmp_path: Path, defect: str
) -> None:
    inputs, observation = native_inputs(tmp_path, {'src/owned/value.py': SOURCE})
    binding = policy_binding(inputs)
    contexts = tuple(
        c.model_copy(update={'expected_bindings': c.expected_bindings[:-1]})
        for c in inputs.document.contexts
    )
    anchors = tuple(
        b.model_copy(update={'anchor': b.anchor.model_copy(update={'column': 99})})
        if b.symbol == binding.symbol
        else b
        for b in inputs.document.semantic_bindings
    )
    documents = {
        'observation': inputs.document,
        'inventory': inputs.document.model_copy(update={'contexts': contexts}),
        'anchor': inputs.document.model_copy(update={'semantic_bindings': anchors}),
    }
    observations = {} if defect == 'observation' else {'active': observation}
    with pytest.raises(ValueError, match='COV002') as failure:
        validate_semantic_inputs(tmp_path, documents[defect], observations)
    if defect == 'anchor':
        assert 'src/owned/value.py:3:4' in str(failure.value)


def test_empty_observed_scope_and_weakened_coverage_have_independent_controls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs, _ = native_inputs(tmp_path, {'src/owned/value.py': SOURCE})
    with pytest.raises(ValueError, match='COV002: OWN001 <policy>:1:0:.*empty'):
        ownership_placement.check(replace(inputs, bindings=MappingProxyType({})))
    partial = without_policy_scope(inputs)
    with pytest.raises(
        ValueError, match='COV002: OWN001 src/owned/value.py:3:4.*omitted'
    ):
        ownership_placement.check(partial)
    source = inspect.getsource(ownership_placement.domain_scope)
    guard = 'key in scopes[key.context]'
    assert guard in source
    namespace = dict(ownership_placement.domain_scope.__globals__)
    exec(source.replace(guard, 'True'), namespace)
    monkeypatch.setattr(ownership_placement, 'domain_scope', namespace['_domain_scope'])
    weakened = ownership_placement.check
    assert weakened(partial) == ()
