import io
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.causal_artifacts import write_context
from fly_brain.qualification.adapters.causal_capture import CauseContext, ObservedStep
from fly_brain.qualification.adapters.observer_stream import StepSnapshot, read_frames
from tests.unit.test_observer_stream import queued_stream

pytestmark = pytest.mark.integration


def context() -> CauseContext:
    shape, parts = queued_stream()
    snapshot = next(read_frames(io.BytesIO(b''.join(parts)), shape))
    assert isinstance(snapshot, StepSnapshot)
    row = ObservedStep(
        snapshot,
        {'pre_v': np.array([-0.045, -0.044], dtype=np.float64)},
        {'pre_v': np.array([-45, -44], dtype=np.float32)},
        np.array([0, 2], dtype=np.int32),
        'actual-native-due-mask-hash',
    )
    return CauseContext((1,), row, row)


def test_cause_archive_preserves_native_phases_and_all_actual_queue_slots(
    tmp_path: Path,
) -> None:
    path = tmp_path / 'context.npz'
    actual = context()
    metadata = write_context(path, actual)
    assert metadata['neurons'] == [1]
    with np.load(path, allow_pickle=False) as artifact:
        assert len(artifact.files) == 52
        for position in ('current', 'previous'):
            assert (
                artifact[f'{position}_reference_pre_v'].tobytes()
                == actual.current.reference['pre_v'].tobytes()
            )
            assert (
                artifact[f'{position}_mlx_pre_v'].tobytes()
                == actual.current.mlx['pre_v'].tobytes()
            )
            assert artifact[
                f'{position}_reference_pathway_0_queue_0_slot_18'
            ].tolist() == [0, 2]
