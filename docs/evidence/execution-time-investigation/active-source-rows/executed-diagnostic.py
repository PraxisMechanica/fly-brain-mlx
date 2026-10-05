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
OUT = Path('/private/tmp/fly-brain-active-rows-performance-20261005-01')
OUT.mkdir(exist_ok=False)
signal.alarm(90)
torch.set_num_threads(1)
started = time.perf_counter()
connectome, pin = pinned_inputs(ROOT)
weights = prepare(connectome, (), (), 1).weights
source_degree = np.bincount(connectome.sources, minlength=pin.neurons)
order = np.argsort(connectome.sources, kind='stable')
offsets = np.concatenate(([0], np.cumsum(source_degree)))
destinations = connectome.destinations[order]
counts = connectome.counts[order].astype(np.float64)
row_absolute_sum = np.bincount(connectome.destinations, weights=np.abs(connectome.counts.astype(np.float64)), minlength=pin.neurons)
assert row_absolute_sum.max() == 69948
assert np.isfinite(counts).all() and np.array_equal(counts, np.floor(counts))
native = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/cpu-first/native.npz'
with np.load(native, allow_pickle=False) as saved:
    steps = saved['spike_steps'].copy()
    neurons = saved['spike_neurons'].copy()
busy = int(np.bincount(steps, minlength=10000).argmax())
real = torch.zeros((1, pin.neurons), dtype=torch.float32)
real[0, torch.from_numpy(neurons[steps == busy])] = 1
patterns = {'rest': torch.zeros_like(real), 'actual_busiest_saved_step': real, 'all_neurons_firing_arithmetic_envelope': torch.ones_like(real), 'four_independent_rows': torch.cat((torch.zeros_like(real), real, torch.ones_like(real), 1-real), dim=0)}
setup_s = time.perf_counter() - started
print(json.dumps({'phase': 'prepared', 'setup_s': setup_s}), flush=True)


def original(spikes):
    return torch.matmul(spikes, weights.transpose(0, 1))


def active_rows(spikes):
    rows = []
    for row in spikes.numpy():
        active = np.flatnonzero(row)
        if active.size:
            indices = np.concatenate([np.arange(offsets[s], offsets[s+1]) for s in active])
            summed = np.bincount(destinations[indices], weights=counts[indices], minlength=pin.neurons)
        else:
            summed = np.zeros(pin.neurons, dtype=np.float64)
        rows.append(summed.astype(np.float32))
    return torch.from_numpy(np.stack(rows))


records = {}
with torch.no_grad():
    for label, spikes in patterns.items():
        expected = original(spikes).numpy().copy()
        expected_scaled = (0.275 * torch.from_numpy(expected)).numpy().copy()
        active_rows(spikes)
        durations = []
        for _ in range(5):
            before = time.perf_counter()
            output = active_rows(spikes)
            durations.append(time.perf_counter() - before)
        actual = output.numpy()
        scaled = (0.275 * output).numpy()
        assert actual.dtype == expected.dtype and actual.shape == expected.shape and actual.tobytes() == expected.tobytes()
        assert scaled.dtype == expected_scaled.dtype and scaled.shape == expected_scaled.shape and scaled.tobytes() == expected_scaled.tobytes()
        records[label] = {'seconds': durations, 'median_s': statistics.median(durations), 'input_shape': list(spikes.shape), 'firing_neurons_per_row': spikes.sum(1).tolist(), 'selected_edge_visits_per_row': [int(source_degree[np.flatnonzero(row)].sum()) for row in spikes.numpy()], 'output_stride': list(output.stride()), 'exact_native_dtype_shape_and_bytes_equal': True, 'unchanged_post_sum_scale_bytes_equal': True, 'output_sha256': hashlib.sha256(actual.tobytes()).hexdigest()}
        print(json.dumps({'phase': 'measured', 'pattern': label, **records[label]}), flush=True)
record = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'scope': 'Alternative active-source gather/bincount operation diagnostic using existing NumPy and original weights. No full model is run and no comparator evaluator is adopted.',
    'decision_confidence_percent': 95,
    'torch': torch.__version__, 'numpy': np.__version__, 'cpu_threads': torch.get_num_threads(),
    'neurons': pin.neurons, 'edges': pin.edges, 'setup_s': setup_s,
    'integer_row_bound': float(row_absolute_sum.max()),
    'accumulation_dtype': 'float64 exact integer accumulation, cast to float32 before unchanged torch post-sum scale',
    'patterns': records,
    'retained_cpu_one_second_spike_count': int(neurons.size),
    'retained_cpu_one_second_average_firing_neurons_per_step': float(neurons.size / 10000),
    'retained_cpu_one_second_active_outgoing_edge_visits': int(source_degree[neurons].sum()),
    'dense_full_scan_edge_visits_per_10000_steps': int(pin.edges * 10000),
    'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'input_artifact_sha256': hashlib.sha256(native.read_bytes()).hexdigest(),
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'src/fly_brain/qualification/adapters/torch_setup.py', ROOT / 'src/fly_brain/qualification/adapters/torch_reference.py')},
    'elapsed_s': time.perf_counter() - started,
    'application_changed': False, 'baseline_change_adopted': False, 'new_full_case_or_matrix_run': False, 'p9_resumed': False,
    'limits': 'Selected operation inputs only; output construction included in timings. Dense all-firing and near-all-firing batch rows expose poor worst-case cost. Exact integer arithmetic proof and matching samples do not qualify a replacement of the frozen comparator or every complete trajectory. This diagnostic does not change the MLX-only production objective.',
}
with (OUT / 'result.json').open('x') as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'completed': True, 'elapsed_s': record['elapsed_s'], 'result': str(OUT / 'result.json')}), flush=True)
