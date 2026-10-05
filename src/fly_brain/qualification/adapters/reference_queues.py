import numpy as np
from numpy.typing import NDArray

from .observer_stream import FinalSnapshot, StepSnapshot


class ReferenceQueues:
    def __init__(
        self, sources: NDArray[np.int32], neurons: int, events: NDArray[np.uint8]
    ) -> None:
        self.order = np.argsort(sources, kind='stable').astype(np.int32)
        self.offsets = np.concatenate(
            ([0], np.cumsum(np.bincount(sources, minlength=neurons)))
        )
        self.events = events
        self.pending: dict[int, NDArray[np.int32]] = {}
        self.step = self.cursor = 0
        self.spikes = np.empty(0, dtype=np.int32)

    def check(self, frame: StepSnapshot | FinalSnapshot) -> None:
        final = isinstance(frame, FinalSnapshot)
        snapshot = frame.step if isinstance(frame, FinalSnapshot) else frame
        if snapshot.step != self.step or (final and self.step != len(self.events)):
            raise ValueError('Reference ledger clock or final horizon differs')
        step = self.step - int(final)
        if final:
            if not np.array_equal(snapshot.spikes, self.spikes):
                raise ValueError(
                    'Reference final spike space changed after the last step'
                )
        else:
            if (
                np.any(snapshot.spikes < 0)
                or np.any(snapshot.spikes >= len(self.offsets) - 1)
                or np.any(np.diff(snapshot.spikes) <= 0)
            ):
                raise ValueError('Reference spike identities are invalid or duplicated')
            self.spikes = snapshot.spikes
            self.pending[step + 18] = np.concatenate(
                [
                    np.empty(0, dtype=np.int32),
                    *(
                        self.order[self.offsets[index] : self.offsets[index + 1]]
                        for index in snapshot.spikes
                    ),
                ]
            )
        channels = np.flatnonzero(self.events[step]).astype(np.int32)
        if not final:
            self.cursor += len(channels)
        cursor = self.cursor if self.events.shape[1] else -1
        if snapshot.source_cursor != cursor or not np.array_equal(
            snapshot.source_spikes, channels
        ):
            raise ValueError('Reference replay cursor or input channels differ')
        recurrent = bool(self.order.size)
        if len(snapshot.pathways) != int(recurrent) + int(bool(self.events.shape[1])):
            raise ValueError('Reference pathway count differs from original inputs')
        if recurrent:
            pathway = snapshot.pathways[0]
            queue = pathway.queues[0]
            if (
                len(queue.slots) != 19
                or queue.offset != (step + 1) % 19
                or not np.array_equal(pathway.delivered, queue.slots[queue.offset])
            ):
                raise ValueError(
                    'Reference delivery or physical queue geometry differs'
                )
            for position, actual in enumerate(queue.slots):
                due = step + (position - queue.offset) % 19
                expected = self.pending.get(due, np.empty(0, dtype=np.int32))
                if not np.array_equal(actual, expected):
                    raise ValueError(
                        f'Reference original-row queue differs at step {step}, slot {position}'
                    )
        if self.events.shape[1]:
            pathway = snapshot.pathways[int(recurrent)]
            queue = pathway.queues[0]
            if (
                queue.offset != 0
                or len(queue.slots) != 1
                or not np.array_equal(queue.slots[0], channels)
                or not np.array_equal(pathway.delivered, channels)
            ):
                raise ValueError(
                    'Reference actual replay queue differs from channel bits'
                )
        if not final:
            self.pending.pop(step - 1, None)
            self.step += 1
