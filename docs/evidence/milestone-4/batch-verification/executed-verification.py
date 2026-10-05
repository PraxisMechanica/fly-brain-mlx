import hashlib
import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def sha(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    return json.loads(path.read_text())


root = Path.cwd()
output = Path(sys.argv[1]).resolve()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
base = root / 'docs/evidence/milestone-4'
batch_path = base / 'four-trial-memory/four-trial-memory.json'
batch = read(batch_path)
assert batch['steps'] == 1000 and batch['trial_indices'] == [0, 1, 2, 3]
assert [(row['begin'], row['rows']) for row in batch['blocks']] == [
    (begin, min(32, 1000 - begin)) for begin in range(0, 1000, 32)
]
connectome, pin = pinned_inputs(root)
assert (batch['neurons'], batch['edges']) == (pin.neurons, pin.edges)
stimulus = generate(connectome, EXPERIMENTS['sugar'], 1000, (0, 1, 2, 3))
with np.load(base / 'four-trial-memory/stimulus.npz', allow_pickle=False) as saved:
    assert saved['events'].dtype == np.uint8
    assert saved['events'].tobytes() == stimulus.events.tobytes()
    assert np.array_equal(saved['targets'], stimulus.targets)
assert batch['stimulus_sha256'] == stimulus.sha256
sources = {
    str(path.relative_to(root)): sha(path.read_bytes())
    for path in (
        batch_path,
        base / 'four-trial-memory/batch-final.npz',
        base / 'four-trial-memory/stimulus.npz',
    )
}
trials = []
with np.load(base / 'four-trial-memory/batch-final.npz', allow_pickle=False) as many:
    batch_queue = many['queue']
    assert batch_queue.dtype == np.bool_ and batch_queue.shape == (19, 4, pin.edges)
    for trial in range(4):
        if trial == 0:
            folder = base / 'full-paired-observer'
            solo = read(folder / 'observed.json')['blocks']
            final_path = folder / 'observed-mlx-final.npz'
            payload = final_path.read_bytes()
            evidence = (folder / 'observed.json', final_path)
        else:
            folder = base / f'cases/sugar-1000-{trial}'
            archive_path = folder / 'observations.zip'
            verification = read(folder / 'verification.json')
            with zipfile.ZipFile(archive_path) as archive:
                phases_name = 'observations/paired-first/phase-digests.jsonl'
                final_name = 'observations/paired-first/mlx-native.npz'
                assert (
                    sha(archive.read(phases_name))
                    == verification['archive_manifest_sha256'][phases_name]
                )
                payload = archive.read(final_name)
                assert (
                    sha(payload) == verification['archive_manifest_sha256'][final_name]
                )
                solo = [
                    json.loads(line) for line in archive.read(phases_name).splitlines()
                ]
            evidence = (archive_path, folder / 'verification.json')
        assert len(solo) == len(batch['blocks']) == 32
        for actual, independent in zip(batch['blocks'], solo, strict=True):
            assert (actual['begin'], actual['rows']) == (
                independent['begin'],
                independent['rows'],
            )
            digest = (
                independent['mlx_native_phase_sha256']
                if trial == 0
                else independent['native_phase_sha256'][1]
            )
            assert actual['native_phase_sha256'][trial][1] == digest
            assert (
                actual['actual_queue_sha256'][trial]
                == independent['mlx_queue_sha256'][0]
            )
            assert [row[trial] for row in actual['actual_due_sha256']] == [
                row[0] for row in independent['mlx_due_sha256']
            ]
        with np.load(io.BytesIO(payload), allow_pickle=False) as one:
            for name in many.files:
                expected = one[name]
                if name == 'queue':
                    assert expected.dtype == batch_queue.dtype
                    assert expected.shape == (19, 1, pin.edges)
                    assert np.array_equal(batch_queue[:, trial], expected[:, 0])
                else:
                    actual = many[name][trial]
                    assert (actual.dtype, actual.shape, actual.tobytes()) == (
                        expected.dtype,
                        expected.shape,
                        expected.tobytes(),
                    ), (trial, name)
        assert batch['trial_stimulus_sha256'][trial] == sha(
            generate(connectome, EXPERIMENTS['sugar'], 1000, (trial,)).events.tobytes()
        )
        for path in evidence:
            sources[str(path.relative_to(root))] = sha(path.read_bytes())
        trials.append(
            {
                'trial': trial,
                'all_32_phase_queue_due_blocks_exact': True,
                'all_13_actual_final_fields_exact': True,
            }
        )
output.mkdir(parents=True, exist_ok=False)
shutil.copyfile(__file__, output / 'executed-verification.py')
record = {
    'checkpoint': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True
    ).strip(),
    'executed_program_sha256': sha(Path(__file__).read_bytes()),
    'steps': 1000,
    'trials': trials,
    'input_pins': {'neurons': pin.neurons, 'edges': pin.edges},
    'artifact_sha256': sources,
    'one_second_batch_gate_accepted': False,
    'batch_repeat_verified': False,
    'cpu_batch_verified': False,
    'new_case_execution_or_acceptance': False,
    'scope': 'Verify the completed Astra method against retained actual 0.1-second MLX batch and four singleton native observations. No one-second, batch-repeat, CPU-batch, or matrix acceptance.',
}
with (output / 'parent-verification.json').open('x') as target:
    json.dump(record, target, indent=2, allow_nan=False)
print(json.dumps({'verified': True, 'trials': len(trials), 'steps': 1000}), flush=True)
