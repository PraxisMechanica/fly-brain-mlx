import gzip
from pathlib import Path
from typing import cast

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
