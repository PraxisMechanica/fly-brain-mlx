import sys
from pathlib import Path

import pytest

from tools.code_quality.run import bounded, check


def test_failed_check_keeps_its_exit_status_and_bounds_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    status = check(
        'types',
        (
            sys.executable,
            '-c',
            'import sys; print("x"*100000); print("actionable failure"); sys.exit(7)',
        ),
    )
    display = capsys.readouterr().err
    saved = (tmp_path / 'logs/quality/types.log').read_text()
    assert status == 7
    assert len(display) < 4300 and len(saved) <= 65536
    assert 'bytes omitted' in display and 'bytes omitted' in saved
    assert 'actionable failure' in display and 'actionable failure' in saved


def test_success_has_no_raw_log_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    assert check('tests', (sys.executable, '-c', 'print("419 passed")')) == 0
    assert '419 passed' in capsys.readouterr().out
    assert not (tmp_path / 'logs').exists()


def test_missing_tool_is_a_failure_with_a_useful_diagnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert check('types', ('missing-project-check-tool',)) == 2
    assert (
        'missing-project-check-tool'
        in (tmp_path / 'logs/quality/types.log').read_text()
    )


def test_short_output_is_preserved() -> None:
    assert bounded('source.py: error', 1024) == 'source.py: error'


def test_unicode_output_obeys_the_byte_limit_without_breaking_characters() -> None:
    text = '漢🙂' * 10000 + '\nactionable failure'
    result = bounded(text, 4096)
    assert len(result.encode('utf-8')) <= 4096
    assert '\ufffd' not in result
    assert 'bytes omitted' in result and result.endswith('actionable failure')
