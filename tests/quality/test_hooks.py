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

pytestmark = pytest.mark.integration


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
        'lint-imports',
        'pytest',
        'tools.code_quality.gate',
    ],
)
def test_every_failed_child_blocks_commit(tmp_path: Path, tool: str) -> None:
    repo, environment = hook_repository(tmp_path)
    previous = git(repo, 'rev-parse', 'HEAD')
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


def test_unchanged_dependency_debt_blocks_document_commit(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path, BAD)
    result = commit_document(repo, environment)
    assert result.returncode != 0
    assert 'fly_brain.simulation.service' in result.stdout + result.stderr
    assert 'fly_brain.simulation.backend' in result.stdout + result.stderr


def test_unstaged_repair_cannot_hide_staged_dependency(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path)
    source = repo / SERVICE
    source.write_text(BAD)
    git(repo, 'add', SERVICE)
    source.write_text(GOOD)
    result = commit_document(repo, environment)
    assert result.returncode != 0
    assert 'fly_brain.simulation.backend' in result.stdout + result.stderr
    assert source.read_text() == GOOD


def test_actual_push_hook_blocks_existing_dependency_debt(tmp_path: Path) -> None:
    root = tmp_path / 'candidate'
    root.mkdir()
    repo, environment = hook_repository(root, BAD)
    remote = tmp_path / 'remote.git'
    git(tmp_path, 'init', '--bare', str(remote))
    git(repo, 'remote', 'add', 'origin', str(remote))
    result = run(['git', 'push', 'origin', 'main'], repo, environment)
    assert result.returncode != 0
    assert 'fly_brain.simulation.backend' in result.stdout + result.stderr


def test_disabling_full_scan_hides_unchanged_debt(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path, BAD)
    config = repo / '.pre-commit-config.yaml'
    config.write_text(
        config.read_text().replace(
            'always_run: true', 'always_run: false\n        types: [python]'
        )
    )
    git(repo, 'add', '.pre-commit-config.yaml')
    result = commit_document(repo, environment)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Skipped' in result.stdout + result.stderr
