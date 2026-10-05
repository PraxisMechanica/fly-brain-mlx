import shutil
from pathlib import Path

import pytest

from tests.quality.support import COMPLEX, SIMPLE, git, measure, repository

pytestmark = pytest.mark.integration


def test_regression_rejects_all_three_metrics(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    (repo / 'calculation.py').write_text(COMPLEX)
    git(repo, 'add', '.')
    result = measure(repo, '--staged')
    assert result.returncode == 1, result.stderr
    assert all(rule in result.stderr for rule in ('CQ001', 'CQ002', 'CQ003'))
    assert 'calculation.py' in result.stderr


def test_repaired_and_close_compliant_source_pass(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    (repo / 'calculation.py').write_text(SIMPLE.replace('+ 1', '+ 2'))
    git(repo, 'add', '.')
    assert measure(repo, '--staged').returncode == 0


def test_unstaged_repair_cannot_hide_staged_regression(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    source = repo / 'calculation.py'
    source.write_text(COMPLEX)
    git(repo, 'add', '.')
    source.write_text(SIMPLE)
    assert measure(repo, '--staged').returncode == 1
    assert source.read_text() == SIMPLE


def test_later_commit_cannot_hide_earlier_regression(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    baseline = git(repo, 'rev-parse', 'HEAD')
    source = repo / 'calculation.py'
    source.write_text(COMPLEX)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Introduce fixture metric regression')
    source.write_text(SIMPLE)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Repair fixture metric regression')
    result = measure(repo, '--base', baseline, '--head', 'HEAD')
    assert result.returncode == 1, result.stderr
    assert 'CQ002' in result.stderr


@pytest.mark.parametrize('problem', ['syntax', 'empty', 'history', 'tool'])
def test_incomplete_analysis_fails(tmp_path: Path, problem: str) -> None:
    repo = repository(tmp_path)
    source = repo / 'calculation.py'
    environment: dict[str, str] = {}
    arguments = ['--staged']
    if problem == 'syntax':
        source.write_text('def broken(:\n')
    elif problem == 'empty':
        source.unlink()
    elif problem == 'history':
        arguments = ['--base', 'missing-reference', '--head', 'HEAD']
    else:
        tools = repo / 'executables'
        tools.mkdir()
        for name in ('node', 'git'):
            executable = shutil.which(name)
            assert executable is not None
            (tools / name).symlink_to(executable)
        environment['PATH'] = str(tools)
    git(repo, 'add', '.')
    result = measure(repo, *arguments, environment=environment)
    assert result.returncode == 2, result.stderr
    assert 'Analysis failed:' in result.stderr
