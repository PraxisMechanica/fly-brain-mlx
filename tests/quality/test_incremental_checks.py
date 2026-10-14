from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest

from tests.quality.support import git, repository
from tools.code_quality import check as workflow
from tools.code_quality import gate, indexed_inputs
from tools.code_quality.change_context import compiler_context
from tools.code_quality.change_inputs import Inputs
from tools.code_quality.changes import Plan


def inputs() -> Plan:
    return Plan(
        changed=('README.md',),
        format_files=(),
        python=(),
        boundaries=False,
        metrics=False,
        base='HEAD',
        head=None,
    )


@pytest.mark.parametrize('stage', ('commit', 'push', 'ci'))
def test_document_changes_do_not_repeat_source_or_checker_test_execution(
    stage: workflow.Stage,
) -> None:
    assert [name for name, _ in workflow.tasks(inputs(), stage)] == ['inputs']


@pytest.mark.parametrize('stage', ('commit', 'push', 'ci'))
def test_delivery_keeps_regression_execution_with_the_component_owner(
    stage: workflow.Stage,
) -> None:
    plan = inputs()
    assert all(name != 'tests' for name, _ in workflow.tasks(plan, stage))


def test_changed_source_keeps_static_guards_without_full_suite_commands() -> None:
    plan = replace(
        inputs(),
        changed=('src/fly_brain/simulation/service.py',),
        format_files=('src/fly_brain/simulation/service.py',),
        python=('src/fly_brain/simulation/service.py', 'src/fly_brain/bootstrap.py'),
        boundaries=True,
        metrics=True,
    )
    tasks = dict(workflow.tasks(plan, 'push'))
    assert tasks['format'][-1] == 'src/fly_brain/simulation/service.py'
    assert tasks['types'] == ('pyright', *plan.python)
    assert 'ownership' in tasks and 'boundaries' in tasks and 'metrics' in tasks
    assert 'tests' not in tasks
    assert tasks['metrics'][-2:] == ('--stage', 'push')


def test_failed_selected_child_stops_delivery_and_preserves_its_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fail(name: str, _command: Sequence[str]) -> int:
        calls.append(name)
        return 7

    monkeypatch.setattr(workflow, 'check', fail)
    assert (
        workflow.execute(
            replace(inputs(), python=('tools/code_quality/check.py',)), 'commit'
        )
        == 7
    )
    assert calls == ['inputs']


@pytest.mark.parametrize(
    'stage,expected',
    (
        ('commit', [(['--staged'], 'staged')]),
        ('push', [(['--base', 'base', '--head', 'head'], 'commits')]),
        ('ci', [(['--base', 'base', '--head', 'head'], 'commits')]),
    ),
)
def test_metric_stage_does_not_measure_both_staged_and_submitted_range(
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    expected: list[tuple[list[str], str]],
) -> None:
    calls: list[tuple[list[str], str]] = []

    def measured(arguments: list[str], name: str) -> int:
        calls.append((arguments, name))
        return 0

    monkeypatch.delenv('PRE_COMMIT', raising=False)

    def references(_environment: Mapping[str, str]) -> tuple[str, str]:
        return 'base', 'head'

    def revision(*arguments: str) -> str:
        return arguments[-1]

    monkeypatch.setattr(gate, 'references', references)
    monkeypatch.setattr(gate, 'git', revision)
    monkeypatch.setattr(gate, 'measure', measured)
    assert gate.main(stage) == 0
    assert calls == expected


def test_changed_native_helpers_must_be_indexed_check_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    helper = tmp_path / 'tools/code_quality/metric_cache.mjs'
    helper.parent.mkdir(parents=True)
    helper.write_text('export const cache = 1;\n')

    def indexed(*_arguments: object, **_keywords: object) -> str:
        return '\0'.join(
            (
                'main.py',
                'pyproject.toml',
                'uv.lock',
                'package.json',
                'pnpm-lock.yaml',
                'justfile',
                '.pre-commit-config.yaml',
                'tools/architecture/ownership.json',
                'tools/code-quality/provenance.json',
                'tools/code-quality/vendor/eng-metrics-code-quality-0.1.0.tgz',
                'tools/code-quality/vendor/eng-metrics-code-quality-0.1.1.tgz',
                'tools/code-quality/python-aggregation.patch',
                'tools/code_quality/metrics.mjs',
                'tools/code_quality/retention.json',
            )
        )

    monkeypatch.setattr(indexed_inputs.subprocess, 'check_output', indexed)
    with pytest.raises(ValueError, match='unindexed.*metric_cache'):
        gate.require_indexed_inputs()


@pytest.mark.parametrize('stage', ('commit', 'push', 'ci'))
@pytest.mark.parametrize('path', ('main.py', 'tests/test_value.py'))
def test_uncommitted_source_cannot_hide_selected_index_or_delivery_debt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: workflow.Stage,
    path: str,
) -> None:
    repository(tmp_path)
    source = tmp_path / path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text('VALUE = 1\n')
    git(tmp_path, 'add', path)
    git(tmp_path, 'commit', '-qm', 'Declare checked input')
    monkeypatch.chdir(tmp_path)
    workflow.verify_checkout(stage, 'HEAD')
    source.write_text('VALUE = 2\n')
    with pytest.raises(ValueError, match='COV002.*execution inputs'):
        workflow.verify_checkout(stage, 'HEAD')


def test_native_bridge_checks_select_only_changed_sources_and_load_type_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    changed = 'tools/architecture/native_changed.mjs'
    untouched = 'tools/architecture/native_unchanged.mjs'
    for name in (changed, untouched):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('export const value = 1;\n')
    tasks = dict(
        workflow.tasks(replace(inputs(), changed=(changed,), native=(changed,)), 'push')
    )
    assert tasks['native-syntax'] == ('node', '--check', changed)
    assert tasks['native-types'][-1] == changed
    assert untouched not in tasks['native-types']


@pytest.mark.parametrize('surviving', (False, True))
def test_removed_native_source_without_a_checked_consumer_fails_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, surviving: bool
) -> None:
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / 'tools/architecture/native_surviving.mjs'
    existing.parent.mkdir(parents=True)
    existing.write_text('export const value = 1;\n')
    changed = ('tools/architecture/native_removed.mjs',) + (
        ('tools/architecture/native_surviving.mjs',) if surviving else ()
    )
    plan = replace(inputs(), changed=changed)
    with pytest.raises(ValueError, match='COV002: removed native source'):
        workflow.tasks(plan, 'push')


@pytest.mark.parametrize(
    'checker',
    (
        'tools/architecture/neutral_import_scope.py',
        'tools/code_quality/boundaries.py',
    ),
)
def test_boundary_implementation_change_invalidates_the_application_scope(
    tmp_path: Path, checker: str
) -> None:
    repository(tmp_path)
    config = tmp_path / 'pyproject.toml'
    config.write_text('[tool.importlinter]\nroot_package="fly_brain"\n')
    git(tmp_path, 'add', 'pyproject.toml')
    git(tmp_path, 'commit', '-qm', 'Declare native boundary context')
    selected = Inputs(tmp_path, frozenset({checker}), frozenset(), None, None, None)
    assert compiler_context(selected).boundaries
