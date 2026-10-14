import hashlib
import json
from pathlib import Path

import pytest

from tests.quality.native_call_support import modified_bridge
from tests.quality.native_type_support import PACKAGE, write
from tests.quality.support import PROJECT
from tools.architecture.inventory import discover
from tools.architecture.native_python_context import (
    NativePythonContextReport,
    inspect_python_context,
)
from tools.architecture.native_sources import NativeInput

CONFIG = (
    '[tool.pyright]\ninclude=["src"]\nexclude=[".venv"]\n'
    'typeCheckingMode="strict"\npythonVersion="3.10"\n'
    'venvPath="."\nvenv=".venv"\nstubPath="typings"\n'
)
SCOPES = ('src', 'typings')


@pytest.fixture
def context_root(tmp_path: Path) -> Path:
    write(
        tmp_path,
        {
            'src/context_pkg/__init__.py': 'from .model import Item\n',
            'src/context_pkg/model.py': 'class Item:\n    value: int\n',
            'src/context_pkg/use.py': 'from typing import TYPE_CHECKING\nfrom external import fetch\nif TYPE_CHECKING:\n    from .model import Item as Alias\n',
            'typings/external.pyi': 'def fetch() -> int: ...\n',
        },
    )
    (tmp_path / 'pyproject.toml').write_text(CONFIG)
    (tmp_path / '.venv').symlink_to(PROJECT / '.venv', target_is_directory=True)
    return tmp_path


def observe(
    root: Path,
    *,
    configuration: tuple[str, ...] = ('pyproject.toml',),
    bridge: Path | None = None,
) -> NativePythonContextReport:
    return inspect_python_context(
        root,
        discover(root, SCOPES),
        PACKAGE,
        scopes=SCOPES,
        configuration=tuple(
            NativeInput(
                str(root / name), hashlib.sha256((root / name).read_bytes()).hexdigest()
            )
            for name in configuration
        ),
        bridge=bridge,
    )


def edited_bridge(
    root: Path,
    before: str,
    after: str,
    module: str = 'native_python_session.mjs',
) -> Path:
    directory = root / 'bridge'
    modified_bridge(directory, lambda source: source)
    target = directory / module
    text = target.read_text()
    assert before in text
    target.write_text(text.replace(before, after))
    return directory / 'native_python_context.mjs'


def test_canonical_native_config_tracked_stub_and_shared_editable_facts(
    context_root: Path,
) -> None:
    report = observe(context_root)
    paths = {entry.path for entry in report.sources}
    assert (
        report.primary_config,
        set(report.tracked),
        report.stub_inputs,
        set(report.tracked) | set(report.stub_inputs),
        {entry.module for entry in report.loaded if entry.path in paths},
        all(entry.python == '3.10' for entry in report.environments),
        (PROJECT / '.venv/lib/python3.10/site-packages/_editable_impl_fly_brain.pth')
        .read_text()
        .strip()
        in report.environments[0].import_roots,
    ) == (
        str(context_root / 'pyproject.toml'),
        {
            str(context_root / path)
            for path in (
                'src/context_pkg/__init__.py',
                'src/context_pkg/model.py',
                'src/context_pkg/use.py',
            )
        },
        (str(context_root / 'typings/external.pyi'),),
        paths,
        {'context_pkg', 'context_pkg.model', 'context_pkg.use', 'external'},
        True,
        True,
    )


def test_normal_site_packages_layout_keeps_native_context_distinctions(
    context_root: Path,
) -> None:
    (context_root / '.venv').unlink()
    library = context_root / '.venv/lib/python3.10/site-packages'
    library.mkdir(parents=True)
    report = observe(context_root)
    assert (
        report.host_kind,
        report.venv,
        report.venv_path,
        str(library) in report.environments[0].import_roots,
    ) == (
        0,
        '.venv',
        str(context_root),
        True,
    )


def test_native_json_precedence_and_declared_extended_config(
    context_root: Path,
) -> None:
    base = context_root / 'base.json'
    base.write_text(
        json.dumps(
            {
                'include': ['src'],
                'exclude': ['.venv'],
                'pythonVersion': '3.10',
                'typeCheckingMode': 'strict',
                'venvPath': '.',
                'venv': '.venv',
                'stubPath': 'typings',
            }
        )
    )
    primary = context_root / 'pyrightconfig.json'
    primary.write_text(json.dumps({'extends': './base.json'}))
    with pytest.raises(ValueError, match='configuration chain'):
        observe(context_root, configuration=('pyproject.toml', 'pyrightconfig.json'))
    report = observe(
        context_root,
        configuration=('pyproject.toml', 'pyrightconfig.json', 'base.json'),
    )
    assert (
        report.primary_config,
        str(base) in {entry.path for entry in report.read_inputs},
    ) == (str(primary), True)


@pytest.mark.parametrize(
    'change',
    (
        ('typeCheckingMode="strict"', 'typeCheckingMode="basic"'),
        ('include=["src"]', 'include=["missing"]'),
        ('exclude=[".venv"]', 'exclude=[".venv","src/context_pkg/model.py"]'),
    ),
)
def test_native_config_weakening_and_omission_fail_closed(
    context_root: Path,
    change: tuple[str, str],
) -> None:
    (context_root / 'pyproject.toml').write_text(CONFIG.replace(*change))
    with pytest.raises(ValueError, match='COV002'):
        observe(context_root)


