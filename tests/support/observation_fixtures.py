import hashlib
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.models import Connectome, Stimulus
from fly_brain.simulation.observation_module import build_observation_sessions
from fly_brain.simulation.observations import ObservationInitialState


@dataclass(frozen=True)
class Fixture:
    connectome: Connectome
    targets: tuple[int, ...]
    events: NDArray[np.uint8]


def fixture(empty: bool = False) -> Fixture:
    counts = np.array([] if empty else [360, 0, 1, -2, 3, 360, -1, -1], dtype=np.int32)
    original = Connectome(
        np.arange(6, dtype=np.int64),
        np.array([] if empty else [0, 0, 0, 1, 2, 3, 4, 4], dtype=np.int32),
        np.array([] if empty else [1, 1, 0, 2, 3, 0, 5, 5], dtype=np.int32),
        counts,
        counts.astype(np.float64) * 0.275,
    )
    targets = () if empty else (0, 0, 1)
    events = np.zeros((4, 101, len(targets)), dtype=np.uint8)
    if targets:
        for trial in range(4):
            events[trial, trial::3, 0] = 1
            events[trial, trial::7, 1] = 1
            events[trial, trial::4, 2] = 1
    return Fixture(original, targets, events)


def initial(case: Fixture) -> ObservationInitialState:
    shape = (case.events.shape[0], 6)
    return ObservationInitialState(
        np.broadcast_to(
            np.array([-52, -52, -44, -44, -44, -52], dtype=np.float64), shape
        ),
        np.broadcast_to(np.array([0, 0, 100, 0, 0, 0], dtype=np.float64), shape),
        np.full(shape, -100000000, dtype=np.int32),
    )


def session_blocks(
    case: Fixture, precision: str, block_size: int
) -> list[SessionBlock]:
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (3,), precision
    )
    return list(
        observe_session(
            factory,
            case.connectome,
            case.targets,
            tuple(range(case.events.shape[0])),
            case.events,
            initial(case),
            block_size,
        )
    )


def stimulus_for(
    events: NDArray[np.uint8],
    targets: tuple[int, ...],
    rates_hz: tuple[float, ...],
    trial_indices: tuple[int, ...],
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
