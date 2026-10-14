from pathlib import Path

import pytest

from tests.quality.support import git, repository
from tools.code_quality import changes, impact
from tools.code_quality.change_inputs import resolve_inputs
from tools.code_quality.changes import Plan, Stage, build_plan

VALUES = 'src/fly_brain/values.py'
FACADE = 'src/fly_brain/facade.py'
USE = 'src/fly_brain/use.py'
APP = (VALUES, FACADE, USE, 'src/fly_brain/__init__.py')
CONFIG = '[project]\nname="scope-fixture"\n[tool.pyright]\ntypeCheckingMode="strict"\n[tool.ruff]\nline-length=88\n[tool.importlinter]\nroot_package="fly_brain"\n'


def write(root: Path, path: str, source: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source)
    git(root, 'add', path)


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    root = repository(tmp_path)
    git(root, 'rm', 'calculation.py')
    for path, source in {
        VALUES: 'VALUE = 1\n',
        FACADE: 'from .values import VALUE as Public\n',
        USE: 'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from .facade import Public as Alias\n',
        'src/fly_brain/__init__.py': '',
        'tests/__init__.py': '',
        'tools/__init__.py': '',
        'main.py': 'from fly_brain.use import Alias\n',
        'pyproject.toml': CONFIG,
        'README.md': 'scope fixture\n',
    }.items():
        write(root, path, source)
    git(root, 'commit', '-qm', 'Declare native scope fixture')
    return root


@pytest.mark.parametrize(
    'path,expected',
    ((VALUES, (VALUES, FACADE, USE)), ('src/fly_brain/__init__.py', APP)),
)
def test_current_native_alias_type_only_reexport_and_initializer_consumers(
    checkout: Path, path: str, expected: tuple[str, ...]
) -> None:
    write(checkout, path, 'VALUE = 2\n')
    assert build_plan(checkout, 'commit', {}) == Plan(
        (path,),
        tuple(sorted((*expected, 'main.py'))),
        (path,),
        True,
        True,
        None,
        None,
        tuple(sorted(expected)),
        git(checkout, 'write-tree'),
    )


def test_docs_and_checker_edits_select_only_their_static_inputs(checkout: Path) -> None:
    write(checkout, 'README.md', 'updated\n')
    documentation = build_plan(checkout, 'commit', {})
    identity = git(checkout, 'write-tree')
    write(checkout, 'tools/checker.py', 'VALUE = 1\n')
    checker = build_plan(checkout, 'commit', {})
    assert (documentation, checker.python, checker.format_files) == (
        Plan(('README.md',), (), (), False, False, None, None, tree=identity),
        ('tools/checker.py',),
        ('tools/checker.py',),
    )


def test_removed_edge_seeds_its_surviving_importer_and_current_consumers(
    checkout: Path,
) -> None:
    write(checkout, FACADE, 'Public = 1\n')
    assert set(build_plan(checkout, 'commit', {}).python) == {FACADE, USE, 'main.py'}


@pytest.mark.parametrize('stage', ('push', 'ci'))
def test_range_preserves_reverted_paths_and_current_consumers(
    checkout: Path, stage: Stage
) -> None:
    base = git(checkout, 'rev-parse', 'HEAD')
    write(checkout, VALUES, 'VALUE = 2\n')
    git(checkout, 'commit', '-qm', 'Change scoped native source')
    write(checkout, VALUES, 'VALUE = 1\n')
    git(checkout, 'commit', '-qm', 'Repair scoped native source')
    head = git(checkout, 'rev-parse', 'HEAD')
    environment = dict(zip(changes.RANGES[stage], (base, head), strict=True))
    plan = build_plan(checkout, stage, environment)
    assert (plan.changed, set(plan.python), plan.base, plan.head, plan.tree) == (
        (VALUES,),
        {VALUES, FACADE, USE, 'main.py'},
        base,
        head,
        git(checkout, 'rev-parse', head + '^{tree}'),
    )


@pytest.mark.parametrize('stage', ('push', 'ci'))
def test_submitted_catalog_and_cache_identity_ignore_unrelated_index_state(
    checkout: Path, stage: Stage
) -> None:
    base = git(checkout, 'rev-parse', 'HEAD')
    write(checkout, VALUES, 'VALUE = 2\n')
    git(checkout, 'commit', '-qm', 'Declare submitted source tree')
    head = git(checkout, 'rev-parse', 'HEAD')
    git(checkout, 'rm', '--cached', FACADE)
    inputs = resolve_inputs(
        checkout, stage, dict(zip(changes.RANGES[stage], (base, head), strict=True))
    )
    assert (FACADE in inputs.existing, inputs.tree) == (
        True,
        git(checkout, 'rev-parse', head + '^{tree}'),
    )


