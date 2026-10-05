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
OUT = Path('/private/tmp/fly-brain-active-sparse-performance-20261005-01')
OUT.mkdir(exist_ok=False)
signal.alarm(90)
torch.set_num_threads(1)
started = time.perf_counter()
connectome, pin = pinned_inputs(ROOT)
weights = prepare(connectome, (), (), 1).weights
transpose_started = time.perf_counter()
source_rows = weights.transpose(0, 1).to_sparse_csr()
transpose_s = time.perf_counter() - transpose_started
original_row_absolute_sum = np.bincount(connectome.destinations, weights=np.abs(connectome.counts.astype(np.float64)), minlength=pin.neurons)
assert original_row_absolute_sum.max() == 69948
assert np.isfinite(weights.values().numpy()).all()
assert np.array_equal(weights.values().numpy(), np.floor(weights.values().numpy()))
native = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/cpu-first/native.npz'
with np.load(native, allow_pickle=False) as saved:
    steps = saved['spike_steps'].copy()
    neurons = saved['spike_neurons'].copy()
busy = int(np.bincount(steps, minlength=10000).argmax())
real = torch.zeros((1, pin.neurons), dtype=torch.float32)
real[0, torch.from_numpy(neurons[steps == busy])] = 1
patterns = {'rest': torch.zeros_like(real), 'actual_busiest_saved_step': real, 'all_neurons_firing_arithmetic_envelope': torch.ones_like(real), 'four_independent_rows': torch.cat((torch.zeros_like(real), real, torch.ones_like(real), 1-real), dim=0)}
setup_s = time.perf_counter() - started
print(json.dumps({'phase': 'prepared', 'setup_s': setup_s, 'source_row_transpose_setup_s': transpose_s}), flush=True)


def original(spikes):
    return torch.matmul(spikes, weights.transpose(0, 1))


def sparse_active_rows(spikes):
    return torch.sparse.mm(spikes.to_sparse_csr(), source_rows).to_dense()


records = {}
with torch.no_grad():
    for label, spikes in patterns.items():
        expected = original(spikes).numpy().copy()
        sparse_active_rows(spikes)
        durations = []
        for _ in range(5):
            before = time.perf_counter()
            output = sparse_active_rows(spikes)
            durations.append(time.perf_counter() - before)
        actual = output.numpy()
        assert actual.dtype == expected.dtype and actual.shape == expected.shape
        assert actual.tobytes() == expected.tobytes()
        records[label] = {'seconds': durations, 'median_s': statistics.median(durations), 'input_shape': list(spikes.shape), 'firing_neurons_per_row': spikes.sum(1).tolist(), 'output_stride': list(output.stride()), 'exact_native_dtype_shape_and_bytes_equal': True, 'output_sha256': hashlib.sha256(actual.tobytes()).hexdigest()}
        print(json.dumps({'phase': 'measured', 'pattern': label, **records[label]}), flush=True)
    with torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU], record_shapes=True) as profile:
        sparse_active_rows(real)
    profile.export_chrome_trace(str(OUT / 'active-operator-trace.json'))
source_degree = np.bincount(connectome.sources, minlength=pin.neurons)
record = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'scope': 'Distinct active-source sparse-sparse operation probe. Original model, weights, one thread and post-sum scale are unchanged; no full model is run or evaluator adopted.',
    'decision_confidence_percent': 95,
    'torch': torch.__version__, 'cpu_threads': torch.get_num_threads(),
    'neurons': pin.neurons, 'edges': pin.edges,
    'setup_s': setup_s, 'source_row_transpose_setup_s': transpose_s,
    'original_row_absolute_sum_bound': float(original_row_absolute_sum.max()),
    'patterns': records,
    'retained_cpu_one_second_spike_count': int(neurons.size),
    'retained_cpu_one_second_average_firing_neurons_per_step': float(neurons.size / 10000),
    'retained_cpu_one_second_active_outgoing_edge_visits': int(source_degree[neurons].sum()),
    'dense_full_scan_edge_visits_per_10000_steps': int(pin.edges * 10000),
    'source_row_matrix': {name: {'dtype': str(value.numpy().dtype), 'shape': list(value.shape), 'bytes': value.numpy().nbytes, 'sha256': hashlib.sha256(value.numpy().tobytes()).hexdigest()} for name, value in (('values', source_rows.values()), ('column_indices', source_rows.col_indices()), ('row_offsets', source_rows.crow_indices()))},
    'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'input_artifact_sha256': hashlib.sha256(native.read_bytes()).hexdigest(),
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'src/fly_brain/qualification/adapters/torch_setup.py', ROOT / 'src/fly_brain/qualification/adapters/torch_reference.py')},
    'elapsed_s': time.perf_counter() - started,
    'application_changed': False, 'baseline_change_adopted': False, 'new_full_case_or_matrix_run': False, 'p9_resumed': False,
    'limits': 'Selected operation inputs, including the actual busiest saved CPU step and a synthetic all-firing/batch envelope. Sparse conversion and dense output cost are included. Not a whole-trajectory, timing-qualification or frozen-comparator replacement. Saved activity counts describe this original CPU raster, not every prescribed experiment.',
}
with (OUT / 'result.json').open('x') as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'completed': True, 'elapsed_s': record['elapsed_s'], 'result': str(OUT / 'result.json')}), flush=True)
