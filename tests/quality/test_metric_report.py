import json
import subprocess
from pathlib import Path

import pytest

from tools.code_quality import diagnostics


@pytest.mark.parametrize(
    'exit_code,status,passed',
    ((0, 'pass', True), (1, 'regression', False), (2, 'analysis_error', False)),
)
def test_metric_report_preserves_valid_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    exit_code: int,
    status: str,
    passed: bool,
) -> None:
    monkeypatch.chdir(tmp_path)
    report = {'status': status, 'passed': passed}

    def execute(
        *arguments: object, **options: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(['node'], exit_code, json.dumps(report), '')

    monkeypatch.setattr(diagnostics.subprocess, 'run', execute)
    assert diagnostics.measure(['--staged'], 'staged') == exit_code
    assert json.loads((tmp_path / 'logs/quality/staged.json').read_text()) == report


@pytest.mark.parametrize(
    'stdout,exit_code',
    (
        ('not json', 0),
        ('[]', 0),
        ('{"status":"pass","passed":1}', 0),
        ('{"status":"pass","passed":true}', 1),
        ('{"status":"pass","passed":true}', 3),
        ('{"status":"pass","passed":true,"extra":"' + '漢' * 11000 + '"}', 0),
    ),
)
def test_invalid_or_oversized_metric_output_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    exit_code: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    def execute(
        *arguments: object, **options: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(['node'], exit_code, stdout, '')

    monkeypatch.setattr(diagnostics.subprocess, 'run', execute)
    assert diagnostics.measure(['--staged'], 'staged') == 2
    report = json.loads((tmp_path / 'logs/quality/staged.json').read_text())
    assert (report['status'], report['passed']) == ('analysis_error', False)
    assert report['error']['message']
    assert len(report['error']['process_output'].encode('utf-8')) <= 2000
    assert 'analysis_error' in capsys.readouterr().err


def test_metric_report_refuses_a_symlinked_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    evidence = tmp_path / 'evidence.json'
    evidence.write_text('{"keep":true}\n')
    logs = tmp_path / 'logs/quality'
    logs.mkdir(parents=True)
    (logs / 'staged.json').symlink_to(evidence)
    with pytest.raises(ValueError, match='symlink'):
        diagnostics.measure(['--staged'], 'staged')
    assert evidence.read_text() == '{"keep":true}\n'
