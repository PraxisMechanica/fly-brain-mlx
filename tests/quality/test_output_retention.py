import json
from pathlib import Path

import pytest

from tests.quality.support import git, repository
from tools.code_quality.retention import (
    MANAGED_ROOTS,
    OUTPUT_ROOTS,
    POLICY,
    clean_outputs,
    read_retention,
)


def retain(root: Path, *paths: str) -> None:
    policy = root / POLICY
    policy.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text(
        json.dumps(
            {
                'version': 1,
                'exceptions': [
                    {
                        'path': path,
                        'reason': 'Required to finish this explicitly selected active verification.',
                        'release_when': 'Remove after the selected verification completes.',
                    }
                    for path in paths
                ],
            }
        )
    )
    git(root, 'add', POLICY)


def retention_repository(root: Path) -> Path:
    repo = repository(root)
    retain(repo)
    return repo


def managed_markers(root: Path) -> tuple[Path, ...]:
    markers = tuple(root / name / 'marker.txt' for name in OUTPUT_ROOTS)
    for path in markers:
        path.parent.mkdir()
        path.write_text('retain if validation fails')
    return markers


def test_default_policy_clears_disposable_logs_and_keeps_unlisted_evidence(
    tmp_path: Path,
) -> None:
    repo = retention_repository(tmp_path)
    managed_markers(repo)
    clean_outputs(repo)
    assert all(not (repo / name).exists() for name in MANAGED_ROOTS)
    assert (repo / 'executions/marker.txt').read_text() == 'retain if validation fails'
    assert (repo / '.quality-reports/marker.txt').is_file()
    assert (repo / 'calculation.py').is_file() and (repo / POLICY).is_file()


def test_specific_active_run_and_exact_file_bridge_a_commit(tmp_path: Path) -> None:
    repo = retention_repository(tmp_path)
    managed_markers(repo)
    kept = repo / 'executions' / 'active' / 'native.npz'
    kept.parent.mkdir()
    kept.write_bytes(b'complete active evidence')
    sibling = repo / 'executions' / 'other'
    sibling.mkdir()
    (sibling / 'native.npz').write_bytes(b'unretained')
    report = repo / 'logs' / 'needed.json'
    report.write_text('{"useful":true}\n')
    retain(repo, 'executions/active', 'logs/needed.json')
    records = read_retention(repo)
    clean_outputs(repo)
    assert kept.read_bytes() == b'complete active evidence'
    assert report.read_text() == '{"useful":true}\n'
    assert (sibling / 'native.npz').read_bytes() == b'unretained'
    assert (repo / '.quality-reports/marker.txt').is_file()
    assert all(record.reason and record.release_when for record in records)


def test_outside_root_review_record_cannot_broaden_cleanup(tmp_path: Path) -> None:
    repo = retention_repository(tmp_path)
    managed_markers(repo)
    fixture = repo / 'data' / 'retained-fixture.npz'
    fixture.parent.mkdir()
    fixture.write_bytes(b'independent fixture')
    unrelated = repo / 'data' / 'unlisted-input.csv'
    unrelated.write_text('pinned input')
    retain(repo, 'data/retained-fixture.npz')
    clean_outputs(repo)
    assert fixture.read_bytes() == b'independent fixture'
    assert unrelated.read_text() == 'pinned input'
    assert all(not (repo / name).exists() for name in MANAGED_ROOTS)


@pytest.mark.parametrize(
    'manifest',
    (
        'not JSON',
        '[]',
        '{"version":true,"exceptions":[]}',
        '{"version":2,"exceptions":[]}',
        '{"version":1,"exceptions":{},"extra":true}',
        '{"version":1,"exceptions":[] ,"version":1}',
        '{"version":1,"exceptions":[{"path":"executions/active","reason":"","release_when":"finished"}]}',
        '{"version":1,"exceptions":[{"path":"executions/active","reason":"needed","release_when":"  "}]}',
        '{"version":1,"exceptions":[{"path":"executions/active","reason":"needed"}]}',
        '{"version":1,"exceptions":[{"path":"executions/active","path":"logs/other","reason":"needed","release_when":"finished"}]}',
    ),
)
def test_malformed_policy_cannot_partially_delete_outputs(
    tmp_path: Path, manifest: str
) -> None:
    repo = retention_repository(tmp_path)
    markers = managed_markers(repo)
    (repo / POLICY).write_text(manifest)
    with pytest.raises(ValueError):
        clean_outputs(repo)
    assert all(path.read_text() == 'retain if validation fails' for path in markers)


