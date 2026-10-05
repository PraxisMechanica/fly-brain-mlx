import io
from dataclasses import replace

import numpy as np
import pytest

from fly_brain.qualification.adapters.observer_evidence import (
    array_record,
    physical_hash,
)
from fly_brain.qualification.adapters.observer_stream import StepSnapshot, read_frames
from tests.unit.test_observer_stream import queued_stream

pytestmark = pytest.mark.unit


def test_native_evidence_preserves_precision_shape_and_signed_zero() -> None:
    value = np.array([-0.0, 1], dtype=np.float64)
    saved = array_record(value)
    assert saved['dtype'] == '<f8' and saved['shape'] == [2]
    assert saved != array_record(value.astype(np.float32))
    assert saved != array_record(np.array([0.0, 1], dtype=np.float64))
    assert saved != array_record(value.reshape(2, 1))


@pytest.mark.parametrize(
    'field,value',
    (('step', 1), ('clock_step', 1), ('time_s', 0.0001), ('source_cursor', 0)),
)
def test_physical_digest_includes_actual_clock_and_source_cursor(
    field: str, value: int | float
) -> None:
    shape, parts = queued_stream()
    snapshot = next(read_frames(io.BytesIO(b''.join(parts)), shape))
    assert isinstance(snapshot, StepSnapshot)
    assert physical_hash(snapshot) != physical_hash(replace(snapshot, **{field: value}))


def test_physical_digest_detects_ordered_spikes_delivery_and_every_queue_position() -> (
    None
):
    shape, parts = queued_stream()
    snapshot = next(read_frames(io.BytesIO(b''.join(parts)), shape))
    assert isinstance(snapshot, StepSnapshot)
    pathway = snapshot.pathways[0]
    queue = pathway.queues[0]
    pathway = replace(pathway, delivered=queue.slots[-1])
    snapshot = replace(
        snapshot,
        spikes=np.array([0, 1], dtype=np.int32),
        source_spikes=np.array([0, 1], dtype=np.int32),
        pathways=(pathway,),
    )
    changed_queues = (
        replace(queue, offset=1),
        replace(queue, slots=queue.slots[::-1]),
        replace(queue, slots=(*queue.slots[:-1], queue.slots[-1][::-1])),
    )
    changed = (
        replace(snapshot, spikes=snapshot.spikes[::-1]),
        replace(snapshot, source_spikes=snapshot.source_spikes[::-1]),
        replace(
            snapshot, pathways=(replace(pathway, delivered=pathway.delivered[::-1]),)
        ),
        *(
            replace(snapshot, pathways=(replace(pathway, queues=(value,)),))
            for value in changed_queues
        ),
    )
    assert len({physical_hash(value) for value in (snapshot, *changed)}) == 7
