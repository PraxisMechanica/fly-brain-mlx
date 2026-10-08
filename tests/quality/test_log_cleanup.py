from pathlib import Path

import pytest

from tests.quality.hook_fixture import commit_document, hook_repository
from tests.quality.support import git, repository
from tools.code_quality.cleanup import clean_logs


def test_cleanup_removes_only_disposable_logs(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    logs = repo / 'logs' / 'quality'
    logs.mkdir(parents=True)
    (logs / 'failure.json').write_text('{"failed": true}\n')
    execution = repo / 'executions' / 'case.npz'
    execution.parent.mkdir()
    execution.write_bytes(b'required native evidence')
    clean_logs(repo)
    assert not (repo / 'logs').exists()
    assert execution.read_bytes() == b'required native evidence'


def test_missing_logs_are_a_valid_clean_state(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    clean_logs(repo)
    assert (repo / 'calculation.py').is_file()


def test_cleanup_refuses_a_symlinked_root(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    evidence = tmp_path / 'required-evidence'
    evidence.mkdir()
    original = evidence / 'trace.npz'
    original.write_bytes(b'keep')
    (repo / 'logs').symlink_to(evidence, target_is_directory=True)
    with pytest.raises(ValueError, match='symlinked'):
        clean_logs(repo)
    assert original.read_bytes() == b'keep'


def test_nested_symlink_does_not_remove_its_target(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    logs = repo / 'logs'
    logs.mkdir()
    evidence = repo / 'executions'
    evidence.mkdir()
    original = evidence / 'trace.npz'
    original.write_bytes(b'keep')
    (logs / 'trace').symlink_to(evidence, target_is_directory=True)
    clean_logs(repo)
    assert original.read_bytes() == b'keep'


def test_versioned_files_block_cleanup(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    logs = repo / 'logs'
    logs.mkdir()
    original = logs / 'fixture.json'
    original.write_text('{"required": true}\n')
    git(repo, 'add', str(original.relative_to(repo)))
    with pytest.raises(ValueError, match='versioned'):
        clean_logs(repo)
    assert original.read_text() == '{"required": true}\n'


def test_file_in_place_of_logs_blocks_cleanup(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    (repo / 'logs').write_text('keep\n')
    with pytest.raises(ValueError, match='directory'):
        clean_logs(repo)
    assert (repo / 'logs').read_text() == 'keep\n'


@pytest.mark.integration
@pytest.mark.parametrize(
    'tool',
    (
        '',
        'ruff format',
        'ruff check',
        'pyright',
        'lint-imports',
        'pytest',
        'tools.code_quality.gate',
    ),
)
def test_hook_cleanup_requires_all_checks_to_pass(tmp_path: Path, tool: str) -> None:
    repo, environment = hook_repository(tmp_path)
    logs = repo / 'logs'
    logs.mkdir()
    diagnostic = logs / 'check.txt'
    diagnostic.write_text('needed for diagnosis\n')
    execution = repo / 'executions' / 'trace.npz'
    execution.parent.mkdir()
    execution.write_bytes(b'scientific evidence')
    previous = git(repo, 'rev-parse', 'HEAD')
    result = commit_document(repo, {**environment, 'FAIL_TOOL': tool})
    if tool:
        assert result.returncode != 0
        assert git(repo, 'rev-parse', 'HEAD') == previous
        assert diagnostic.read_text() == 'needed for diagnosis\n'
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert not logs.exists()
    assert execution.read_bytes() == b'scientific evidence'


@pytest.mark.integration
def test_hook_refuses_to_clean_a_symlinked_logs_root(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path)
    target = repo / 'executions'
    target.mkdir()
    original = target / 'trace.npz'
    original.write_bytes(b'preserve')
    (repo / 'logs').symlink_to(target, target_is_directory=True)
    previous = git(repo, 'rev-parse', 'HEAD')
    result = commit_document(repo, environment)
    assert result.returncode != 0
    assert 'symlinked logs' in result.stdout + result.stderr
    assert git(repo, 'rev-parse', 'HEAD') == previous
    assert original.read_bytes() == b'preserve'


@pytest.mark.integration
def test_disabling_fail_fast_erases_failed_diagnostics(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path)
    logs = repo / 'logs'
    logs.mkdir()
    (logs / 'failure.txt').write_text('needed for diagnosis\n')
    config = repo / '.pre-commit-config.yaml'
    config.write_text(config.read_text().replace('fail_fast: true', 'fail_fast: false'))
    git(repo, 'add', '.pre-commit-config.yaml')
    result = commit_document(repo, {**environment, 'FAIL_TOOL': 'pyright'})
    assert result.returncode != 0
    assert not logs.exists()
