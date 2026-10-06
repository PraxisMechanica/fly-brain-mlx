from collections.abc import Mapping

import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.simulation.observations import HostArray, HostFieldSnapshots


def trial_fields(fields: Mapping[str, HostArray], trial: int) -> HostFieldSnapshots:
    return HostFieldSnapshots.capture(
        {name: value[:, trial : trial + 1] for name, value in fields.items()}
    )


def replace_block(
    block: SessionBlock,
    *,
    begin: int | None = None,
    rows: int | None = None,
    fields: Mapping[str, HostArray] | None = None,
    checks: NDArray[np.bool_] | None = None,
    due_edges: tuple[tuple[NDArray[np.int32], ...], ...] | None = None,
) -> SessionBlock:
    return SessionBlock(
        block.begin if begin is None else begin,
        block.rows if rows is None else rows,
        block.trial_indices,
        block.fields if fields is None else fields,
        block.checks if checks is None else checks,
        block.queue_sha256,
        block.queue_slot_sha256,
        block.final_queue,
        block.due_edges if due_edges is None else due_edges,
        block.due_sha256,
    )
