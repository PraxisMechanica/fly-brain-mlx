import json
import signal
import subprocess
from pathlib import Path
from typing import TextIO

import numpy as np
import pytest

from fly_brain.qualification.adapters import pytest_runner
from fly_brain.qualification.adapters.batch_stimulus import load
from fly_brain.qualification.models import QualificationRequest
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.models import Connectome, InputPin
from tests.support.seeded_inputs import generate
from tests.unit.test_stimuli import connectome

pytestmark = pytest.mark.integration


@pytest.mark.parametrize('timed_out', (False, True))
def test_local_qualification_prepares_the_required_pinned_proof_and_consumer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, timed_out: bool
) -> None:
    network = connectome()
    pin = InputPin('csv', 'parquet', len(network.neuron_ids), 0)
    request = QualificationRequest(tmp_path, tmp_path / 'fresh')

    def inputs(project: Path, reader_factory: object) -> tuple[Connectome, InputPin]:
        assert project == request.project and callable(reader_factory)
        return network, pin

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
        assert env['FLY_BRAIN_PINNED_PROJECT'] == str(request.project)
        assert env['MLX_ENABLE_TF32'] == '0'
        assert command[4:6] == (
            'tests/qualification',
            'tests/integration/test_session_proof_artifacts.py',
        )
        assert f'--basetemp={request.output / "temporary"}' in command
        actual = load(request.output / 'frozen-stimulus', EXPERIMENTS['sugar'], pin)
        expected = generate(network, EXPERIMENTS['sugar'], 1000, actual.trial_indices)
        assert actual.trial_indices == (0, 1, 2, 3)
        assert np.array_equal(actual.events, expected.events)
        assert actual.sha256 == expected.sha256
        metadata = json.loads(
            (request.output / 'frozen-stimulus/stimulus.json').read_text()
        )
        assert metadata['seed_tuples'] == [[20261004, 0, trial] for trial in range(4)]
        assert stderr == subprocess.STDOUT and start_new_session is True
        stdout.write('scientific checks executed\n')
        (request.output / 'tests.xml').write_text(
            '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0" />'
            '</testsuites>'
        )
        return Process()

    monkeypatch.setattr(pytest_runner, 'load_pinned_inputs', inputs)
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
