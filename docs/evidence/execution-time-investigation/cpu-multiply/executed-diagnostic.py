import hashlib
import json
import signal
import statistics
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.torch_setup import prepare

ROOT = Path('/Users/ocasta/Code/fly-brain')
OUT = Path('/private/tmp/fly-brain-cpu-matmul-performance-20261005-01')
OUT.mkdir(exist_ok=False)
signal.alarm(90)
torch.set_num_threads(1)
started = time.perf_counter()
connectome, pin = pinned_inputs(ROOT)
model = prepare(connectome, (), (), 1)
weights = model.weights
values = weights.values().numpy()
row_abs = np.bincount(connectome.destinations, weights=np.abs(connectome.counts.astype(np.float64)), minlength=pin.neurons)
bound = float(row_abs.max())
assert np.isfinite(values).all() and np.array_equal(values, np.floor(values))
assert bound < 2**24
with np.load(ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/cpu-first/native.npz', allow_pickle=False) as saved:
    raster_steps = saved['spike_steps'].copy()
    raster_neurons = saved['spike_neurons'].copy()
busy = int(np.bincount(raster_steps, minlength=10000).argmax())
real = torch.zeros((1, pin.neurons), dtype=torch.float32)
real[0, torch.from_numpy(raster_neurons[raster_steps == busy])] = 1
patterns = {
    'rest': torch.zeros_like(real),
    'actual_busiest_saved_step': real,
    'all_neurons_firing_arithmetic_envelope': torch.ones_like(real),
    'four_independent_rows': torch.cat((torch.zeros_like(real), real, torch.ones_like(real), 1 - real), dim=0),
}
setup_s = time.perf_counter() - started
print(json.dumps({'phase': 'prepared', 'setup_s': setup_s, 'max_original_row_absolute_count': bound, 'coalesced_csr_entries': weights._nnz()}), flush=True)


def original(spikes):
    return torch.matmul(spikes, weights.transpose(0, 1))


def csr_default(spikes):
    return torch.sparse.mm(weights, spikes.transpose(0, 1)).transpose(0, 1)


def csr_explicit_sum(spikes):
    return torch.sparse.mm(weights, spikes.transpose(0, 1), reduce='sum').transpose(0, 1)


operations = {'original_dense_times_csc': original, 'csr_times_dense_default': csr_default, 'csr_times_dense_explicit_sum': csr_explicit_sum}
records = {}
with torch.no_grad():
    for label, spikes in patterns.items():
        expected = original(spikes).numpy().copy()
        measurements = {}
        for name, operation in operations.items():
            operation(spikes)
            durations = []
            for _ in range(5):
                before = time.perf_counter()
                output = operation(spikes)
                durations.append(time.perf_counter() - before)
            actual = output.numpy()
            measurements[name] = {
                'seconds': durations,
                'median_s': statistics.median(durations),
                'exact_native_dtype_shape_and_bytes_equal': (actual.dtype == expected.dtype and actual.shape == expected.shape and actual.tobytes() == expected.tobytes()),
                'maximum_absolute_difference': float(np.max(np.abs(actual.astype(np.float64) - expected))),
                'output_shape': list(output.shape),
                'output_stride': list(output.stride()),
                'output_sha256': hashlib.sha256(actual.tobytes()).hexdigest(),
            }
        assert all(row['exact_native_dtype_shape_and_bytes_equal'] for row in measurements.values())
        records[label] = {'input_shape': list(spikes.shape), 'firing_neurons_per_row': spikes.sum(1).tolist(), 'measurements': measurements}
        print(json.dumps({'phase': 'measured', 'pattern': label, 'median_s': {name: row['median_s'] for name, row in measurements.items()}}), flush=True)
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU], record_shapes=True) as profiler:
        for name, operation in operations.items():
            with torch.profiler.record_function(name):
                operation(real)
    profiler.export_chrome_trace(str(OUT / 'cpu-operator-trace.json'))
    profile = [{'name': event.key, 'count': event.count, 'self_cpu_time_us': event.self_cpu_time_total, 'cpu_time_us': event.cpu_time_total} for event in profiler.key_averages()]

record = {
    'scope': 'Bounded component performance diagnosis using unchanged original comparator weights and selected saved/whole-binary-envelope inputs; no model replacement or full trajectory qualification.',
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'torch': torch.__version__, 'numpy': np.__version__,
    'torch_git_version': torch.version.git_version,
    'torch_build': torch.__config__.show(),
    'cpu_threads': torch.get_num_threads(), 'cpu_interop_threads': torch.get_num_interop_threads(),
    'weights_layout': str(weights.layout), 'weights_dtype': str(weights.dtype),
    'original_rows': pin.edges, 'neurons': pin.neurons, 'coalesced_csr_entries': weights._nnz(),
    'all_stored_weights_finite_integral_float32': True,
    'maximum_stored_absolute_weight': float(np.abs(values).max()),
    'maximum_original_row_absolute_count_sum': bound,
    'float32_exact_integer_bound': 2**24,
    'native_busiest_step': busy,
    'setup_s': setup_s,
    'patterns': records,
    'profile': profile,
    'elapsed_s': time.perf_counter() - started,
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'src/fly_brain/qualification/adapters/torch_reference.py', ROOT / 'src/fly_brain/qualification/adapters/torch_setup.py')},
    'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'application_changed': False, 'baseline_change_adopted': False,
    'new_full_case_or_matrix_run': False, 'p9_resumed': False,
    'limits': 'Timing only selected standalone multiply operations. Full pipeline speed and a changed comparator mode remain unqualified.',
}
with (OUT / 'result.json').open('x') as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'completed': True, 'elapsed_s': record['elapsed_s'], 'result': str(OUT / 'result.json')}), flush=True)
