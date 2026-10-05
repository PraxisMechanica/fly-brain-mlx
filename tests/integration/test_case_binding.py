import hashlib
from pathlib import Path

import pytest

from fly_brain.qualification.adapters.case_binding import require_bound_files

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault',
    (
        'none',
        'changed',
        'required_missing',
        'context_missing',
        'manifest_missing',
        'manifest_extra',
    ),
)
def test_review_binding_refuses_stale_or_incomplete_original_evidence(
    tmp_path: Path, fault: str
) -> None:
    names = [
        'case.json',
        'normalized-spikes.npz',
        'environment.json',
        'stimulus.json',
        'stimulus.npz',
        'reference-job.json',
    ]
    for mode in ('first', 'repeat'):
        names.extend(
            f'observations/paired-{mode}/{name}'
            for name in (
                'phase-digests.jsonl',
                'physical-digests.jsonl',
                'causal.json',
                'reference-final-physical.json',
                'reference-native.npz',
                'mlx-native.npz',
                'reference-final-physical.npz',
                'spike-context.npz',
            )
        )
        names.extend(
            f'observations/cpu-{mode}/{name}'
            for name in ('native-digests.jsonl', 'native.npz')
        )
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'original fixture bytes')
    manifest = {
        name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in names
    }
    if fault == 'none':
        require_bound_files(tmp_path, manifest, has_spike_context=True)
        return
    if fault == 'changed':
        (tmp_path / 'case.json').write_bytes(b'changed report')
    elif fault in ('required_missing', 'context_missing'):
        name = (
            'case.json'
            if fault == 'required_missing'
            else 'observations/paired-repeat/spike-context.npz'
        )
        (tmp_path / name).rename(tmp_path / 'retained-missing-file.bin')
        manifest.pop(name)
    elif fault == 'manifest_missing':
        manifest.pop('case.json')
    else:
        manifest['unknown.json'] = '0' * 64
    with pytest.raises(ValueError):
        require_bound_files(tmp_path, manifest, has_spike_context=True)
