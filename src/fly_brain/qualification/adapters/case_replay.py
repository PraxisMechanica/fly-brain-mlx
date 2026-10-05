import json
import re
from pathlib import Path

from .replay_evidence import cpu, paired


def require_complete_replay(run: Path, steps: int) -> None:
    if steps < 1:
        raise ValueError('Case replay requires a positive complete horizon')
    observations = run / 'observations'
    paired(observations / 'paired-first', observations / 'paired-repeat')
    cpu(observations / 'cpu-first', observations / 'cpu-repeat')
    expected = [(begin, min(32, steps - begin)) for begin in range(0, steps, 32)]
    for mode in ('first', 'repeat'):
        pair = observations / f'paired-{mode}'
        phases = [
            json.loads(line)
            for line in (pair / 'phase-digests.jsonl').read_text().splitlines()
        ]
        if [(row['begin'], row['rows']) for row in phases] != expected or any(
            len(row['native_phase_sha256']) != 2
            or len(row['mlx_queue_sha256']) != 1
            or len(row['mlx_due_sha256']) != row['rows']
            or any(len(due) != 1 for due in row['mlx_due_sha256'])
            or any(
                re.fullmatch('[0-9a-f]{64}', digest) is None
                for digest in (
                    *row['native_phase_sha256'],
                    *row['mlx_queue_sha256'],
                    *(due[0] for due in row['mlx_due_sha256']),
                )
            )
            for row in phases
        ):
            raise ValueError(
                'Paired replay requires complete native phase, queue and due coverage'
            )
        physical = [
            json.loads(line)
            for line in (pair / 'physical-digests.jsonl').read_text().splitlines()
        ]
        if [row['step'] for row in physical] != list(range(steps + 1)) or any(
            re.fullmatch('[0-9a-f]{64}', row['sha256']) is None for row in physical
        ):
            raise ValueError(
                'Reference replay requires every actual physical queue step'
            )
        causal = json.loads((pair / 'causal.json').read_text())
        if causal['steps'] != steps:
            raise ValueError('Causal replay must cover the complete case')
        native = [
            json.loads(line)
            for line in (observations / f'cpu-{mode}' / 'native-digests.jsonl')
            .read_text()
            .splitlines()
        ]
        if [row['step'] for row in native] != list(range(-1, steps)) or any(
            len(row['native_sha256']) != 1
            or re.fullmatch('[0-9a-f]{64}', row['native_sha256'][0]) is None
            for row in native
        ):
            raise ValueError('CPU replay requires its initial and every native state')
