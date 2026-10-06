from collections.abc import Mapping
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.observations import (
    HostArray,
    HostFieldSnapshots,
    HostSnapshot,
)


def capture_final_queue(
    queue: NDArray[np.bool_] | None,
) -> HostSnapshot[np.bool_] | None:
    return None if queue is None else HostSnapshot.capture(queue)


def capture_due_rows(
    rows: tuple[tuple[NDArray[np.int32], ...], ...],
) -> tuple[tuple[HostSnapshot[np.int32], ...], ...]:
    return tuple(tuple(HostSnapshot.capture(value) for value in row) for row in rows)


@dataclass(frozen=True, init=False)
class SessionBlock:
    begin: int
    rows: int
    trial_indices: tuple[int, ...]
    _fields_snapshot: HostFieldSnapshots = field(init=False, repr=False)
    _checks_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)
    queue_sha256: tuple[str, ...]
    queue_slot_sha256: tuple[tuple[str, ...], ...]
    _final_queue_snapshot: HostSnapshot[np.bool_] | None = field(init=False, repr=False)
    _due_edges_snapshot: tuple[tuple[HostSnapshot[np.int32], ...], ...] = field(
        init=False, repr=False
    )
    due_sha256: tuple[tuple[str, ...], ...]

    def __init__(
        self,
        begin: int,
        rows: int,
        trial_indices: tuple[int, ...],
        fields: Mapping[str, HostArray],
        checks: NDArray[np.bool_],
        queue_sha256: tuple[str, ...],
        queue_slot_sha256: tuple[tuple[str, ...], ...],
        final_queue: NDArray[np.bool_] | None,
        due_edges: tuple[tuple[NDArray[np.int32], ...], ...],
        due_sha256: tuple[tuple[str, ...], ...],
    ) -> None:
        object.__setattr__(self, 'begin', begin)
        object.__setattr__(self, 'rows', rows)
        object.__setattr__(self, 'trial_indices', trial_indices)
        object.__setattr__(self, '_fields_snapshot', HostFieldSnapshots.capture(fields))
        object.__setattr__(self, '_checks_snapshot', HostSnapshot.capture(checks))
        object.__setattr__(self, 'queue_sha256', queue_sha256)
        object.__setattr__(self, 'queue_slot_sha256', queue_slot_sha256)
        object.__setattr__(
            self, '_final_queue_snapshot', capture_final_queue(final_queue)
        )
        object.__setattr__(self, '_due_edges_snapshot', capture_due_rows(due_edges))
        object.__setattr__(self, 'due_sha256', due_sha256)

    @property
    def fields(self) -> Mapping[str, HostArray]:
        return self._fields_snapshot.fields

    @property
    def checks(self) -> NDArray[np.bool_]:
        return self._checks_snapshot.array

    @property
    def final_queue(self) -> NDArray[np.bool_] | None:
        return (
            None
            if self._final_queue_snapshot is None
            else self._final_queue_snapshot.array
        )

    @property
    def due_edges(self) -> tuple[tuple[NDArray[np.int32], ...], ...]:
        return tuple(
            tuple(value.array for value in row) for row in self._due_edges_snapshot
        )
