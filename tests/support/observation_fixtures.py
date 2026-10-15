import hashlib
from dataclasses import dataclass

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import (
    HostArray,
    as_host,
    boolean_input,
    evaluate,
)
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.identifiers import (
    FlyWireIds64,
    NeuronRow,
    NeuronRows32,
    TrialId,
)
from fly_brain.simulation.models import Connectome, Stimulus
from fly_brain.simulation.observation_module import build_observation_sessions
from fly_brain.simulation.observations import ObservationInitialState


@dataclass(frozen=True)
class Fixture:
    connectome: Connectome
    targets: tuple[NeuronRow, ...]
    events: NDArray[np.uint8]


def fixture(empty: bool = False) -> Fixture:
    counts = np.array([] if empty else [360, 0, 1, -2, 3, 360, -1, -1], dtype=np.int32)
    original = Connectome(
        FlyWireIds64(np.arange(6, dtype=np.int64)),
        NeuronRows32(
            np.array([] if empty else [0, 0, 0, 1, 2, 3, 4, 4], dtype=np.int32)
        ),
        NeuronRows32(
            np.array([] if empty else [1, 1, 0, 2, 3, 0, 5, 5], dtype=np.int32)
        ),
        counts,
        counts.astype(np.float64) * 0.275,
    )
    targets = () if empty else (NeuronRow(0), NeuronRow(0), NeuronRow(1))
    events = np.zeros((4, 101, len(targets)), dtype=np.uint8)
    if targets:
        for trial in range(4):
            events[trial, trial::3, 0] = 1
            events[trial, trial::7, 1] = 1
            events[trial, trial::4, 2] = 1
    return Fixture(original, targets, events)


def initial(case: Fixture) -> ObservationInitialState:
    shape = (case.events.shape[0], 6)
    last = np.full(shape, -100000000, dtype=np.int32)
    last[:, 5] = -10
    return ObservationInitialState(
        np.broadcast_to(
            np.array([-52, -52, -44, -44, -44, -52], dtype=np.float64), shape
        ),
        np.broadcast_to(np.array([0, 0, 100, 0, 0, 0], dtype=np.float64), shape),
        last,
    )


def session_blocks(
    case: Fixture, precision: str, block_size: int
) -> list[SessionBlock]:
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (NeuronRow(3),), precision
    )
    return list(
        observe_session(
            factory,
            case.connectome,
            case.targets,
            tuple(map(TrialId, range(case.events.shape[0]))),
            case.events,
            initial(case),
            block_size,
        )
    )


def stimulus_for(
    events: NDArray[np.uint8],
    targets: tuple[NeuronRow, ...],
    rates_hz: tuple[float, ...],
    trial_indices: tuple[TrialId, ...],
) -> Stimulus:
    return Stimulus(
        events,
        targets,
        rates_hz,
        trial_indices,
        0,
        0,
        hashlib.sha256(events.tobytes()).hexdigest(),
    )


def ordinary_phases(
    case: Fixture, precision: str, starting: ObservationInitialState | None
) -> dict[str, HostArray]:
    execution = prepare(case.connectome, case.targets, (3,), precision)
    trials = case.events.shape[0]
    state = (
        core.initial_state(execution.network, trials)
        if starting is None
        else core.initial_state(
            execution.network,
            trials,
            starting.voltage_mv,
            starting.synaptic_mv,
            starting.last_spike_step,
        )
    )
    rows: dict[str, list[mx.array]] = {}
    for step in range(case.events.shape[1]):
        with mx.stream(mx.gpu):
            inputs = boolean_input(case.events[:, step, :].astype(np.bool_))
            state, trace = execution.advance(state, inputs)
            evaluate(*state[:-1], trace.spikes)
        for name, value in (
            ('pre_v', trace.pre_voltage_mv),
            ('pre_u', trace.pre_voltage_offset_mv),
            ('pre_g', trace.pre_synaptic_mv),
            ('pre_not_refractory', trace.available),
            ('spikes', trace.spikes),
            ('before_v', trace.before_reset_voltage_mv),
            ('before_u', trace.before_reset_voltage_offset_mv),
            ('before_g', trace.before_reset_synaptic_mv),
            ('before_not_refractory', trace.receiving),
            ('end_v', state.voltage_mv),
            ('end_u', state.voltage_offset_mv),
            ('end_g', state.synaptic_mv),
            ('end_last_spike_step', state.last_spike_step),
            ('end_not_refractory', trace.receiving),
            ('accepted_inputs', trace.accepted_inputs),
            ('due', trace.due),
        ):
            rows.setdefault(name, []).append(value)
        rows.setdefault('queue', []).append(state.queue)
    with mx.stream(mx.gpu):
        arrays = {name: mx.stack(values) for name, values in rows.items()}
        evaluate(*arrays.values())
        return {name: as_host(value) for name, value in arrays.items()}
