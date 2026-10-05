import os
import struct
import sys
import zlib
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import (
    BrianJob,
    Frame,
    build,
    results,
    run,
)
from fly_brain.qualification.adapters.observer_stream import (
    MAGIC,
    FinalSnapshot,
    PhaseBlock,
    StepSnapshot,
    StreamShape,
)
from fly_brain.simulation.models import Connectome

pytestmark = [pytest.mark.integration, pytest.mark.reference]


@dataclass(frozen=True)
class Runs:
    jobs: dict[str, BrianJob]
    frames: dict[str, tuple[Frame, ...]]
    root: Path


@pytest.fixture(scope='module')
def runs(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Runs:
    destination = cast(str | None, request.config.getoption('--artifact-output'))
    output = (
        Path(destination) / 'brian-jobs'
        if destination
        else tmp_path_factory.mktemp('brian-jobs')
    )
    output.mkdir(parents=True, exist_ok=True)
    sources = np.array([0, 0, 0, 1, 2, 3, 4, 4], dtype=np.int32)
    destinations = np.array([1, 1, 0, 2, 3, 0, 5, 5], dtype=np.int32)
    counts = np.array([360, 0, 1, -2, 3, 360, -1, -1], dtype=np.int32)
    connectome = Connectome(
        np.arange(6, dtype=np.int64), sources, destinations, counts, counts * 0.275
    )
    events = np.zeros((101, 3), dtype=np.uint8)
    events[::3, 0] = events[::7, 1] = events[::4, 2] = 1
    jobs = {
        name: build(connectome, (0, 0, 1), (3,), events, output / name, size)
        for name, size in (('ordinary', None), ('observed', 32))
    }
    assert all(
        not tuple((job.directory / 'results').iterdir()) for job in jobs.values()
    )
    jobs['repeat'] = jobs['observed']
    frames = {
        name: tuple(run(job, output / (name + '-results')))
        for name, job in jobs.items()
    }
    return Runs(jobs, frames, output)


def test_live_pipe_preserves_ordinary_final_state_and_spikes(runs: Runs) -> None:
    stock = results(runs.jobs['ordinary'], runs.root / 'ordinary-results')
    observed = results(runs.jobs['observed'], runs.root / 'observed-results')
    assert runs.frames['ordinary'] == ()
    for name, value in stock.items():
        assert value.tobytes() == observed[name].tobytes(), name
    final = runs.frames['observed'][-1]
    assert isinstance(final, FinalSnapshot) and final.step.clock_step == 101
    for name, value in final.fields.items():
        assert value.tobytes() == observed[name].tobytes(), name
    blocks = [
        frame for frame in runs.frames['observed'] if isinstance(frame, PhaseBlock)
    ]
    assert [(block.begin, block.rows) for block in blocks] == [
        (0, 32),
        (32, 32),
        (64, 32),
        (96, 5),
    ]
    assert not (runs.root / 'observed-results/stdout.txt').exists()


def test_reused_binary_starts_each_repeat_from_fresh_state(runs: Runs) -> None:
    first = results(runs.jobs['observed'], runs.root / 'observed-results')
    repeat = results(runs.jobs['repeat'], runs.root / 'repeat-results')
    for name, value in first.items():
        assert value.tobytes() == repeat[name].tobytes(), name
    blocks = [
        frame for frame in runs.frames['observed'] if isinstance(frame, PhaseBlock)
    ]
    repeated = [
        frame for frame in runs.frames['repeat'] if isinstance(frame, PhaseBlock)
    ]
    for left, right in zip(blocks, repeated, strict=True):
        for name, value in left.fields.items():
            assert value.tobytes() == right.fields[name].tobytes(), name


def program(directory: Path, body: str, observed: bool) -> BrianJob:
    directory.mkdir()
    binary = directory / 'main'
    binary.write_text('#!' + sys.executable + '\n' + body)
    binary.chmod(0o700)
    return BrianJob(directory, StreamShape(2, 2, 0, (), 2), observed, {})


def slow_program(directory: Path, payload: bytes) -> BrianJob:
    return program(
        directory,
        'import os, sys, time\n'
        'from pathlib import Path\n'
        f'Path({str(directory / "pid")!r}).write_text(str(os.getpid()))\n'
        f'sys.stdout.buffer.write({payload!r})\n'
        'sys.stdout.buffer.flush()\n'
        'time.sleep(30)\n',
        True,
    )


def assert_process_exited(job: BrianJob) -> None:
    pid = int((job.directory / 'pid').read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_nonzero_process_exit_keeps_its_error_log(tmp_path: Path) -> None:
    job = program(
        tmp_path / 'failure',
        'import sys\nsys.stderr.write("reference failed\\n")\nsys.exit(7)\n',
        False,
    )
    with pytest.raises(RuntimeError, match='exited 7'):
        tuple(run(job, tmp_path / 'results'))
    assert (tmp_path / 'results/stderr.log').read_text() == 'reference failed\n'


def test_transport_failure_stops_only_its_owned_process(tmp_path: Path) -> None:
    job = slow_program(tmp_path / 'corrupt', b'garbled!')
    with pytest.raises(ValueError, match='signature'):
        tuple(run(job, tmp_path / 'results'))
    assert_process_exited(job)


def test_closing_a_partial_stream_stops_its_owned_process(tmp_path: Path) -> None:
    header = MAGIC + struct.pack('<QQQQQ', 2, 2, 0, 0, 2)
    step = struct.pack('<QQQdiQQ', 1, 0, 0, 0.0, -1, 0, 0)
    payload = b''.join(
        part + struct.pack('<I', zlib.crc32(part)) for part in (header, step)
    )
    job = slow_program(tmp_path / 'unfinished', payload)
    with closing(run(job, tmp_path / 'results')) as frames:
        first = next(frames)
        assert isinstance(first, StepSnapshot) and first.step == 0
    assert_process_exited(job)
