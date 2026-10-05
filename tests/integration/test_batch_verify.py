import json
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.batch_native import Engine
from fly_brain.qualification.adapters.batch_verify import compare
from fly_brain.qualification.batch_evidence import NativeDifference, PhaseDifference
from tests.unit.test_batch_native import native

pytestmark = pytest.mark.integration


@pytest.mark.parametrize('engine', ('mlx', 'cpu'))
def test_saved_batch_comparison_covers_actual_trial_shapes_and_streams(
    engine: Engine,
    tmp_path: Path,
) -> None:
    batch = tmp_path / 'batch'
    singletons = {trial: tmp_path / f'single-{trial}' for trial in range(4)}
    hashes = tuple(str(trial + 1) * 64 for trial in range(4))
    stream = 'phase-digests.jsonl' if engine == 'mlx' else 'native-digests.jsonl'
    many = native(engine, 4)
    many['spike_trials'] = np.arange(4, dtype=np.int64)
    many['spike_neurons'] = np.arange(4, dtype=np.int64)
    many['spike_steps'] = np.full(4, 32, dtype=np.int64)
    for path, trial in (
        (batch, None),
        *((path, trial) for trial, path in singletons.items()),
    ):
        path.mkdir()
        arrays = many if trial is None else native(engine, 1)
        if trial is not None:
            arrays['spike_neurons'] = np.array([trial], dtype=np.int64)
            arrays['spike_steps'] = np.array([32], dtype=np.int64)
            if engine == 'cpu':
                arrays['spike_trials'] = np.array([0], dtype=np.int64)
        filename = (
            'mlx-native.npz' if engine == 'mlx' and trial is not None else 'native.npz'
        )
        with (path / filename).open('xb') as artifact:
            np.savez_compressed(artifact, **arrays)
        selected = hashes if trial is None else (hashes[trial],)
        if engine == 'mlx':
            rows = [
                {
                    'begin': begin,
                    'rows': min(32, 35 - begin),
                    'native_phase_sha256': selected
                    if trial is None
                    else ('f' * 64, *selected),
                    'mlx_queue_sha256': selected,
                    'mlx_due_sha256': [selected] * min(32, 35 - begin),
                }
                for begin in (0, 32)
            ]
        else:
            rows = [{'step': step, 'native_sha256': selected} for step in range(-1, 35)]
        (path / stream).write_text(''.join(json.dumps(row) + '\n' for row in rows))
    assert compare(batch, singletons, engine, 35, 6, 3, 2) == (
        None,
        {trial: () for trial in range(4)},
    )
    path = batch / stream
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    key = 'native_phase_sha256' if engine == 'mlx' else 'native_sha256'
    rows[-1][key][3] = 'f' * 64
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
    unresolved = (
        PhaseDifference(3, 32, 3, 'native')
        if engine == 'mlx'
        else NativeDifference(3, 34)
    )
    assert compare(batch, singletons, engine, 35, 6, 3, 2)[0] == unresolved
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows[:-1]))
    with pytest.raises(ValueError, match='every prescribed block|initial and every'):
        compare(batch, singletons, engine, 35, 6, 3, 2)
