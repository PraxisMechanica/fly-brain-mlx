import os
import re
import struct
import sys
import zlib
from collections.abc import Mapping
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
from fly_brain.qualification.adapters.observer_tape import replay
from fly_brain.qualification.adapters.paired_observer import phase_hash
from fly_brain.qualification.adapters.reference_queues import ReferenceQueues
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
        name: build(
            connectome,
            (0, 0, 1),
            (3,),
            events,
            output / name,
            size,
            bind_build=name == 'observed',
        )
        for name, size in (('ordinary', None), ('observed', 32))
    }
    assert all(
        not tuple((job.directory / 'results').iterdir()) for job in jobs.values()
    )
    jobs['repeat'] = jobs['observed']
    frames = {
        name: tuple(
            run(
                job,
                output / (name + '-results'),
                tape=output / (name + '.gz') if job.observed else None,
            )
        )
        for name, job in jobs.items()
    }
    return Runs(jobs, frames, output)


def test_bound_build_covers_effective_preferences_and_consumed_system_headers(
    runs: Runs,
) -> None:
    context = runs.jobs['observed'].build_context
    assert context is not None
    assert 'refractory_timing = False' in str(context['preferences'])
    assert 'zlib.h' in str(context['dependencies'])
    assert set(cast(Mapping[str, object], context['packages'])) == {
        'brian2',
        'cython',
        'numpy',
        'sympy',
        'mpmath',
        'pyparsing',
        'jinja2',
        'markupsafe',
        'setuptools',
        'packaging',
    }


def test_recorded_live_execution_replays_every_native_phase(runs: Runs) -> None:
    for name in ('observed', 'repeat'):
        recorded = tuple(replay(runs.root / (name + '.gz'), runs.jobs[name].shape))
        assert len(recorded) == len(runs.frames[name])
        for actual, expected in zip(recorded, runs.frames[name], strict=True):
            assert type(actual) is type(expected)
            if isinstance(actual, PhaseBlock) and isinstance(expected, PhaseBlock):
                assert (actual.begin, actual.rows, phase_hash(actual.fields)) == (
                    expected.begin,
                    expected.rows,
                    phase_hash(expected.fields),
                )
            if isinstance(actual, FinalSnapshot) and isinstance(
                expected, FinalSnapshot
            ):
                assert phase_hash(actual.fields) == phase_hash(expected.fields)
    assert (runs.root / 'observed.gz').read_bytes() == (
        runs.root / 'repeat.gz'
    ).read_bytes()


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


def test_every_physical_queue_and_cursor_repeats_through_the_live_pipe(
    runs: Runs,
) -> None:
    for left, right in zip(runs.frames['observed'], runs.frames['repeat'], strict=True):
        assert type(left) is type(right)
        if isinstance(left, FinalSnapshot) and isinstance(right, FinalSnapshot):
            left, right = left.step, right.step
        if not isinstance(left, StepSnapshot) or not isinstance(right, StepSnapshot):
            continue
        assert struct.pack(
            '<QQdi', left.step, left.clock_step, left.time_s, left.source_cursor
        ) == struct.pack(
            '<QQdi', right.step, right.clock_step, right.time_s, right.source_cursor
        )
        assert left.spikes.tobytes() == right.spikes.tobytes()
        assert left.source_spikes.tobytes() == right.source_spikes.tobytes()
        for first, second in zip(left.pathways, right.pathways, strict=True):
            assert first.delivered.tobytes() == second.delivered.tobytes()
            for a, b in zip(first.queues, second.queues, strict=True):
                assert a.offset == b.offset
                assert tuple(slot.tobytes() for slot in a.slots) == tuple(
                    slot.tobytes() for slot in b.slots
                )


def test_reference_weights_keep_original_unit_scaling_and_silenced_rows(
    runs: Runs,
) -> None:
    expected = np.array([360, 0, 1, -2, 3, 0, -1, -1], dtype=np.int32) * (0.275 * 0.001)
    for name in ('ordinary', 'observed', 'repeat'):
        job = runs.jobs[name]
        actual = np.fromfile(
            runs.root / (name + '-results') / job.files['weights'], dtype=np.float64
        )
        assert actual.tobytes() == expected.tobytes()


