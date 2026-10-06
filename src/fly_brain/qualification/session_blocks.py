from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.observations import (
    HostArray,
    HostFieldSnapshots,
    HostSnapshot,
    snapshot_view,
)


@dataclass(frozen=True)
class SessionBlock:
    begin: int
    rows: int
    trial_indices: tuple[int, ...]
    fields: Mapping[str, HostArray]
    checks: NDArray[np.bool_]
    queue_sha256: tuple[str, ...]
    queue_slot_sha256: tuple[tuple[str, ...], ...]
    final_queue: NDArray[np.bool_] | None
    due_edges: tuple[tuple[NDArray[np.int32], ...], ...]
    due_sha256: tuple[tuple[str, ...], ...]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        object.__setattr__(self, 'fields', HostFieldSnapshots.capture(self.fields))
        object.__setattr__(
            self,
            'checks',
            HostSnapshot.capture(self.checks),
        )
        if self.final_queue is not None:
            value = self.final_queue
            object.__setattr__(
                self,
                'final_queue',
                HostSnapshot.capture(value),
            )
        object.__setattr__(
            self,
            'due_edges',
            tuple(
                tuple(HostSnapshot.capture(value) for value in row)
                for row in self.due_edges
            ),
        )
