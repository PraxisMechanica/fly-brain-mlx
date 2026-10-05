import io
from dataclasses import replace
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
    previous = replace(
        row,
        reference={'pre_v': np.array([-0.046, -0.045], dtype=np.float64)},
        mlx={'pre_v': np.array([-46, -45], dtype=np.float32)},
    )
    return CauseContext((1,), row, previous)


def test_cause_archive_preserves_native_phases_and_all_actual_queue_slots(
    tmp_path: Path,
) -> None:
    path = tmp_path / 'context.npz'
    actual = context()
    metadata = write_context(path, actual)
    assert metadata['neurons'] == [1]
    with np.load(path, allow_pickle=False) as artifact:
        assert len(artifact.files) == 52
        for position, observed in (
            ('current', actual.current),
            ('previous', actual.previous),
        ):
            assert observed is not None
            assert (
                artifact[f'{position}_reference_pre_v'].tobytes()
                == observed.reference['pre_v'].tobytes()
            )
            assert (
                artifact[f'{position}_mlx_pre_v'].tobytes()
                == observed.mlx['pre_v'].tobytes()
            )
            for engine, fields in (
                ('reference', observed.reference),
                ('mlx', observed.mlx),
            ):
                for name, value in fields.items():
                    saved = artifact[f'{position}_{engine}_{name}']
                    assert (saved.dtype, saved.shape, saved.tobytes()) == (
                        value.dtype,
                        value.shape,
                        value.tobytes(),
                    )
            for slot, value in enumerate(observed.snapshot.pathways[0].queues[0].slots):
                saved = artifact[f'{position}_reference_pathway_0_queue_0_slot_{slot}']
                assert (saved.dtype, saved.shape, saved.tobytes()) == (
                    value.dtype,
                    value.shape,
                    value.tobytes(),
                )


def test_existing_cause_evidence_cannot_be_overwritten(tmp_path: Path) -> None:
    path = tmp_path / 'retained.npz'
    path.write_bytes(b'preserved evidence')
    with pytest.raises(FileExistsError):
        write_context(path, context())
    assert path.read_bytes() == b'preserved evidence'
