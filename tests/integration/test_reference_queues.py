import gzip
from dataclasses import replace
from pathlib import Path
from typing import Literal, cast

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.observer_stream import (
    FinalSnapshot,
    StepSnapshot,
    StreamShape,
    read_frames,
)
from fly_brain.qualification.adapters.reference_queues import ReferenceQueues

pytestmark = pytest.mark.integration
Record = tuple[
    NDArray[np.int32], NDArray[np.uint8], tuple[StepSnapshot | FinalSnapshot, ...]
]


@pytest.fixture(params=(0, 1, 17, 32))
def recorded(request: pytest.FixtureRequest) -> Record:
    evidence = (
        Path(__file__).resolve().parents[2]
        / 'docs/evidence/milestone-4/reference-observer'
    )
    size = cast(int, request.param)
    with np.load(evidence / 'input.npz') as inputs:
        sources = np.asarray(inputs['sources'], dtype=np.int32)
        events = np.asarray(inputs['events'], dtype=np.uint8)
    with gzip.open(evidence / f'block-{size}-observer.bin.gz', 'rb') as stream:
        frames = tuple(
            frame
            for frame in read_frames(stream, StreamShape(6, 101, 3, (8, 3), size))
            if isinstance(frame, (StepSnapshot, FinalSnapshot))
        )
    return sources, events, frames


def test_independent_ledger_checks_all_retained_actual_queue_modes(
    recorded: Record,
) -> None:
    sources, events, frames = recorded
    ledger = ReferenceQueues(sources, 6, events)
    for frame in frames:
        ledger.check(frame)
        assert len(ledger.pending) <= 19
    assert ledger.step == 101


@pytest.mark.parametrize(
    ('field', 'value', 'reason'),
    [
        ('source_cursor', -1, 'replay cursor'),
        ('source_spikes', np.array([2, 1, 0], dtype=np.int32), 'input channels'),
        ('spikes', np.array([0, 0], dtype=np.int32), 'duplicated'),
        ('spikes', np.array([6], dtype=np.int32), 'invalid'),
        ('step', 9, 'clock'),
    ],
)
def test_altered_discrete_observations_fail_the_ledger(
    recorded: Record, field: str, value: int | NDArray[np.int32], reason: str
) -> None:
    sources, events, frames = recorded
    first = frames[0]
    assert isinstance(first, StepSnapshot)
    ledger = ReferenceQueues(sources, 6, events)
    with pytest.raises(ValueError, match=reason):
        ledger.check(replace(first, **{field: value}))


@pytest.mark.parametrize('fault', ('offset', 'delivery', 'order', 'missing', 'replay'))
def test_altered_actual_queue_content_and_order_fail_the_ledger(
    recorded: Record, fault: Literal['offset', 'delivery', 'order', 'missing', 'replay']
) -> None:
    sources, events, frames = recorded
    first = frames[0]
    assert isinstance(first, StepSnapshot)
    position = int(fault == 'replay')
    pathway = first.pathways[position]
    queue = pathway.queues[0]
    slots = list(queue.slots)
    if fault in ('order', 'missing'):
        slot = next(index for index, edges in enumerate(slots) if len(edges) > 1)
        slots[slot] = (
            slots[slot][::-1] if fault == 'order' else np.empty(0, dtype=np.int32)
        )
    if fault == 'replay':
        slots[0] = np.array([0], dtype=np.int32)
    queue = replace(
        queue,
        slots=tuple(slots),
        offset=(queue.offset + 1) % 19 if fault == 'offset' else queue.offset,
    )
    pathway = replace(
        pathway,
        queues=(queue,),
        delivered=np.array([0], dtype=np.int32)
        if fault in ('delivery', 'replay')
        else pathway.delivered,
    )
    pathways = list(first.pathways)
    pathways[position] = pathway
    ledger = ReferenceQueues(sources, 6, events)
    with pytest.raises(ValueError, match='queue|delivery'):
        ledger.check(replace(first, pathways=tuple(pathways)))


def test_final_spike_space_cannot_change_after_the_last_step(recorded: Record) -> None:
    sources, events, frames = recorded
    ledger = ReferenceQueues(sources, 6, events)
    for frame in frames[:-1]:
        ledger.check(frame)
    final = frames[-1]
    assert isinstance(final, FinalSnapshot)
    changed = replace(final.step, spikes=np.array([6], dtype=np.int32))
    with pytest.raises(ValueError, match='final spike space'):
        ledger.check(replace(final, step=changed))
