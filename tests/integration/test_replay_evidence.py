from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.replay_evidence import cpu

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault', ('none', 'digest', 'field', 'dtype', 'shape', 'zero', 'missing')
)
def test_saved_replay_requires_complete_native_arrays_and_exact_digest_coverage(
    tmp_path: Path, fault: str
) -> None:
    first, repeat = tmp_path / 'first', tmp_path / 'repeat'
    for output in (first, repeat):
        output.mkdir()
        (output / 'native-digests.jsonl').write_text('initial\nstep 0\nstep 1\n')
        with (output / 'native.npz').open('xb') as archive:
            np.savez_compressed(archive, v=np.array([-0.0, 1], dtype=np.float32))
    if fault == 'none':
        cpu(first, repeat)
        return
    if fault in ('digest', 'missing'):
        (repeat / 'native-digests.jsonl').write_text(
            'initial\nstep 0\n' if fault == 'missing' else 'initial\nchanged\nstep 1\n'
        )
    else:
        values = np.array([-0.0, 1], dtype=np.float32)
        if fault == 'dtype':
            values = values.astype(np.float64)
        if fault == 'shape':
            values = values.reshape(2, 1)
        if fault == 'zero':
            values[0] = 0.0
        with (repeat / 'native.npz').open('wb') as archive:
            np.savez_compressed(archive, **{'g' if fault == 'field' else 'v': values})
    with pytest.raises(ValueError, match='Repeat'):
        cpu(first, repeat)
