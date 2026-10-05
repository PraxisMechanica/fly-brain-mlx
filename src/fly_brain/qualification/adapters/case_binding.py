import hashlib
from collections.abc import Mapping
from pathlib import Path


def scientific_files(run: Path) -> tuple[Path, ...]:
    observations = run / 'observations'
    return tuple(
        sorted(
            set(run.glob('*.json'))
            | set(run.glob('*.npz'))
            | set(observations.rglob('*.json'))
            | set(observations.rglob('*.jsonl'))
            | set(observations.rglob('*.npz'))
        )
    )


def require_bound_files(
    run: Path, manifest: Mapping[str, str], *, has_spike_context: bool
) -> None:
    required = {
        'case.json',
        'normalized-spikes.npz',
        'environment.json',
        'stimulus.json',
        'stimulus.npz',
        'reference-job.json',
    }
    for mode in ('first', 'repeat'):
        required.update(
            f'observations/paired-{mode}/{name}'
            for name in (
                'phase-digests.jsonl',
                'physical-digests.jsonl',
                'causal.json',
                'reference-final-physical.json',
                'reference-native.npz',
                'mlx-native.npz',
                'reference-final-physical.npz',
                *(('spike-context.npz',) if has_spike_context else ()),
            )
        )
        required.update(
            f'observations/cpu-{mode}/{name}'
            for name in ('native-digests.jsonl', 'native.npz')
        )
    actual = {str(path.relative_to(run)) for path in scientific_files(run)}
    if not required <= actual or set(manifest) != actual:
        raise ValueError('Case binding requires every original scientific artifact')
    for name, digest in manifest.items():
        if hashlib.sha256((run / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Bound case artifact changed: {name}')