@pytest.mark.parametrize(
    'path',
    (
        '/outside',
        '../outside',
        'executions/../outside',
        '.git/config',
        'executions/.Git/config',
        '.',
        'executions',
        'logs',
        '.quality-reports',
        'executions/*',
        'executions//active',
        'executions\\active',
    ),
)
def test_unsafe_or_blanket_exception_paths_cannot_delete_any_output(
    tmp_path: Path, path: str
) -> None:
    repo = retention_repository(tmp_path)
    markers = managed_markers(repo)
    retain(repo, path)
    with pytest.raises(ValueError):
        clean_outputs(repo)
    assert all(marker.is_file() for marker in markers)


@pytest.mark.parametrize(
    'paths',
    (
        ('executions/active', 'executions/active'),
        ('executions/active', 'executions/active/native.npz'),
        ('data/fixture.npz', 'data/fixture.npz'),
    ),
)
def test_duplicate_or_overlapping_exceptions_fail_before_deletion(
    tmp_path: Path, paths: tuple[str, ...]
) -> None:
    repo = retention_repository(tmp_path)
    markers = managed_markers(repo)
    retain(repo, *paths)
    with pytest.raises(ValueError, match='overlapping'):
        clean_outputs(repo)
    assert all(marker.is_file() for marker in markers)


def test_policy_symlink_is_refused_before_other_roots_are_cleaned(
    tmp_path: Path,
) -> None:
    repo = retention_repository(tmp_path)
    markers = managed_markers(repo)
    target = repo / 'source-policy.json'
    target.write_text((repo / POLICY).read_text())
    (repo / POLICY).unlink()
    (repo / POLICY).symlink_to(target)
    with pytest.raises(ValueError, match='symlinked'):
        clean_outputs(repo)
    assert all(marker.is_file() for marker in markers)
    assert target.is_file()


def test_symlink_in_retained_path_is_not_followed(tmp_path: Path) -> None:
    repo = retention_repository(tmp_path)
    markers = managed_markers(repo)
    target = repo / 'outside'
    target.mkdir()
    native = target / 'native.npz'
    native.write_bytes(b'keep outside target')
    (repo / 'executions/active').symlink_to(target, target_is_directory=True)
    retain(repo, 'executions/active/native.npz')
    with pytest.raises(ValueError, match='symlinked'):
        clean_outputs(repo)
    assert all(marker.is_file() for marker in markers)
    assert native.read_bytes() == b'keep outside target'


@pytest.mark.parametrize('root_name', ('executions', '.quality-reports'))
def test_later_invalid_root_blocks_deletion_of_earlier_logs(
    tmp_path: Path, root_name: str
) -> None:
    repo = retention_repository(tmp_path)
    logs = repo / 'logs'
    logs.mkdir()
    marker = logs / 'marker.txt'
    marker.write_text('keep until all checks validate')
    target = repo / 'outside'
    target.mkdir()
    (repo / root_name).symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match='symlinked'):
        clean_outputs(repo)
    assert marker.read_text() == 'keep until all checks validate'


def test_unindexed_policy_blocks_cleanup(tmp_path: Path) -> None:
    repo = retention_repository(tmp_path)
    markers = managed_markers(repo)
    git(repo, 'rm', '--cached', POLICY)
    with pytest.raises(ValueError, match='indexed'):
        clean_outputs(repo)
    assert all(marker.is_file() for marker in markers)


def test_versioned_execution_blocks_deletion_of_untracked_logs(tmp_path: Path) -> None:
    repo = retention_repository(tmp_path)
    markers = managed_markers(repo)
    git(repo, 'add', 'executions/marker.txt')
    with pytest.raises(ValueError, match='versioned'):
        clean_outputs(repo)
    assert all(marker.is_file() for marker in markers)
