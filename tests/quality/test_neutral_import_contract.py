import inspect
from collections.abc import Mapping
from pathlib import Path

import pytest

from tests.quality.support import PROJECT, run
from tools.architecture import neutral_import_contract as adapter
from tools.architecture import neutral_import_scope as scope_adapter

pytestmark = pytest.mark.unit
NEUTRAL = 'neutral_modules = ["fly_brain.simulation.identifiers"]'
FOREIGN = 'foreign_roots = ["fly_brain.simulation", "fly_brain.qualification", "mlx", "brian2", "torch"]'
CONFIG = f"""[tool.importlinter]
root_package = "fly_brain"
include_external_packages = true
contract_types = ["neutral_imports: tools.architecture.neutral_import_contract.NeutralImportContract"]

[[tool.importlinter.contracts]]
name = "Spike comparison has no execution framework"
type = "neutral_imports"
source_root = "fly_brain.comparison"
{FOREIGN}
{NEUTRAL}
"""
VALUE = (PROJECT / 'src/fly_brain/simulation/identifiers.py').read_text()


def source_fixture(
    root: Path, source: str, extras: Mapping[str, str | None] | None = None
) -> None:
    files: dict[str, str | None] = {
        'fly_brain/__init__.py': '',
        'fly_brain/comparison/__init__.py': '',
        'fly_brain/comparison/models.py': source,
        'fly_brain/simulation/__init__.py': '',
        'fly_brain/simulation/identifiers.py': VALUE,
        'fly_brain/simulation/backend.py': 'VALUE = 1\n',
        'fly_brain/qualification/__init__.py': '',
        'fly_brain/qualification/implementation.py': 'VALUE = 1\n',
    }
    files.update(extras or {})
    for name, content in files.items():
        if content is None:
            continue
        path = root / 'src' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    (root / 'pyproject.toml').write_text(CONFIG)


def lint(root: Path) -> tuple[int, str]:
    result = run(
        [
            str(PROJECT / '.venv/bin/lint-imports'),
            '--config',
            'pyproject.toml',
            '--no-cache',
        ],
        root,
        {'PYTHONPATH': str(root / 'src') + ':' + str(root) + ':' + str(PROJECT)},
    )
    return result.returncode, result.stdout + result.stderr


def rejected(root: Path, *evidence: str) -> None:
    code, output = lint(root)
    assert code != 0, output
    for expected in evidence:
        assert expected in output, output


def checker_source() -> str:
    return (
        inspect.getsource(scope_adapter)
        + '\n'
        + inspect.getsource(adapter).replace(
            'from tools.architecture.neutral_import_scope import source_scope\n', ''
        )
    )


def checker(root: Path, source: str) -> None:
    (root / 'mutant.py').write_text(source)
    (root / 'pyproject.toml').write_text(
        CONFIG.replace(
            'tools.architecture.neutral_import_contract.NeutralImportContract',
            'mutant.NeutralImportContract',
        )
    )


@pytest.mark.parametrize(
    'source,line',
    (
        ('import fly_brain.simulation.backend\n', 1),
        ('import fly_brain.simulation.backend as alias\n', 1),
        ('from fly_brain.simulation.backend import VALUE as Alias\n', 1),
        (
            'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from fly_brain.simulation.backend import VALUE\n',
            3,
        ),
        (
            'def capture():\n    from fly_brain.simulation.backend import VALUE\n    def inner(): return VALUE\n    return inner\n',
            2,
        ),
    ),
)
def test_native_source_import_forms_are_rejected_and_repaired(
    tmp_path: Path, source: str, line: int
) -> None:
    source_fixture(tmp_path, source)
    rejected(
        tmp_path,
        'DEP003',
        f'fly_brain.comparison.models -> fly_brain.simulation.backend (l.{line})',
    )
    (tmp_path / 'src/fly_brain/comparison/models.py').write_text(
        'from fly_brain.simulation.identifiers import TrialId\n'
    )
    assert lint(tmp_path)[0] == 0


