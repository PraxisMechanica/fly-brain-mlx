import json
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.pending_queues import verify

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault',
    (
        'none',
        'future',
        'cleared',
        'offset',
        'clock',
        'dtype',
        'duplicate',
        'bounds',
        'geometry',
        'mapping',
    ),
)
def test_pending_delivery_compares_actual_future_rows_and_excludes_delivered_history(
    tmp_path: Path, fault: str
) -> None:
    steps, offset = 101, 101 % 19
    metadata = {'step': steps, 'clock_step': steps + int(fault == 'clock')}
    (tmp_path / 'reference-final-physical.json').write_text(json.dumps(metadata))
    sources = np.array([0, 1, 1, 2], dtype=np.int32)
    queue = np.zeros((19, 1, 3), dtype=np.bool_)
    queue[steps % 19, 0, 1] = True
    queue[(steps + 17) % 19, 0, 2] = True
    arrays: dict[str, NDArray[np.generic]] = {
        'reference_pathway_0_queue_0_offset': np.asarray(
            offset + int(fault == 'offset'), dtype=np.int32
        ),
        **{
            f'reference_pathway_0_queue_0_slot_{slot}': np.empty(0, dtype=np.int32)
            for slot in range(19)
        },
    }
    arrays[f'reference_pathway_0_queue_0_slot_{offset}'] = np.array([0], dtype=np.int32)
    name = f'reference_pathway_0_queue_0_slot_{(offset + 1) % 19}'
    arrays[name] = np.array([2, 1], dtype=np.int32)
    arrays[f'reference_pathway_0_queue_0_slot_{(offset + 18) % 19}'] = np.array(
        [3], dtype=np.int32
    )
    if fault == 'future':
        queue[steps % 19, 0, 0] = True
    if fault == 'cleared':
        queue[(steps - 1) % 19, 0, 0] = True
    if fault == 'dtype':
        arrays[name] = arrays[name].astype(np.int64)
    if fault == 'duplicate':
        arrays[name] = np.array([2, 1, 1], dtype=np.int32)
    if fault == 'bounds':
        arrays[name] = np.array([2, 4], dtype=np.int32)
    if fault == 'geometry':
        queue = queue[:, :, :-1]
    if fault == 'mapping':
        sources[2] = 0
    with (tmp_path / 'reference-final-physical.npz').open('xb') as archive:
        np.savez_compressed(archive, **arrays)
    with (tmp_path / 'mlx-native.npz').open('xb') as archive:
        np.savez_compressed(archive, queue=queue)
    if fault != 'none':
        with pytest.raises(ValueError):
            verify(tmp_path, steps, sources, 3)
        return
    assert verify(tmp_path, steps, sources, 3) == (2,) + (0,) * 16 + (1,)