def test_undeclared_primary_config_cannot_replace_native_toml(
    context_root: Path,
) -> None:
    (context_root / 'pyrightconfig.json').write_text(
        json.dumps(
            {
                'include': ['src'],
                'pythonVersion': '3.10',
                'typeCheckingMode': 'strict',
                'venvPath': '.',
                'venv': '.venv',
                'stubPath': 'typings',
            }
        )
    )
    with pytest.raises(ValueError, match='fell back'):
        observe(context_root)


def test_foreign_editable_first_party_resolution_is_rejected(
    context_root: Path,
) -> None:
    (context_root / '.venv').unlink()
    library = context_root / '.venv/lib/python3.10/site-packages'
    library.mkdir(parents=True)
    foreign = context_root.parent / 'foreign-source'
    write(
        foreign, {'context_pkg/__init__.py': '', 'context_pkg/hidden.py': 'value = 1\n'}
    )
    (library / 'foreign.pth').write_text(str(foreign))
    (context_root / 'src/context_pkg/use.py').write_text('import context_pkg.hidden\n')
    with pytest.raises(ValueError, match='COV002.*(foreign|unresolved)'):
        observe(context_root)


@pytest.mark.parametrize(
    'module,before,after,message',
    (
        (
            'native_python_session.mjs',
            'FullAccessHost',
            'LimitedAccessHost',
            'full host',
        ),
        (
            'native_python_observation.mjs',
            'const enumeration = service._sourceEnumerator.enumerate(0);',
            'const enumeration = service._sourceEnumerator.enumerate(0); enumeration.isComplete = false;',
            'incomplete',
        ),
        (
            'native_python_session.mjs',
            "await invoke(native(6074), 'ensureTomlModuleLoaded', []);",
            'await Promise.resolve();',
            'configuration',
        ),
        (
            'native_python_session.mjs',
            "request_sha256: createHash('sha256').update(text).digest('hex')",
            "request_sha256: '0'.repeat(64)",
            'provenance differs',
        ),
        (
            'native_python_session.mjs',
            'compiler_artifacts: Object.entries(HASHES).map(([path, sha256]) => ({path: join(packageRoot, path), sha256}))',
            'compiler_artifacts: []',
            'provenance differs',
        ),
    ),
)
def test_native_context_guards_have_independent_controls(
    context_root: Path,
    module: str,
    before: str,
    after: str,
    message: str,
) -> None:
    bridge = edited_bridge(context_root, before, after, module)
    with pytest.raises(ValueError, match='COV002.*' + message):
        observe(context_root, bridge=bridge)


def test_disabling_native_strict_rule_guard_admits_weak_context(
    context_root: Path,
) -> None:
    (context_root / 'pyproject.toml').write_text(
        CONFIG + 'reportUnknownVariableType="none"\n'
    )
    with pytest.raises(ValueError, match='weakened'):
        observe(context_root)
    bridge = edited_bridge(
        context_root,
        "JSON.stringify(config.diagnosticRuleSet) !== JSON.stringify(invoke(native(9963), 'getStrictDiagnosticRuleSet', []))",
        'false',
    )
    report = observe(context_root, bridge=bridge)
    assert dict(report.diagnostic_rules)['reportUnknownVariableType'] == 'none'


def test_changed_source_and_absent_native_tool_fail_closed(context_root: Path) -> None:
    sources = discover(context_root, SCOPES)
    configuration = (
        NativeInput(
            str(context_root / 'pyproject.toml'),
            hashlib.sha256((context_root / 'pyproject.toml').read_bytes()).hexdigest(),
        ),
    )
    (context_root / 'src/context_pkg/model.py').write_text('value = 2\n')
    with pytest.raises(ValueError, match='independent context discovery differs'):
        inspect_python_context(
            context_root, sources, PACKAGE, scopes=SCOPES, configuration=configuration
        )
    with pytest.raises(ValueError, match='could not complete'):
        inspect_python_context(
            context_root,
            discover(context_root, SCOPES),
            PACKAGE,
            scopes=SCOPES,
            configuration=configuration,
            node='absent-context-node',
        )


@pytest.mark.parametrize('scopes', ((), ('missing',), ('../',)))
def test_empty_missing_and_escaping_context_scopes_reject(
    context_root: Path,
    scopes: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError, match='COV002'):
        inspect_python_context(
            context_root, (), PACKAGE, scopes=scopes, configuration=()
        )


def test_native_syntax_error_is_not_a_context_verdict(context_root: Path) -> None:
    (context_root / 'src/context_pkg/model.py').write_text('def broken(:\n')
    with pytest.raises(ValueError, match='COV002'):
        observe(context_root)


def test_runtime_and_semantic_capabilities_remain_unavailable(
    context_root: Path,
) -> None:
    report = observe(context_root)
    for capability in (
        'declarations',
        'types',
        'calls',
        'alias_resolution',
        'effects',
        'control_flow',
        'runtime_targets',
        'runtime_environment_equivalence',
    ):
        with pytest.raises(ValueError, match='COV002: native Python context lacks'):
            report.require(capability)


def test_missing_compiler_artifact_is_a_coverage_failure(context_root: Path) -> None:
    absent = context_root / 'absent-compiler'
    absent.mkdir()
    with pytest.raises(ValueError, match='COV002'):
        inspect_python_context(
            context_root,
            discover(context_root, SCOPES),
            absent,
            scopes=SCOPES,
            configuration=(
                NativeInput(
                    str(context_root / 'pyproject.toml'),
                    hashlib.sha256(
                        (context_root / 'pyproject.toml').read_bytes()
                    ).hexdigest(),
                ),
            ),
        )