@pytest.mark.parametrize(
    'module',
    (
        'fly_brain.bridge',
        'fly_brain.comparison.facade',
        'fly_brain.simulation.identifiers',
    ),
)
def test_native_transitive_and_reexport_paths_remain_intact(
    tmp_path: Path, module: str
) -> None:
    filename = module.replace('.', '/') + '.py'
    source_fixture(
        tmp_path,
        f'from {module} import VALUE\n',
        {filename: 'from fly_brain.simulation.backend import VALUE\n'},
    )
    rejected(
        tmp_path,
        'DEP003',
        f'fly_brain.comparison.models -> {module} (l.1)',
        f'{module} -> fly_brain.simulation.backend (l.1)',
    )


def test_new_comparison_and_simulation_nodes_are_discovered(tmp_path: Path) -> None:
    source_fixture(
        tmp_path,
        'from fly_brain.simulation.identifiers import TrialId\n',
        {
            'fly_brain/comparison/new_consumer.py': 'from fly_brain.simulation.new_backend import VALUE\n',
            'fly_brain/simulation/new_backend.py': 'VALUE = 2\n',
        },
    )
    rejected(
        tmp_path,
        'DEP003',
        'fly_brain.comparison.new_consumer -> fly_brain.simulation.new_backend (l.1)',
    )


def test_close_names_comments_and_strings_do_not_create_import_permissions_or_edges(
    tmp_path: Path,
) -> None:
    source_fixture(
        tmp_path,
        '# import fly_brain.simulation.backend\ntext = "fly_brain.simulation.backend"\nfrom fly_brain.simulation.identifiers import TrialId\n',
    )
    assert lint(tmp_path)[0] == 0
    (tmp_path / 'src/fly_brain/simulation/identifiers_extra.py').write_text(
        'VALUE = 1\n'
    )
    (tmp_path / 'src/fly_brain/comparison/models.py').write_text(
        'from fly_brain.simulation.identifiers_extra import VALUE\n'
    )
    rejected(
        tmp_path,
        'DEP003',
        'fly_brain.comparison.models -> fly_brain.simulation.identifiers_extra (l.1)',
    )


@pytest.mark.parametrize(
    'original,replacement',
    (
        ('source_root = "fly_brain.comparison"', 'source_root = "fly_brain.absent"'),
        (
            NEUTRAL,
            'neutral_modules = []',
        ),
        (
            NEUTRAL,
            'neutral_modules = ["fly_brain.simulation.*"]',
        ),
        (
            NEUTRAL,
            'neutral_modules = ["fly_brain.simulation.backend"]',
        ),
        (FOREIGN, 'foreign_roots = []'),
        (NEUTRAL, 'neutral_modules = "fly_brain.simulation.identifiers"'),
        (NEUTRAL, 'neutral_modules = [false]'),
        (NEUTRAL, 'neutral_modules = [""]'),
        ('include_external_packages = true', 'include_external_packages = false'),
        (
            'include_external_packages = true',
            'include_external_packages = true\nexclude_type_checking_imports = true',
        ),
        (
            'source_root = "fly_brain.comparison"',
            'source_root = "fly_brain.comparison"\nignore_imports = ["fly_brain.comparison -> fly_brain.simulation"]',
        ),
    ),
)
def test_invalid_or_weakened_native_configuration_fails_closed(
    tmp_path: Path, original: str, replacement: str
) -> None:
    source_fixture(tmp_path, 'from fly_brain.simulation.identifiers import TrialId\n')
    (tmp_path / 'pyproject.toml').write_text(CONFIG.replace(original, replacement))
    rejected(tmp_path, 'COV002')


@pytest.mark.parametrize(
    'missing', ('comparison', 'simulation', 'qualification', 'identifiers')
)
def test_missing_native_scope_never_returns_a_kept_contract(
    tmp_path: Path, missing: str
) -> None:
    omitted = {
        'comparison': {
            'fly_brain/comparison/__init__.py': None,
            'fly_brain/comparison/models.py': None,
        },
        'simulation': {
            'fly_brain/simulation/__init__.py': None,
            'fly_brain/simulation/identifiers.py': None,
            'fly_brain/simulation/backend.py': None,
        },
        'qualification': {
            'fly_brain/qualification/__init__.py': None,
            'fly_brain/qualification/implementation.py': None,
        },
        'identifiers': {'fly_brain/simulation/identifiers.py': None},
    }
    source_fixture(tmp_path, '', omitted[missing])
    rejected(tmp_path, 'COV002')


