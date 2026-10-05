import json
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.case_replay import require_complete_replay

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault',
    (
        'none',
        'paired_tail',
        'cpu_initial',
        'physical_final',
        'due',
        'phase',
        'queue',
        'causal',
    ),
)
def test_identical_repeats_cannot_hide_incomplete_case_observation(
    tmp_path: Path, fault: str
) -> None:
    steps = 35
    for mode in ('first', 'repeat'):
        pair, cpu = (
            tmp_path / 'observations' / f'{name}-{mode}' for name in ('paired', 'cpu')
        )
        pair.mkdir(parents=True)
        cpu.mkdir(parents=True)
        phases = [
            {
                'begin': begin,
                'rows': min(32, steps - begin),
                'native_phase_sha256': ['0' * 64] * 2,
                'mlx_queue_sha256': ['0' * 64],
                'mlx_due_sha256': [['0' * 64] for _ in range(min(32, steps - begin))],
            }
            for begin in (0, 32)
        ]
        physical = [{'step': step, 'sha256': '0' * 64} for step in range(steps + 1)]
        native = [
            {'step': step, 'native_sha256': ['0' * 64]} for step in range(-1, steps)
        ]
        causal = {'steps': steps, 'contexts': {'budget': None, 'spike': None}}
        if fault == 'paired_tail':
            phases.pop()
        if fault == 'cpu_initial':
            native.pop(0)
        if fault == 'physical_final':
            physical.pop()
        if fault == 'due':
            phases[0]['mlx_due_sha256'] = []
        if fault == 'phase':
            phases[0]['native_phase_sha256'] = ['0' * 64]
        if fault == 'queue':
            phases[0]['mlx_queue_sha256'] = []
        if fault == 'causal':
            causal['steps'] = 34
        for path, rows in (
            (pair / 'phase-digests.jsonl', phases),
            (pair / 'physical-digests.jsonl', physical),
            (cpu / 'native-digests.jsonl', native),
        ):
            path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        (pair / 'causal.json').write_text(json.dumps(causal))
        (pair / 'reference-final-physical.json').write_text('{}')
        for output, names in (
            (
                pair,
                (
                    'reference-native.npz',
                    'mlx-native.npz',
                    'reference-final-physical.npz',
                ),
            ),
            (cpu, ('native.npz',)),
        ):
            for name in names:
                with (output / name).open('xb') as archive:
                    np.savez_compressed(archive, v=np.array([1], dtype=np.float32))
    if fault == 'none':
        require_complete_replay(tmp_path, steps)
    else:
        with pytest.raises(ValueError, match='requires|cover'):
            require_complete_replay(tmp_path, steps)
