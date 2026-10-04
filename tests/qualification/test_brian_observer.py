import gc
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
    case: NetworkCase, events: NDArray[np.uint8], output: Path, block_size: int
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
        block_size,
    )
    install(network, group, source, (recurrent, inputs), monitors, shape)
    network.run(len(events) * 0.1 * b.ms)
    b.prefs.devices.cpp_standalone.extra_make_args_unix = ['-j2']
    b.device.build(directory=str(output / 'standalone'), clean=False, with_output=False)
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
) -> dict[int, CapturedRun]:
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
            for size in (0, 1, 17, 32)
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


@pytest.mark.parametrize('block_size', [1, 17, 32])
def test_streamed_monitor_clearing_preserves_every_stock_phase_byte(
    runs: dict[int, CapturedRun], block_size: int
) -> None:
    stock = runs[0]
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
    runs: dict[int, CapturedRun],
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
    runs: dict[int, CapturedRun],
) -> None:
    for run in runs.values():
        final = run.frames[-1]
        assert isinstance(final, FinalSnapshot) and final.step.clock_step == 101
        for name, values in run.final.items():
            assert final.fields[name].tobytes() == values.tobytes(), name
        assert any(
            slot.size for queue in final.step.pathways[0].queues for slot in queue.slots
        )