@pytest.mark.parametrize(
    'guard,replacement,source,extras',
    (
        (
            'graph.find_descendants(source_root)',
            "{'fly_brain.comparison.models'}",
            'pass\n',
            {
                'fly_brain/comparison/new.py': 'from fly_brain.simulation.backend import VALUE\n'
            },
        ),
        (
            'foreign.update(graph.find_descendants(root))',
            'foreign.update(())',
            'from fly_brain.simulation.new_backend import VALUE\n',
            {'fly_brain/simulation/new_backend.py': 'VALUE = 1\n'},
        ),
        (
            "'allow_indirect_imports': 'false'",
            "'allow_indirect_imports': 'true'",
            'from fly_brain.bridge import VALUE\n',
            {'fly_brain/bridge.py': 'from fly_brain.simulation.backend import VALUE\n'},
        ),
        (
            'foreign - set(neutral_modules)',
            "foreign - {'fly_brain.simulation.backend'}",
            'from fly_brain.simulation.backend import VALUE\n',
            {},
        ),
    ),
)
def test_weakening_each_native_discovery_path_or_exact_neutral_exception_loses_its_violation(
    tmp_path: Path, guard: str, replacement: str, source: str, extras: dict[str, str]
) -> None:
    source_fixture(tmp_path, source, extras)
    rejected(tmp_path, 'DEP003')
    code = checker_source()
    assert guard in code
    checker(tmp_path, code.replace(guard, replacement))
    status, output = lint(tmp_path)
    assert status == 0, output


@pytest.mark.parametrize(
    'module', ('fly_brain.qualification.implementation', 'mlx', 'brian2', 'torch')
)
def test_intrinsic_other_framework_prohibitions_remain_native_paths(
    tmp_path: Path, module: str
) -> None:
    source_fixture(tmp_path, f'import {module}\n')
    rejected(tmp_path, 'DEP003', f'fly_brain.comparison.models -> {module} (l.1)')


def test_exact_neutral_node_does_not_approve_package_descendants(
    tmp_path: Path,
) -> None:
    source_fixture(
        tmp_path,
        'from fly_brain.simulation.identifiers.hidden import VALUE\n',
        {
            'fly_brain/simulation/identifiers.py': None,
            'fly_brain/simulation/identifiers/__init__.py': VALUE,
            'fly_brain/simulation/identifiers/hidden.py': 'VALUE = 1\n',
        },
    )
    rejected(
        tmp_path,
        'DEP003',
        'fly_brain.comparison.models -> fly_brain.simulation.identifiers.hidden (l.1)',
    )


def test_empty_discovered_comparison_scope_and_native_parse_error_fail(
    tmp_path: Path,
) -> None:
    source_fixture(tmp_path, '', {'fly_brain/comparison/models.py': None})
    rejected(tmp_path, 'COV002')
    (tmp_path / 'src/fly_brain/comparison/models.py').write_text('def broken(:\n')
    rejected(tmp_path, 'Syntax error')


@pytest.mark.parametrize(
    'anchor,fault,guard,diagnostic',
    (
        (
            'required = {source_root',
            "graph.squash_module('fly_brain.simulation.backend')\n    required = {source_root",
            'any(graph.is_module_squashed(m) for m in (*source, *internal))',
            'squashed internal module inventory',
        ),
        (
            'result = native.check(graph, verbose=verbose)',
            "result = native.check(graph, verbose=verbose)\n        result.warnings.append('native analysis warning')",
            'result.ignored_import_count or result.warnings',
            'native contract ignored imports or warned',
        ),
        (
            'result = native.check(graph, verbose=verbose)',
            'result = native.check(graph, verbose=verbose)\n        result.ignored_import_count = 1',
            'result.ignored_import_count or result.warnings',
            'native contract ignored imports or warned',
        ),
    ),
)
def test_native_inventory_and_framework_failures_have_independent_rejection_guards(
    tmp_path: Path, anchor: str, fault: str, guard: str, diagnostic: str
) -> None:
    source_fixture(tmp_path, 'from fly_brain.simulation.identifiers import TrialId\n')
    source = checker_source()
    assert anchor in source
    faulty = source.replace(anchor, fault)
    checker(tmp_path, faulty)
    rejected(tmp_path, 'COV002', diagnostic)
    checker(tmp_path, faulty.replace(guard, 'False'))
    status, output = lint(tmp_path)
    assert status == 0, output
