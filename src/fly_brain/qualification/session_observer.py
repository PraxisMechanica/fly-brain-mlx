from collections.abc import Generator

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.models import Connectome
from fly_brain.simulation.observations import (
    HostArray,
    ObservationInitialState,
    ObservationOperands,
)

from .ports import ObservationSessionFactory
from .session_blocks import SessionBlock
from .session_expectations import (
    expect_step,
    initial_ledger,
    observation_checks,
    require_configuration,
    require_physical_queue,
)


def observe_session(
    factory: ObservationSessionFactory,
    connectome: Connectome,
    targets: tuple[int, ...],
    trial_indices: tuple[int, ...],
    events: NDArray[np.uint8],
    initial: ObservationInitialState | None = None,
    block_size: int = 32,
) -> Generator[SessionBlock, None, None]:
    if not 1 <= block_size <= 32:
        raise ValueError('MLX observer blocks must contain 1 to 32 steps')
    if (
        events.dtype != np.uint8
        or events.ndim != 3
        or events.shape[0] != len(trial_indices)
        or events.shape[2] != len(targets)
        or not events.shape[1]
        or np.any(events > 1)
    ):
        raise ValueError('Observation requires complete canonical trial/channel events')
    session = factory(trial_indices, initial)
    configuration = session.configuration
    ledger = initial_ledger(connectome, targets, len(trial_indices), initial)
    require_configuration(
        configuration, connectome, targets, trial_indices, initial, ledger
    )
    steps = events.shape[1]
    for begin in range(0, steps, block_size):
        end = min(begin + block_size, steps)
        rows: dict[str, list[HostArray]] = {}
        checks: list[NDArray[np.bool_]] = []
        due_edges: list[tuple[NDArray[np.int32], ...]] = []
        due_sha256: list[tuple[str, ...]] = []
        operands: ObservationOperands | None = None
        for step in range(begin, end):
            inputs = events[:, step, :].astype(np.bool_)
            actual = session.advance(inputs)
            if actual.trial_indices != trial_indices:
                raise ValueError('Actual observation trial order differs')
            ledger, operands = expect_step(ledger, actual, inputs, connectome, targets)
            flags = observation_checks(actual, session.compare(operands), operands)
            if not flags.all():
                raise ValueError(
                    'Actual native observation failed independent qualification checks'
                )
            checks.append(flags)
            due_edges.append(actual.due_edges)
            due_sha256.append(actual.due_sha256)
            for name, value in actual.fields.items():
                rows.setdefault(name, []).append(value)
        queue = session.physical_queue()
        if operands is None:
            raise ValueError('Observation block is missing actual comparison operands')
        require_physical_queue(queue, operands, end, trial_indices)
        yield SessionBlock(
            begin,
            end - begin,
            trial_indices,
            {name: np.stack(values) for name, values in rows.items()},
            np.stack(checks),
            queue.sha256,
            queue.slot_sha256,
            queue.queue if end == steps else None,
            tuple(due_edges),
            tuple(due_sha256),
        )
