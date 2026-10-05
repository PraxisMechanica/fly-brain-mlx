import hashlib
import json
import zipfile
from dataclasses import asdict
from pathlib import Path

import pytest

from fly_brain.qualification.adapters.case_binding import require_cause_binding
from fly_brain.qualification.causality import CausalAudit
from fly_brain.qualification.models import ParityCase

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault',
    (
        'none',
        'pending',
        'unexplained',
        'trial',
        'neuron',
        'missing_proof',
        'review_changed',
        'execution_changed',
        'manifest_incomplete',
        'archive_incomplete',
        'launch',
        'budget',
        'threshold',
    ),
)
def test_completed_cause_cannot_apply_to_changed_or_incomplete_evidence(
    tmp_path: Path, fault: str
) -> None:
    run, review = tmp_path / 'run', tmp_path / 'review'
    run.mkdir()
    review.mkdir()
    paired = run / 'observations/paired-first'
    paired.mkdir(parents=True)
    names = [
        'environment.json',
        'reference-job.json',
        'stimulus.json',
        'stimulus.npz',
        *(
            f'observations/paired-first/{name}'
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
        ),
    ]
    for name in names:
        (run / name).write_bytes(('actual ' + name).encode())
    manifest = {
        name: hashlib.sha256((run / name).read_bytes()).hexdigest() for name in names
    }
    preflight = {
        'launch_checkpoint': 'launch' if fault != 'launch' else 'wrong',
        'first_spike_step': 5719,
        'first_spike_neurons': [100750],
        'no_first_budget_violation_reported': fault != 'budget',
        'threshold_prerequisites_pass': fault != 'threshold',
        'case_accepted': False,
        'artifact_sha256': manifest.copy(),
    }
    if fault == 'manifest_incomplete':
        preflight['artifact_sha256'] = {
            name: digest
            for name, digest in manifest.items()
            if 'physical-digests' not in name
        }
    (review / 'first-cause-preflight.json').write_text(json.dumps(preflight))
    with zipfile.ZipFile(review / 'first-observation.zip', 'x') as archive:
        for name in names:
            if fault != 'archive_incomplete' or 'spike-context' not in name:
                archive.write(run / name, name)
    for name in (
        'astra-review.md',
        'executed-preflight.py',
        'parent-host-proof.json',
        'executed-host-proof.py',
        'dispatch.json',
    ):
        (review / name).write_text('completed bound evidence ' + name)
    case = ParityCase('sugar', 10000, 0)
    identity = {
        **asdict(case),
        'first_spike_step': 5719,
        'first_spike_neurons': [100750],
    }
    if fault == 'trial':
        identity['trial'] = 1
    elif fault == 'neuron':
        identity['first_spike_neurons'] = [7]
    bound = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in review.iterdir()
    }
    if fault == 'missing_proof':
        bound.pop('executed-host-proof.py')
    decision = {
        'review_complete': fault != 'pending',
        'case_accepted': False,
        'classification': 'Explained finite-precision trajectory roundoff under the existing policy.'
        if fault != 'unexplained'
        else 'Unresolved',
        'case_identity': identity,
        'bound_artifact_sha256': bound,
    }
    (review / 'review-decision.json').write_text(json.dumps(decision))
    if fault == 'review_changed':
        (review / 'astra-review.md').write_text('changed review')
    elif fault == 'execution_changed':
        (paired / 'spike-context.npz').write_bytes(b'changed cause')
    audit = CausalAudit()
    audit.step, audit.first_spike_step, audit.first_spike_neurons = (
        10000,
        5719,
        (100750,),
    )
    if fault == 'none':
        hashes = require_cause_binding(run, review, case, audit, 'launch')
        assert set(hashes) == {*bound, 'review-decision.json'}
    else:
        with pytest.raises(ValueError):
            require_cause_binding(run, review, case, audit, 'launch')
