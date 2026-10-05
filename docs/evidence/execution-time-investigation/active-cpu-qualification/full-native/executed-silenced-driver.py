import base64
import csv
import hashlib
import json
import signal
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.active_cpu import ActiveSources, step
from fly_brain.qualification.adapters.torch_collect import collect
from fly_brain.qualification.adapters.torch_setup import native_float, prepare, tensor
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate, neuron_indices

root = Path('/Users/ocasta/Code/fly-brain')
output = root / 'data/results/performance-remediation-active-cpu-silenced-20261005'
output.mkdir(exist_ok=False)
signal.alarm(900)
torch.set_num_threads(1)
started = time.perf_counter()
connectome, pin = pinned_inputs(root)
lock = (root / 'uv.lock').read_bytes()
assert lock == subprocess.check_output(['git', 'show', '55ea35f:uv.lock'], cwd=root)
site = root / '.venv/lib/python3.10/site-packages'
verified = 0
native_hashes = {}
with (site / 'torch-2.11.0.dist-info/RECORD').open(newline='') as stream:
    for name, digest, size in csv.reader(stream):
        if digest:
            algorithm, encoded = digest.split('=', 1)
            assert algorithm == 'sha256'
            path = site / name
            actual = hashlib.sha256(path.read_bytes()).digest()
            assert base64.urlsafe_b64encode(actual).rstrip(b'=').decode() == encoded, name
            verified += 1
            if name.startswith('torch/lib/') and path.suffix in ('.so', '.dylib'):
                native_hashes[name] = actual.hex()
record = {'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'lock_sha256': hashlib.sha256(lock).hexdigest(), 'torch_record_entries_verified': verified, 'current_native_binary_sha256': native_hashes, 'torch_build': torch.__config__.show(), 'torch_git_version': torch.version.git_version, 'cpu_threads': torch.get_num_threads(), 'cpu_interop_threads': torch.get_num_interop_threads(), 'historical_identity': 'Derived from identical retained locked artifact/install chain; original environment did not measure native binary hashes.', 'cases': {}}
for name, steps, original in (
    ('sugar-silenced', 1000, root / 'data/results/milestone-4-parity-sugar-silenced-1000-0-20261005-01'),
):
    experiment = EXPERIMENTS[name]
    stimulus = generate(connectome, experiment, steps, (0,))
    metadata = json.loads((original / 'stimulus.json').read_text())
    assert stimulus.sha256 == metadata['canonical_event_sha256']
    assert list(stimulus.targets) == metadata['targets']
    assert metadata['input_sha256'] == {'completeness': pin.completeness_sha256, 'connectivity': pin.connectivity_sha256}
    model = prepare(connectome, stimulus.targets, neuron_indices(connectome, experiment.silenced_ids), 1)
    candidate = step(model)
    case_output = output / name
    case_output.mkdir()
    samples = []
    for mode in ('first', 'repeat'):
        print(json.dumps({'phase': 'running', 'case': name, 'mode': mode, 'elapsed_s': time.perf_counter() - started}), flush=True)
        began = time.perf_counter()
        collect(model, stimulus, case_output / mode, candidate)
        elapsed = time.perf_counter() - began
        expected = original / 'observations' / ('cpu-' + mode)
        actual = case_output / mode
        assert (actual / 'native-digests.jsonl').read_bytes() == (expected / 'native-digests.jsonl').read_bytes()
        with np.load(actual / 'native.npz', allow_pickle=False) as a, np.load(expected / 'native.npz', allow_pickle=False) as b:
            assert a.files == b.files
            for field in a.files:
                assert (a[field].dtype, a[field].shape, a[field].tobytes()) == (b[field].dtype, b[field].shape, b[field].tobytes()), field
        snapshots = [json.loads(line) for line in (actual / 'native-digests.jsonl').read_text().splitlines()]
        assert [s['step'] for s in snapshots] == list(range(-1, steps))
        samples.append({'mode': mode, 'elapsed_s': elapsed, 'native_snapshots': len(snapshots), 'all_digests_raster_and_final_bytes_match': True, 'artifact_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in actual.iterdir()}})
        print(json.dumps({'phase': 'verified', 'case': name, **samples[-1]}), flush=True)
    record['cases'][name] = {'steps': steps, 'trial': 0, 'event_sha256': stimulus.sha256, 'original': str(original), 'runs': samples}
    (output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
record['elapsed_s'] = time.perf_counter() - started
record['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
record['source_sha256'] = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / 'src/fly_brain/qualification/adapters').glob('*.py') if p.stem in ('active_cpu', 'torch_reference', 'torch_setup', 'torch_observer', 'torch_collect', 'paired_observer')}
(output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
signal.alarm(0)
print(json.dumps({'completed': True, 'elapsed_s': record['elapsed_s'], 'output': str(output)}), flush=True)