@pytest.mark.parametrize(
    'arguments', (('rm', VALUES), ('mv', VALUES, 'src/fly_brain/replacement.py'))
)
def test_unproved_deleted_native_target_fails_closed(
    checkout: Path, arguments: tuple[str, ...]
) -> None:
    git(checkout, *arguments)
    with pytest.raises(ValueError, match='COV002: unproved affected scope'):
        build_plan(checkout, 'commit', {})


@pytest.mark.parametrize(
    'context,path,source',
    (
        ('style', 'pyproject.toml', CONFIG.replace('88', '80')),
        ('types', 'pyproject.toml', CONFIG.replace('strict', 'basic')),
        (
            'imports',
            'pyproject.toml',
            CONFIG.replace('root_package="fly_brain"', 'root_package="other"'),
        ),
        ('stub', 'typings/provider.pyi', 'class Value: ...\n'),
        ('runtime', 'uv.lock', 'class Value: ...\n'),
    ),
)
def test_context_changes_invalidate_their_native_check_scopes(
    checkout: Path, context: str, path: str, source: str
) -> None:
    write(checkout, path, source)
    plan = build_plan(checkout, 'commit', {})
    current = set(APP) | {'main.py', 'tests/__init__.py', 'tools/__init__.py'}
    assert (set(plan.python), set(plan.format_files), set(plan.boundary_files)) == (
        current | {'typings/provider.pyi'}
        if context == 'stub'
        else current
        if context in ('types', 'runtime')
        else set(),
        current
        if context in ('style', 'runtime')
        else {'typings/provider.pyi'}
        if context == 'stub'
        else set(),
        set(APP) if context in ('imports', 'runtime') else set(),
    )


def test_manual_working_and_unindexed_inputs_remain_visible(checkout: Path) -> None:
    (checkout / VALUES).write_text('VALUE = 3\n')
    target = checkout / 'tools/unindexed.py'
    target.write_text('VALUE = 1\n')
    plan = build_plan(checkout, 'manual', {})
    assert (set(plan.changed), set(plan.python)) == (
        {VALUES, 'tools/unindexed.py'},
        {VALUES, FACADE, USE, 'main.py', 'tools/unindexed.py'},
    )


@pytest.mark.parametrize(
    'path,source',
    (
        (VALUES, 'def broken(:\n'),
        ('pyproject.toml', '[tool.pyright\n'),
        ('pyproject.toml', 'tool = "not a table"\n'),
        ('tools/omitted/source.py', 'VALUE = 1\n'),
        ('src/tools/__init__.py', 'VALUE = 1\n'),
    ),
)
def test_invalid_source_config_or_module_catalog_fails_closed(
    checkout: Path, path: str, source: str
) -> None:
    write(checkout, VALUES, 'VALUE = 3\n')
    write(checkout, path, source)
    with pytest.raises(ValueError, match='COV002'):
        build_plan(checkout, 'commit', {})


@pytest.mark.parametrize('stage', ('unknown', 'ci'))
def test_unknown_stage_or_missing_range_fails_closed(
    checkout: Path, stage: Stage
) -> None:
    write(checkout, VALUES, 'VALUE = 3\n')
    with pytest.raises(ValueError, match='COV002'):
        build_plan(checkout, stage, {})


def test_missing_canonical_package_fails_closed(checkout: Path) -> None:
    write(checkout, VALUES, 'VALUE = 3\n')
    (checkout / 'src/fly_brain').rename(checkout / 'src/missing')
    with pytest.raises(ValueError, match='COV002'):
        build_plan(checkout, 'commit', {})


def test_changed_native_tool_version_fails_closed(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write(checkout, VALUES, 'VALUE = 3\n')
    monkeypatch.setattr(impact.grimp, '__version__', 'unknown')
    with pytest.raises(ValueError, match='COV002'):
        build_plan(checkout, 'commit', {})


def test_canonical_native_paths_override_loaded_editable_packages(
    checkout: Path,
) -> None:
    write(checkout, 'tools/local_source.py', 'VALUE = 1\n')
    assert build_plan(checkout, 'commit', {}).python == ('tools/local_source.py',)


def test_disabling_native_dependency_selection_loses_consumer(
    checkout: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write(checkout, VALUES, 'VALUE = 2\n')
    expected = build_plan(checkout, 'commit', {})
    graph = impact.current_graph(checkout, None)
    graph.remove_import(importer='fly_brain.facade', imported='fly_brain.values')

    def incomplete(_root: Path, _tree: str | None) -> impact.grimp.ImportGraph:
        return graph

    monkeypatch.setattr(changes, 'current_graph', incomplete)
    weakened = build_plan(checkout, 'commit', {})
    assert (USE in expected.python, USE in weakened.python) == (True, False)
