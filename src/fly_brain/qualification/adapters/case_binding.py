import hashlib
import json
import zipfile
from collections.abc import Mapping
from pathlib import Path

from ..adjudication import require_same_cause
from ..causality import CausalAudit
from ..models import ParityCase


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


def require_cause_binding(
    run: Path, review: Path, case: ParityCase, audit: CausalAudit, launch: str
) -> dict[str, str]:
    decision_path = review / 'review-decision.json'
    decision = json.loads(decision_path.read_text())
    if (
        decision['review_complete'] is not True
        or decision['case_accepted'] is not False
        or decision['classification']
        != 'Explained finite-precision trajectory roundoff under the existing policy.'
    ):
        raise ValueError('Cause binding requires a completed explained-roundoff review')
    identity = decision['case_identity']
    require_same_cause(
        case,
        audit,
        ParityCase(identity['experiment'], identity['steps'], identity['trial']),
        identity['first_spike_step'],
        tuple(identity['first_spike_neurons']),
    )
    bound = decision['bound_artifact_sha256']
    required = {
        'astra-review.md',
        'first-cause-preflight.json',
        'first-observation.zip',
        'executed-preflight.py',
        'parent-host-proof.json',
        'executed-host-proof.py',
        'dispatch.json',
    }
    if set(bound) != required:
        raise ValueError('Cause binding requires every completed review artifact')
    for name, digest in bound.items():
        if hashlib.sha256((review / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Bound review artifact changed: {name}')
    preflight = json.loads((review / 'first-cause-preflight.json').read_text())
    if (
        preflight['launch_checkpoint'] != launch
        or preflight['first_spike_step'] != audit.first_spike_step
        or tuple(preflight['first_spike_neurons']) != audit.first_spike_neurons
        or preflight['no_first_budget_violation_reported'] is not True
        or preflight['threshold_prerequisites_pass'] is not True
        or preflight['case_accepted'] is not False
    ):
        raise ValueError('Cause preflight must bind this execution and native cause')
    manifest = preflight['artifact_sha256']
    first = run / 'observations' / 'paired-first'
    required_first = {
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
    }
    actual = required_first | {
        str(path.relative_to(run))
        for path in first.iterdir()
        if path.suffix in ('.json', '.jsonl', '.npz')
    }
    if set(manifest) != actual or any(not (run / name).is_file() for name in actual):
        raise ValueError('Cause binding requires the complete actual first observation')
    for name, digest in manifest.items():
        if hashlib.sha256((run / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Reviewed execution artifact changed: {name}')
    with zipfile.ZipFile(review / 'first-observation.zip') as archive:
        if (
            len(archive.namelist()) != len(manifest)
            or set(archive.namelist()) != set(manifest)
            or any(
                hashlib.sha256(archive.read(name)).hexdigest() != digest
                for name, digest in manifest.items()
            )
        ):
            raise ValueError('Reviewed archive must contain every bound original byte')
    return {
        'review-decision.json': hashlib.sha256(decision_path.read_bytes()).hexdigest(),
        **bound,
    }
