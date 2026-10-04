import gc
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import brian2 as b
import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters import brian_reference
from fly_brain.qualification.adapters.brian_observer import install
from fly_brain.qualification.adapters.observer_stream import (
    PHASE_FIELDS,
    FinalSnapshot,
    ObservationArray,
    PhaseBlock,
    StepSnapshot,
    StreamShape,
    read_frames,
)
from fly_brain.simulation.models import NetworkCase

pytestmark = [pytest.mark.integration, pytest.mark.reference]

Frame = StepSnapshot | PhaseBlock | FinalSnapshot


@dataclass(frozen=True)
class CapturedRun:
    frames: tuple[Frame, ...]
    phases: dict[str, ObservationArray]
    final: dict[str, ObservationArray]
    spike_coordinates: NDArray[np.int64]
    directory: Path


def execute(
    case: NetworkCase, events: NDArray[np.uint8], output: Path, block_size: int | None
) -> CapturedRun:
    output.mkdir(parents=True, exist_ok=False)
    b.device.reinit()
    b.set_device('cpp_standalone', build_on_run=False)
    b.start_scope()
    gc.collect()
    b.defaultclock.dt = 0.1 * b.ms
    params = brian_reference.default_parameters()
    group = b.NeuronGroup(
        case.neurons,
        params['eqs'],
        method='linear',
        threshold=params['eq_th'],
        reset=params['eq_rst'],
        refractory='rfc',
        namespace=params,
        name='observed_neurons',
    )
    group.v = np.broadcast_to(case.voltage, (case.neurons,)) * b.mV
    group.g = np.broadcast_to(case.synaptic, (case.neurons,)) * b.mV
    group.lastspike = np.broadcast_to(case.last_spike, (case.neurons,)) * 0.1 * b.ms
    refractory = np.full(case.neurons, 2.2)
    refractory[list(case.targets)] = 0
    group.rfc = refractory * b.ms
    recurrent = b.Synapses(
        group,
        group,
        'w : volt',
        on_pre='g += w',
        delay=1.8 * b.ms,
        name='observed_recurrent',
    )
    recurrent.connect(
        i=np.asarray(case.sources, dtype=np.int32),
        j=np.asarray(case.destinations, dtype=np.int32),
    )
    recurrent.w = np.where(np.isin(case.sources, case.silenced), 0, case.weights) * b.mV
    steps, channels = np.nonzero(events)
    source = b.SpikeGeneratorGroup(
        len(case.targets), channels, steps * 0.1 * b.ms, name='observed_source'
    )
    inputs = b.Synapses(source, group, on_pre='v += 68.75*mV', name='observed_input')
    inputs.connect(i=np.arange(len(case.targets)), j=np.asarray(case.targets))
    inputs.pre.order = 0
    monitors = (
        b.StateMonitor(
            group,
            ('v', 'g', 'not_refractory'),
            record=True,
            when='thresholds',
            order=-1,
            name='observed_pre',
        ),
        b.StateMonitor(
            group,
            ('v', 'g', 'not_refractory'),
            record=True,
            when='resets',
            order=-1,
            name='observed_before',
        ),
        b.StateMonitor(
            group,
            ('v', 'g', 'lastspike', 'not_refractory'),
            record=True,
            when='end',
            name='observed_end',
        ),
    )
    spikes = b.SpikeMonitor(group)
    network = b.Network(
        group, recurrent, source, inputs, *monitors, spikes, name='observed_network'
    )
    shape = StreamShape(
        case.neurons,
        len(events),
        len(case.targets),
        (len(case.sources), len(case.targets)),
        block_size or 0,
    )
    if block_size is not None:
        install(network, group, source, (recurrent, inputs), monitors, shape)
    network.run(len(events) * 0.1 * b.ms)
    b.prefs.devices.cpp_standalone.extra_make_args_unix = ['-j2']
    b.device.build(directory=str(output / 'standalone'), clean=False, with_output=False)
    frames: tuple[Frame, ...] = ()
    if block_size is not None:
        with (output / 'standalone/results/stdout.txt').open('rb') as recorded:
            frames = tuple(read_frames(recorded, shape))
    phases: dict[str, ObservationArray] = {}
    if block_size:
        blocks = [frame for frame in frames if isinstance(frame, PhaseBlock)]
        phases = {
            name: np.concatenate([block.fields[name] for block in blocks])
            for name in blocks[0].fields
        }
    else:
        for monitor, (phase, names) in zip(monitors, PHASE_FIELDS, strict=True):
            phases[phase + '_t'] = np.asarray(monitor.t[:], dtype=np.float64)
            for name in names:
                values = getattr(monitor, name)
                phases[phase + '_' + name] = np.asarray(
                    values[:],
                    dtype=np.bool_ if name == 'not_refractory' else np.float64,
                ).T
    final = {
        name: np.asarray(
            getattr(group, name)[:],
            dtype=np.bool_ if name == 'not_refractory' else np.float64,
        )
        for name in ('v', 'g', 'lastspike', 'not_refractory')
    }
    coordinates = np.column_stack(
        (
            np.rint(spikes.t[:] / (0.1 * b.ms)).astype(np.int64),
            np.asarray(spikes.i[:], dtype=np.int64),
        )
    )
    np.savez_compressed(
        output / 'phases.npz',
        **phases,
        **{'final_' + name: values for name, values in final.items()},
        spike_coordinates=coordinates,
    )
    return CapturedRun(frames, phases, final, coordinates, output)