def test_live_queues_follow_original_rows_and_canonical_input_bits(runs: Runs) -> None:
    sources = np.array([0, 0, 0, 1, 2, 3, 4, 4], dtype=np.int32)
    events = np.zeros((101, 3), dtype=np.uint8)
    events[::3, 0] = events[::7, 1] = events[::4, 2] = 1
    for name in ('observed', 'repeat'):
        ledger = ReferenceQueues(sources, 6, events)
        for frame in runs.frames[name]:
            if isinstance(frame, (StepSnapshot, FinalSnapshot)):
                ledger.check(frame)
                assert len(ledger.pending) <= 19
        assert ledger.step == 101


def test_phase_capture_preserves_ordinary_numerical_source_and_inputs(
    runs: Runs,
) -> None:
    stock, observed = (runs.jobs[name].directory for name in ('ordinary', 'observed'))
    for folder in ('code_objects', 'static_arrays'):
        for file in (stock / folder).iterdir():
            if folder == 'static_arrays' or file.suffix in ('.cpp', '.h'):
                assert file.read_bytes() == (
                    observed / folder / file.name
                ).read_bytes().replace(b'#include <zlib.h>\n', b''), file.name
    ordinary_main, observed_main = (
        (path / 'main.cpp').read_text() for path in (stock, observed)
    )
    calls = r'reference_network.add\(&defaultclock, (\w+)\);'
    core_calls = [
        name
        for name in re.findall(calls, observed_main)
        if not name.startswith(
            ('_run_reference_pre_', '_run_reference_before_', '_run_reference_end_')
        )
    ]
    assert core_calls == re.findall(calls, ordinary_main)
    assert (
        len(re.findall(r'reference_network.run\(', ordinary_main))
        == len(re.findall(r'reference_network.run\(', observed_main))
        == 1
    )
    assert observed_main.index(
        'reference_network.add(&defaultclock, +[]()'
    ) > observed_main.index(
        'reference_network.add(&defaultclock, _run_reference_end_codeobject);'
    )
    initialization = [
        [
            line.strip()
            for line in main.split('reference_network.clear();')[0].splitlines()
            if '_array_default_neurons_' in line and '=' in line
        ]
        for main in (ordinary_main, observed_main)
    ]
    assert initialization[0] == initialization[1]
    for field in ('v', 'g', 'lastspike'):
        assert any(
            f'_array_default_neurons_{field}[i] =' in line for line in initialization[0]
        )


@pytest.mark.parametrize(
    ('edges', 'channels'), ((True, False), (False, True), (False, False))
)
def test_silent_and_empty_edge_jobs_preserve_real_queue_geometry(
    edges: bool, channels: bool, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    sources = np.array([0, 0] if edges else [], dtype=np.int32)
    destinations = np.array([1, 2] if edges else [], dtype=np.int32)
    counts = np.array([360, -1] if edges else [], dtype=np.int32)
    connectome = Connectome(
        np.arange(3, dtype=np.int64), sources, destinations, counts, counts * 0.275
    )
    events = np.zeros((39, int(channels)), dtype=np.uint8)
    if channels:
        events[::3, 0] = 1
    destination = cast(str | None, request.config.getoption('--artifact-output'))
    root = (
        Path(destination) / f'brian-job-{edges}-{channels}' if destination else tmp_path
    )
    job = build(connectome, (0,) if channels else (), (), events, root / 'build')
    ledger = ReferenceQueues(sources, 3, events)
    final = None
    for frame in run(job, root / 'results'):
        if isinstance(frame, (StepSnapshot, FinalSnapshot)):
            ledger.check(frame)
        if isinstance(frame, FinalSnapshot):
            final = frame
    assert final is not None and len(final.step.pathways) == int(edges) + int(channels)
    values = results(job, root / 'results')
    if channels:
        assert np.array_equal(np.rint(values['spike_t'] / 0.0001), np.arange(1, 39, 3))
    else:
        assert values['spike_i'].size == 0 and final.step.source_cursor == -1


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
