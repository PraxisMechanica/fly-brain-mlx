import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from fly_brain.qualification.batch_evidence import PhaseDigest, phase_difference

root = Path.cwd()
base = root / 'docs/evidence/milestone-4'
output = Path(sys.argv[1]).resolve()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
proof_path = base / 'batch-verification/parent-verification.json'
proof = json.loads(proof_path.read_text())
for name, digest in proof['artifact_sha256'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
batch = json.loads((base / 'four-trial-memory/four-trial-memory.json').read_text())
many = tuple(
    PhaseDigest(
        row['begin'],
        row['rows'],
        tuple(trial[1] for trial in row['native_phase_sha256']),
        tuple(row['actual_queue_sha256']),
        tuple(tuple(values) for values in row['actual_due_sha256']),
    )
    for row in batch['blocks']
)
singletons = {}
for trial in range(4):
    if trial == 0:
        saved = json.loads((base / 'full-paired-observer/observed.json').read_text())[
            'blocks'
        ]
    else:
        with zipfile.ZipFile(
            base / f'cases/sugar-1000-{trial}/observations.zip'
        ) as archive:
            saved = [
                json.loads(line)
                for line in archive.read(
                    'observations/paired-first/phase-digests.jsonl'
                ).splitlines()
            ]
    singletons[trial] = tuple(
        PhaseDigest(
            row['begin'],
            row['rows'],
            (
                row['mlx_native_phase_sha256']
                if trial == 0
                else row['native_phase_sha256'][1],
            ),
            tuple(row['mlx_queue_sha256']),
            tuple(tuple(values) for values in row['mlx_due_sha256']),
        )
        for row in saved
    )
assert phase_difference(many, singletons, 1000) is None
output.mkdir(parents=True, exist_ok=False)
shutil.copyfile(__file__, output / 'executed-verification.py')
record = {
    'checkpoint': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True
    ).strip(),
    'executed_program_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'phase_rule_source_sha256': hashlib.sha256(
        (root / 'src/fly_brain/qualification/batch_evidence.py').read_bytes()
    ).hexdigest(),
    'bound_parent_proof_sha256': hashlib.sha256(proof_path.read_bytes()).hexdigest(),
    'all_original_artifact_hashes_revalidated': True,
    'actual_four_trial_native_queue_and_due_blocks_exact': True,
    'steps': 1000,
    'blocks_per_trial': 32,
    'trials': [0, 1, 2, 3],
    'new_case_execution_or_acceptance': False,
    'one_second_batch_gate_accepted': False,
    'scope': 'Regression of the committed pure phase rules on the already verified retained actual short MLX batch and singleton observations. Other batch requirements remain open.',
}
with (output / 'actual-phase-control.json').open('x') as target:
    json.dump(record, target, indent=2, allow_nan=False)
print(json.dumps({'verified': True, 'steps': 1000, 'trials': 4}), flush=True)
