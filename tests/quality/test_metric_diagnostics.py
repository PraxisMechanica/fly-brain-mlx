import json
from pathlib import Path
from typing import cast

import pytest

from tests.quality.python_metric_fixture import protocol_tool
from tests.quality.support import COMPLEX, PROJECT, SIMPLE, git, repository, run
from tools.architecture.compiler import JsonValue, object_value

pytestmark = pytest.mark.integration
ADAPTER = PROJECT / 'tools/code_quality/metrics.mjs'


def compact(
    root: Path,
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> tuple[int, dict[str, JsonValue]]:
    result = run(['node', str(ADAPTER), *arguments], root, environment)
    assert result.stderr == '', result.stderr
    assert len(result.stdout.splitlines()) == 1
    return result.returncode, object_value(cast(JsonValue, json.loads(result.stdout)))


def test_passing_staged_change_has_only_compact_summary(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    (repo / 'calculation.py').write_text(SIMPLE.replace('+ 1', '+ 2'))
    git(repo, 'add', '.')
    status, report = compact(repo, '--staged')
    assert (status, report['status'], report['passed']) == (0, 'pass', True)
    assert (report['commits'], report['comparisons']) == (0, 1)
    assert report['before'] == report['after']
    assert report['findings'] == {
        'total': 0,
        'by_rule': {},
        'examples': [],
        'omitted': 0,
    }
    assert 'files' not in report and 'unsupported_paths' not in json.dumps(report)


def test_staged_regression_cannot_be_hidden_by_unstaged_repair(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    source = repo / 'calculation.py'
    source.write_text(COMPLEX)
    git(repo, 'add', '.')
    source.write_text(SIMPLE)
    status, report = compact(repo, '--staged')
    findings = object_value(report['findings'])
    examples = findings['examples']
    assert isinstance(examples, list)
    assert (status, report['status'], report['passed']) == (1, 'regression', False)
    assert findings['by_rule'] == {'CQ001': 1, 'CQ002': 3, 'CQ003': 1}
    assert findings['total'] == len(examples) == 5 and findings['omitted'] == 0
    assert any(
        object_value(example)['path'] == 'calculation.py' for example in examples
    )
    assert source.read_text() == SIMPLE


def test_commit_range_keeps_bad_commit_after_later_repair(tmp_path: Path) -> None:
    repo = repository(tmp_path)
    base = git(repo, 'rev-parse', 'HEAD')
    source = repo / 'calculation.py'
    source.write_text(COMPLEX)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Introduce fixture metric regression')
    bad = git(repo, 'rev-parse', 'HEAD')
    source.write_text(SIMPLE)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Repair fixture metric regression')
    status, report = compact(repo, '--base', base, '--head', 'HEAD')
    examples = object_value(report['findings'])['examples']
    assert isinstance(examples, list)
    assert (status, report['status'], report['passed']) == (1, 'regression', False)
    assert (report['commits'], report['comparisons']) == (2, 2)
    assert report['before'] == report['after']
    assert all(object_value(example)['commit'] == bad for example in examples)
    assert object_value(report['findings'])['total'] == 5


def test_large_regression_keeps_exact_counts_and_only_twenty_examples(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    paths = [repo / 'calculation.py', *(repo / f'probe_{i:03d}.py' for i in range(39))]
    for path in paths:
        path.write_text(SIMPLE)
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'Declare many source fixtures')
    for path in paths:
        path.write_text(COMPLEX)
    git(repo, 'add', '.')
    status, report = compact(repo, '--staged')
    findings = object_value(report['findings'])
    examples = findings['examples']
    assert isinstance(examples, list)
    assert (status, report['passed']) == (1, False)
    assert (findings['total'], len(examples), findings['omitted']) == (44, 20, 24)
    assert findings['by_rule'] == {'CQ001': 1, 'CQ002': 42, 'CQ003': 1}
    assert len(json.dumps(report)) < 4000
    assert all(
        set(object_value(example)) == {'path', 'rule', 'metric', 'before', 'after'}
        for example in examples
    )


def test_long_native_error_keeps_reason_and_explicit_omitted_count(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path)
    status, report = compact(
        repo, '--staged', environment=protocol_tool(repo, 'invalid-' + 'x' * 5000)
    )
    error = object_value(report['error'])
    message = error['message']
    assert isinstance(message, str)
    assert (status, report['status'], report['passed']) == (2, 'analysis_error', False)
    assert len(message) <= 2000 and cast(int, error['omitted_chars']) > 3000
    assert f'[{error["omitted_chars"]} characters omitted]' in message
    assert 'calculation.py' in message and 'Radon' in message


@pytest.mark.parametrize(
    'arguments',
    (
        (),
        ('--head', 'HEAD'),
        ('--base', 'HEAD'),
        ('--base', '', '--head', 'HEAD'),
        ('--staged', '--base', 'HEAD', '--head', 'HEAD'),
        ('--staged', '--staged'),
        ('--staged', '--json', 'report.json'),
        ('--staged', 'unexpected'),
    ),
)
def test_argument_errors_fail_closed_without_writing_reports(
    tmp_path: Path, arguments: tuple[str, ...]
) -> None:
    repo = repository(tmp_path)
    status, report = compact(repo, *arguments)
    assert (status, report['status'], report['passed']) == (2, 'analysis_error', False)
    assert object_value(report['error'])['message']
    assert not (repo / 'report.json').exists()


@pytest.mark.parametrize('problem', ('syntax', 'history'))
def test_analysis_errors_keep_source_or_history_reason(
    tmp_path: Path, problem: str
) -> None:
    repo = repository(tmp_path)
    if problem == 'syntax':
        (repo / 'calculation.py').write_text('def broken(:\n')
        git(repo, 'add', '.')
        arguments = ('--staged',)
        expected = 'calculation.py'
    else:
        arguments = ('--base', 'missing-reference', '--head', 'HEAD')
        expected = 'missing-reference'
    status, report = compact(repo, *arguments)
    assert (status, report['status'], report['passed']) == (2, 'analysis_error', False)
    assert expected in cast(str, object_value(report['error'])['message'])
