from dataclasses import replace
from pathlib import Path

import pytest

from tests.quality.support import git
from tests.quality.test_changed_checks import CONFIG, VALUES, write
from tests.quality.test_changed_checks import checkout as checkout
from tests.quality.test_incremental_checks import inputs
from tools.code_quality import check as workflow
from tools.code_quality import test_selection
from tools.code_quality.change_inputs import Inputs
from tools.code_quality.changes import build_plan

APP = 'tests/unit/test_value.py'
QUALITY = 'tests/quality/test_checker.py'
CATALOG = frozenset(
    (APP, QUALITY, test_selection.PROOF, 'tests/qualification/test_matrix.py')
)


@pytest.mark.parametrize(
    'stage,count', (('commit', 1), ('ci', 1), ('push', 0), ('manual', 0))
)
def test_automatic_boundaries_dispatch_one_explicit_test_task(
    stage: workflow.Stage, count: int
) -> None:
    plan = replace(inputs(), tests=(APP,), python=(QUALITY,))
    selected = [
        arguments for name, arguments in workflow.tasks(plan, stage) if name == 'tests'
    ]
    assert (
        selected
        == [('python', '-m', 'pytest', '-q', '--ignore=' + test_selection.PROOF, APP)]
        * count
    )


@pytest.mark.parametrize(
    'changed,impacts,expected',
    (
        (
            {'src/fly_brain/value.py'},
            {'src/fly_brain/value.py': {APP, QUALITY}},
            (APP,),
        ),
        (
            {'tools/code_quality/value.py'},
            {'tools/code_quality/value.py': {APP, QUALITY}},
            (QUALITY, APP),
        ),
        ({QUALITY}, {}, (QUALITY,)),
        ({test_selection.PROOF, 'tests/qualification/test_matrix.py'}, {}, ()),
        ({'typings/provider.pyi'}, {}, ()),
    ),
)
def test_test_scope_uses_actual_python_consumers_and_excludes_scientific_inputs(
    tmp_path: Path,
    changed: set[str],
    impacts: dict[str, set[str]],
    expected: tuple[str, ...],
) -> None:
    selected = Inputs(tmp_path, frozenset(changed), CATALOG, None, None, None)
    assert test_selection.select_tests(selected, impacts, 'ci') == expected


@pytest.mark.parametrize(
    'section,expected',
    (('pytest', (APP,)), ('pyright', ()), ('ruff', ()), ('importlinter', ())),
)
def test_only_pytest_configuration_widens_application_test_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    section: str,
    expected: tuple[str, ...],
) -> None:
    before = '[tool.' + section + ']\nvalue=1\n'
    (tmp_path / 'pyproject.toml').write_text(before.replace('value=1', 'value=2'))

    def source(*_arguments: object) -> str:
        return before

    monkeypatch.setattr(test_selection, 'git', source)
    selected = Inputs(
        tmp_path, frozenset({'pyproject.toml'}), CATALOG, None, None, None
    )
    assert test_selection.select_tests(selected, {}, 'commit') == expected


def test_commit_test_scope_includes_pending_delivery_without_widening_static_paths(
    checkout: Path,
) -> None:
    write(checkout, APP, 'from fly_brain.values import VALUE\n')
    write(checkout, QUALITY, 'VALUE = 1\n')
    write(checkout, 'tests/unit/__init__.py', '')
    write(checkout, 'tests/quality/__init__.py', '')
    git(checkout, 'commit', '-qm', 'Declare application test consumers')
    git(checkout, 'remote', 'add', 'origin', '.')
    git(checkout, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
    write(
        checkout,
        'pyproject.toml',
        CONFIG + '[tool.pytest.ini_options]\naddopts=["-m","not checker"]\n',
    )
    git(checkout, 'commit', '-qm', 'Configure pending application selection')
    write(checkout, VALUES, 'VALUE = 2\n')
    plan = build_plan(checkout, 'commit', {})
    assert (plan.changed, plan.tests, QUALITY in plan.python) == (
        (VALUES,),
        (APP,),
        False,
    )
