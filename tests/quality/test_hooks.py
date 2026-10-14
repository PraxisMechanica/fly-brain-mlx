from pathlib import Path

import pytest

from tests.quality.hook_fixture import (
    BAD,
    GOOD,
    SERVICE,
    commit_document,
    hook_repository,
)
from tests.quality.support import git, run

pytestmark = [pytest.mark.integration, pytest.mark.checker]


def test_installed_hooks_allow_compliant_commit(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path)
    result = commit_document(repo, environment)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Passed' in result.stdout + result.stderr


@pytest.mark.parametrize(
    'tool',
    [
        'ruff format',
        'ruff check',
        'pyright',
        'tools.code_quality.boundaries',
        'tools.code_quality.gate --inputs-only',
        'tools.code_quality.gate --stage',
    ],
)
def test_every_failed_child_blocks_commit(tmp_path: Path, tool: str) -> None:
    repo, environment = hook_repository(tmp_path)
    previous = git(repo, 'rev-parse', 'HEAD')
    changed = repo / SERVICE
    changed.write_text(GOOD + '# Changed checked input\n')
    git(repo, 'add', SERVICE)
    result = commit_document(repo, {**environment, 'FAIL_TOOL': tool})
    assert result.returncode != 0
    assert 'controlled tool failure: ' + tool in result.stdout + result.stderr
    assert git(repo, 'rev-parse', 'HEAD') == previous


def test_missing_executable_blocks_commit(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path)
    (repo / 'executables/uv').unlink()
    result = commit_document(repo, environment)
    assert result.returncode != 0
    assert 'uv' in result.stdout + result.stderr


def test_document_commit_does_not_repeat_unchanged_source_analysis(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path, BAD)
    result = commit_document(repo, environment)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'fly_brain.qualification.adapters' not in result.stdout + result.stderr


def test_unstaged_repair_cannot_hide_staged_dependency(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path)
    source = repo / SERVICE
    source.write_text(BAD)
    git(repo, 'add', SERVICE)
    source.write_text(GOOD)
    result = commit_document(repo, environment)
    assert result.returncode != 0
    assert 'fly_brain.qualification.adapters' in result.stdout + result.stderr
    assert source.read_text() == GOOD


def test_actual_push_hook_blocks_changed_dependency_debt(tmp_path: Path) -> None:
    root = tmp_path / 'candidate'
    root.mkdir()
    repo, environment = hook_repository(root)
    remote = tmp_path / 'remote.git'
    git(tmp_path, 'clone', '--bare', str(repo), str(remote))
    git(repo, 'remote', 'add', 'origin', str(remote))
    parent = git(repo, 'rev-parse', 'HEAD')
    (repo / SERVICE).write_text(BAD)
    git(repo, 'add', SERVICE)
    tree = git(repo, 'write-tree')
    broken = git(
        repo,
        'commit-tree',
        tree,
        '-p',
        parent,
        '-m',
        'Create deliberately broken push fixture',
    )
    git(repo, 'update-ref', 'HEAD', broken)
    result = run(['git', 'push', 'origin', 'main'], repo, environment)
    assert result.returncode != 0
    assert 'fly_brain.qualification.adapters' in result.stdout + result.stderr


def test_document_only_commit_has_no_checker_regression_replay(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path, BAD)
    result = commit_document(repo, {**environment, 'FAIL_TOOL': 'pytest'})
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'controlled tool failure' not in result.stdout + result.stderr