@pytest.fixture(scope='module')
def runs(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> dict[int | None, CapturedRun]:
    destination = cast(str | None, request.config.getoption('--artifact-output'))
    output = (
        Path(destination) / 'brian-observer'
        if destination
        else tmp_path_factory.mktemp('brian-observer')
    )
    case = NetworkCase(
        6,
        sources=(0, 0, 0, 1, 2, 3, 4, 4),
        destinations=(1, 1, 0, 2, 3, 0, 5, 5),
        weights=(100, 0, 0.275, -0.55, 0.825, 100, -0.275, -0.275),
        targets=(0, 0, 1),
        silenced=(3,),
        voltage=np.array([-52, -52, -44, -44, -44, -52]),
        synaptic=np.array([0, 0, 100, 0, 0, 0]),
    )
    events = np.zeros((101, 3), dtype=np.uint8)
    events[::3, 0] = 1
    events[::7, 1] = 1
    events[::4, 2] = 1
    try:
        result = {
            size: execute(case, events, output / f'block-{size}', size)
            for size in (None, 0, 1, 17, 32)
        }
    finally:
        b.device.reinit()
        b.set_device('runtime')
    np.savez_compressed(
        output / 'input.npz',
        events=events,
        sources=np.asarray(case.sources),
        destinations=np.asarray(case.destinations),
        weights=np.asarray(case.weights),
    )
    return result


@pytest.mark.parametrize('block_size', [0, 1, 17, 32])
def test_streamed_monitor_clearing_preserves_every_stock_phase_byte(
    runs: dict[int | None, CapturedRun], block_size: int
) -> None:
    stock = runs[None]
    observed = runs[block_size]
    assert stock.phases.keys() == observed.phases.keys()
    for name, values in stock.phases.items():
        assert (values.dtype, values.shape, values.tobytes()) == (
            observed.phases[name].dtype,
            observed.phases[name].shape,
            observed.phases[name].tobytes(),
        ), name
    assert stock.spike_coordinates.tobytes() == observed.spike_coordinates.tobytes()
    for name, values in stock.final.items():
        assert values.tobytes() == observed.final[name].tobytes(), name


def test_all_physical_queue_and_cursor_observations_are_partition_independent(
    runs: dict[int | None, CapturedRun],
) -> None:
    expected = [frame for frame in runs[0].frames if isinstance(frame, StepSnapshot)]
    for size in (1, 17, 32):
        actual = [
            frame for frame in runs[size].frames if isinstance(frame, StepSnapshot)
        ]
        assert len(actual) == len(expected) == 101
        for first, second in zip(expected, actual, strict=True):
            assert (
                first.step,
                first.clock_step,
                first.time_s,
                first.source_cursor,
            ) == (second.step, second.clock_step, second.time_s, second.source_cursor)
            assert first.spikes.tobytes() == second.spikes.tobytes()
            assert first.source_spikes.tobytes() == second.source_spikes.tobytes()
            for left, right in zip(first.pathways, second.pathways, strict=True):
                assert left.delivered.tobytes() == right.delivered.tobytes()
                for a, b_queue in zip(left.queues, right.queues, strict=True):
                    assert a.offset == b_queue.offset
                    assert tuple(slot.tobytes() for slot in a.slots) == tuple(
                        slot.tobytes() for slot in b_queue.slots
                    )


def test_final_frame_observes_real_neural_state_and_pending_queue(
    runs: dict[int | None, CapturedRun],
) -> None:
    for run in runs.values():
        if not run.frames:
            continue
        final = run.frames[-1]
        assert isinstance(final, FinalSnapshot) and final.step.clock_step == 101
        for name, values in run.final.items():
            assert final.fields[name].tobytes() == values.tobytes(), name
        assert any(
            slot.size for queue in final.step.pathways[0].queues for slot in queue.slots
        )


def test_every_actual_queue_slot_and_delivery_matches_an_independent_event_ledger(
    runs: dict[int | None, CapturedRun],
) -> None:
    with np.load(runs[0].directory.parent / 'input.npz') as recorded:
        events = np.asarray(recorded['events'], dtype=np.uint8)
        sources = np.asarray(recorded['sources'], dtype=np.int64)
    outgoing = [
        np.flatnonzero(sources == neuron).astype(np.int32) for neuron in range(6)
    ]
    for run in runs.values():
        if not run.frames:
            continue
        snapshots = [frame for frame in run.frames if isinstance(frame, StepSnapshot)]
        ledger: dict[int, NDArray[np.int32]] = {}
        cursor = 0
        for snapshot in snapshots:
            step = snapshot.step
            spikes = run.spike_coordinates[run.spike_coordinates[:, 0] == step, 1]
            assert np.array_equal(snapshot.spikes, spikes), step
            ledger[step + 18] = np.concatenate(
                [
                    np.empty(0, dtype=np.int32),
                    *(outgoing[int(index)] for index in spikes),
                ]
            ).astype(np.int32)
            recurrent, replay = snapshot.pathways
            queue = recurrent.queues[0]
            assert len(queue.slots) == 19 and queue.offset == (step + 1) % 19
            for position, actual in enumerate(queue.slots):
                due = step + (position - queue.offset) % 19
                expected = ledger.get(due, np.empty(0, dtype=np.int32))
                assert np.array_equal(actual, expected), (step, position)
            assert np.array_equal(recurrent.delivered, queue.slots[queue.offset])
            channels = np.flatnonzero(events[step]).astype(np.int32)
            cursor += len(channels)
            assert snapshot.source_cursor == cursor
            assert np.array_equal(snapshot.source_spikes, channels)
            assert replay.queues[0].offset == 0 and len(replay.queues[0].slots) == 1
            assert np.array_equal(replay.queues[0].slots[0], channels)
            assert np.array_equal(replay.delivered, channels)
        final = run.frames[-1]
        assert isinstance(final, FinalSnapshot) and final.step.source_cursor == cursor
        for actual, expected in zip(
            final.step.pathways, snapshots[-1].pathways, strict=True
        ):
            assert actual.delivered.tobytes() == expected.delivered.tobytes()
            for left, right in zip(actual.queues, expected.queues, strict=True):
                assert left.offset == right.offset
                assert tuple(slot.tobytes() for slot in left.slots) == tuple(
                    slot.tobytes() for slot in right.slots
                )


def test_observer_preserves_generated_numerical_code_initialization_and_schedule(
    runs: dict[int | None, CapturedRun],
) -> None:
    stock = runs[None].directory / 'standalone'
    files = {
        path.relative_to(stock)
        for path in stock.rglob('*')
        if path.is_file()
        and (
            path.suffix in ('.cpp', '.h')
            or path.parent.name == 'static_arrays'
            or path.name == 'makefile'
        )
        and path.name != 'main.cpp'
    }
    main = (stock / 'main.cpp').read_text()
    clock_write = '        _array_defaultclock_dt[0] = 0.0001;\n'
    consecutive_clock_writes = '(?:' + re.escape(clock_write) + ')+'
    initialization = main.split('observed_network.clear();')[0]
    assert clock_write in initialization
    initialization = re.sub(consecutive_clock_writes, clock_write, initialization)
    calls = re.findall(r'observed_network.add\(&defaultclock, (\w+)\);', main)
    assert calls == [
        '_run_observed_neurons_stateupdater_codeobject',
        '_run_observed_pre_codeobject',
        '_run_observed_neurons_spike_thresholder_codeobject',
        '_run_observed_source_codeobject',
        '_run_spikemonitor_codeobject',
        '_run_observed_recurrent_pre_push_spikes',
        '_run_observed_recurrent_pre_codeobject',
        '_run_observed_input_pre_push_spikes',
        '_run_observed_input_pre_codeobject',
        '_run_observed_before_codeobject',
        '_run_observed_neurons_spike_resetter_codeobject',
        '_run_observed_end_codeobject',
    ]
    invocation = re.findall(r'observed_network.run\([^;]+;', main)
    assert len(invocation) == 1
    assert '-O3 -ffast-math -fno-finite-math-only' in (stock / 'makefile').read_text()
    for size in (0, 1, 17, 32):
        directory = runs[size].directory / 'standalone'
        for name in files:
            assert (stock / name).read_bytes() == (directory / name).read_bytes(), name
        observed = (directory / 'main.cpp').read_text()
        observed_initialization = observed.split('observed_network.clear();')[0]
        assert clock_write in observed_initialization
        assert (
            re.sub(consecutive_clock_writes, clock_write, observed_initialization)
            == initialization
        )
        assert (
            re.findall(r'observed_network.add\(&defaultclock, (\w+)\);', observed)
            == calls
        )
        assert re.findall(r'observed_network.run\([^;]+;', observed) == invocation
        assert observed.index(
            'observed_network.add(&defaultclock, +[]()'
        ) > observed.index(
            'observed_network.add(&defaultclock, _run_observed_end_codeobject);'
        )
