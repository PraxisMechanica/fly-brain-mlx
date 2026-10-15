import signal
import subprocess
from pathlib import Path
from typing import TextIO

import pytest

from fly_brain.qualification.adapters import pytest_runner
from fly_brain.qualification.models import QualificationRequest

pytestmark = pytest.mark.integration


@pytest.mark.parametrize('timed_out', (False, True))
def test_local_qualification_excludes_historical_full_model_preservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, timed_out: bool
) -> None:
    request = QualificationRequest(tmp_path, tmp_path / 'fresh')

    killed: list[tuple[int, int]] = []

    class Process:
        pid = 123

        def wait(self, *, timeout: float | None = None) -> int:
            if timeout is not None:
                assert 0 < timeout <= 300
                if timed_out:
                    raise subprocess.TimeoutExpired('pytest', timeout)
            return -9 if killed else 0

    def execute(
        command: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str],
        stdout: TextIO,
        stderr: int,
        start_new_session: bool,
    ) -> Process:
        assert cwd == request.project
        assert env['MLX_ENABLE_TF32'] == '0'
        assert command[4:6] == (
            'tests/qualification',
            '--ignore=tests/qualification/test_observation_session_pinned.py',
        )
        assert [value for value in command if value.startswith('--ignore=')] == [
            '--ignore=tests/qualification/test_observation_session_pinned.py'
        ]
        assert 'tests/integration/test_session_proof_artifacts.py' not in command
        assert f'--basetemp={request.output / "temporary"}' in command
        assert not (request.output / 'frozen-stimulus').exists()
        assert stderr == subprocess.STDOUT and start_new_session is True
        stdout.write('scientific checks executed\n')
        (request.output / 'tests.xml').write_text(
            '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0" />'
            '</testsuites>'
        )
        return Process()

    monkeypatch.setattr(pytest_runner.subprocess, 'Popen', execute)

    def terminate(pid: int, signum: int) -> None:
        killed.append((pid, signum))

    monkeypatch.setattr(pytest_runner.os, 'killpg', terminate)
    result = pytest_runner.run_tests(request)
    assert result.accepted is (not timed_out)
    log = (request.output / 'qualification.log').read_text()
    assert log.startswith('scientific checks executed\n')
    if timed_out:
        assert result.exit_code == 124 and result.counts is None
        assert killed == [(123, signal.SIGKILL)]
        assert 'five-minute limit' in log
    else:
        assert killed == []
