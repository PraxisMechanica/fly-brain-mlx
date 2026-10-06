from pathlib import Path

import pytest

from tests.quality.hook_fixture import commit_document, hook_repository
from tests.quality.support import git
from tests.quality.test_active_session_boundary import (
    CONTRACT,
    NEUTRAL,
    SCOPES,
    TARGETS,
)

pytestmark = pytest.mark.integration


@pytest.mark.parametrize('scope', SCOPES)
@pytest.mark.parametrize('target', TARGETS)
def test_actual_canonical_active_scope_rejects_repairs_and_loses_detection_when_removed(
    tmp_path: Path, scope: str, target: str
) -> None:
    repo, environment = hook_repository(tmp_path)
    policy = repo / 'pyproject.toml'
    original = policy.read_text()
    selected = next(
        item
        for item in original.split('[[tool.importlinter.contracts]]')
        if f'name = "{CONTRACT}"' in item
    )
    assert all(f'"{item}"' in selected for item in (*SCOPES, *TARGETS))
    path = repo / Path('src', *scope.split('.')).with_suffix('.py')
    path.write_text(f'from {target} import VALUE\n')
    git(repo, 'add', 'src')
    rejected = commit_document(repo, environment)
    output = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert (
        CONTRACT in output and scope in output and target in output and '(l.' in output
    )
    path.write_text(NEUTRAL)
    git(repo, 'add', 'src')
    repaired = commit_document(repo, environment)
    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    path.write_text(f'from {target} import VALUE\n')
    git(repo, 'add', 'src')
    assert commit_document(repo, environment).returncode != 0
    weakened = selected.replace(f'    "{scope}",\n', '')
    assert weakened != selected
    policy.write_text(original.replace(selected, weakened, 1))
    git(repo, 'add', 'pyproject.toml')
    hidden = commit_document(repo, environment)
    assert hidden.returncode == 0, hidden.stdout + hidden.stderr


def test_actual_canonical_active_transitivity_rejects_indirect_path_and_weakening(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path)
    policy = repo / 'pyproject.toml'
    original = policy.read_text()
    selected = next(
        item
        for item in original.split('[[tool.importlinter.contracts]]')
        if f'name = "{CONTRACT}"' in item
    )
    scope, target = SCOPES[0], TARGETS[1]
    helper = 'fly_brain.qualification.active_contract_helper'
    (repo / Path('src', *helper.split('.')).with_suffix('.py')).write_text(
        f'from {target} import VALUE\n'
    )
    path = repo / Path('src', *scope.split('.')).with_suffix('.py')
    path.write_text(f'from {helper} import VALUE\n')
    git(repo, 'add', 'src')
    rejected = commit_document(repo, environment)
    output = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert all(name in output for name in (CONTRACT, scope, helper, target))
    path.write_text(NEUTRAL)
    git(repo, 'add', 'src')
    repaired = commit_document(repo, environment)
    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    path.write_text(f'from {helper} import VALUE\n')
    weakened = selected.replace(
        'allow_indirect_imports = false', 'allow_indirect_imports = true'
    )
    assert weakened != selected
    policy.write_text(original.replace(selected, weakened, 1))
    git(repo, 'add', 'src', 'pyproject.toml')
    hidden = commit_document(repo, environment)
    assert hidden.returncode == 0, hidden.stdout + hidden.stderr
