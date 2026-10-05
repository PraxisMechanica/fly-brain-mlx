import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
import torch

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.paired_observer import phase_hash
from fly_brain.qualification.adapters.torch_observer import observe
from fly_brain.qualification.adapters.torch_setup import native_float, prepare, replay_inputs
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def raw(array):
    return {'dtype': array.dtype.str, 'shape': list(array.shape), 'sha256': hashlib.sha256(array.tobytes(order='C')).hexdigest()}


def write_json(path, value):
    with path.open('x') as artifact:
        json.dump(value, artifact, indent=2)
        artifact.write('\n')


root = Path.cwd()
checkpoint = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
assert importlib.metadata.version('torch') == '2.11.0'
assert np.__version__ == '1.26.4' and torch.get_default_dtype() == torch.float32
torch.set_num_threads(1)
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
started = time.perf_counter()
connectome, pin = pinned_inputs(root)
stimulus = generate(connectome, EXPERIMENTS['sugar'], 1000, (0,))
assert stimulus.sha256 == 'd7bb792f082eeca79d6e88a1e8ca0791dca210eb15c86ec70a34348b272a82b3'
with (output / 'stimulus.npz').open('xb') as artifact:
    np.savez_compressed(artifact, events=stimulus.events, targets=np.asarray(stimulus.targets, dtype=np.int32))
model = prepare(connectome, stimulus.targets, (), 1)
assert model.weights.device.type == 'cpu' and model.weights.layout == torch.sparse_csr
names = ('g', 'delay_buffer', 'spikes', 'v', 'refrac')
metadata = {
    'checkpoint': checkpoint, 'command': sys.argv, 'python': sys.version,
    'platform': platform.platform(), 'device': 'cpu', 'default_dtype': str(torch.get_default_dtype()),
    'torch': importlib.metadata.version('torch'), 'numpy': np.__version__,
    'threads': torch.get_num_threads(), 'interop_threads': torch.get_num_interop_threads(),
    'deterministic_algorithms_enabled': torch.are_deterministic_algorithms_enabled(),
    'weights_layout': str(model.weights.layout), 'neurons': pin.neurons, 'edges': pin.edges,
    'stimulus_sha256': stimulus.sha256, 'stimulus_events': int(stimulus.events.sum()),
    'steps': 1000, 'trials': [0], 'setup_decision_confidence_percent': 99,
    'sources': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (
        root / 'src/fly_brain/qualification/adapters/torch_reference.py',
        root / 'src/fly_brain/qualification/adapters/torch_setup.py',
        root / 'src/fly_brain/qualification/adapters/torch_observer.py',
        root / 'src/fly_brain/qualification/adapters/paired_observer.py',
        root / 'src/fly_brain/simulation/stimuli.py',
    )},
}
write_json(output / 'environment.json', metadata)
samples, sample_errors, mode = [], [], 'setup'
done = threading.Event()


def sample_memory():
    try:
        with (output / 'memory-samples.jsonl').open('x') as artifact:
            while not done.is_set():
                rss = int(subprocess.check_output(['ps', '-o', 'rss=', '-p', str(os.getpid())], text=True)) * 1024
                value = {'elapsed_s': time.perf_counter() - started, 'mode': mode, 'pid': os.getpid(), 'process_rss_bytes': rss}
                samples.append(value)
                artifact.write(json.dumps(value) + '\n')
                artifact.flush()
                done.wait(0.25)
    except BaseException as error:
        sample_errors.append(repr(error))


def ordinary():
    with torch.no_grad():
        state = model.state_init()
    yield -1, {name: native_float(value) for name, value in zip(names, state, strict=True)}
    for step in range(1000):
        counts = replay_inputs(stimulus.events[:, step], stimulus.targets, pin.neurons)
        with torch.no_grad():
            state = model.forward(counts, *state)
        yield step, {name: native_float(value) for name, value in zip(names, state, strict=True)}


records = {}
sampler = threading.Thread(target=sample_memory, daemon=True)
sampler.start()
try:
    for mode in ('ordinary', 'observed', 'repeat'):
        beginning = time.perf_counter()
        frames = ordinary() if mode == 'ordinary' else (
            (snapshot.step, snapshot.fields) for snapshot in observe(model, stimulus.events, stimulus.targets)
        )
        digests, spike_steps, spike_neurons, final = [], [], [], None
        print(json.dumps({'phase': 'executing', 'mode': mode}), flush=True)
        for step, fields in frames:
            assert step == len(digests) - 1
            assert all(value.dtype == np.float32 and np.isfinite(value).all() for value in fields.values())
            assert fields['delay_buffer'].shape == (1, 19, pin.neurons)
            assert all(value.shape == (1, pin.neurons) for name, value in fields.items() if name != 'delay_buffer')
            spikes, refractory = fields['spikes'], fields['refrac']
            assert np.all((spikes == 0) | (spikes == 1))
            assert np.all(refractory >= 0) and np.array_equal(refractory, np.floor(refractory))
            digests.append({'step': step, 'native_five_tensor_sha256': phase_hash(fields)})
            if step >= 0:
                trials, neurons = np.nonzero(spikes)
                assert not trials.any()
                spike_steps.extend([step] * len(neurons))
                spike_neurons.extend(neurons.tolist())
            final = fields
            if step in (0, 255, 511, 767, 999):
                print(json.dumps({'phase': 'progress', 'mode': mode, 'step': step, 'seconds': time.perf_counter() - beginning}), flush=True)
        elapsed_s = time.perf_counter() - beginning
        assert len(digests) == 1001 and final is not None
        arrays = {name: value.copy() for name, value in final.items()}
        arrays['spike_steps'] = np.asarray(spike_steps, dtype=np.int64)
        arrays['spike_neurons'] = np.asarray(spike_neurons, dtype=np.int64)
        with (output / (mode + '-final.npz')).open('xb') as artifact:
            np.savez_compressed(artifact, **arrays)
        write_json(output / (mode + '-digests.json'), digests)
        records[mode] = {'execution_and_capture_s': elapsed_s, 'spikes': len(spike_steps), 'active_neurons': len(set(spike_neurons)), 'observations': len(digests), 'final': {name: raw(value) for name, value in arrays.items()}}
        if mode == 'ordinary':
            baseline_digests, baseline_final = digests, records[mode]['final']
        else:
            assert digests == baseline_digests and records[mode]['final'] == baseline_final
finally:
    done.set()
    sampler.join(5)
assert not sampler.is_alive() and not sample_errors and samples
report = {
    'checkpoint': checkpoint, 'environment': 'environment.json', 'modes': records,
    'all_five_actual_state_tensors_and_physical_buffers_ordinary_observed_repeat_byte_identical': True,
    'memory': {'sampled_process_rss_peak_bytes': max(row['process_rss_bytes'] for row in samples), 'samples_file': 'memory-samples.jsonl', 'scope': 'Proof process only; sampling begins after input loading and CSR prepare return; includes fresh-state allocation, execution, native hashing and collection. Not total system/unified memory.'},
    'scope': 'Complete 0.1-second sugar trial 0 CPU comparator observation/repeat proof. No four-trial/one-second gate, full three-engine matrix acceptance or benchmark approval.',
}
write_json(output / 'cpu-observer.json', report)
print(json.dumps(report), flush=True)
