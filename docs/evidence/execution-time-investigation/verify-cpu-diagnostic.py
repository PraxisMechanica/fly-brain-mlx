import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import torch

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.torch_setup import prepare

ROOT = Path('/Users/ocasta/Code/fly-brain')
SOURCE = Path('/private/tmp/fly-brain-cpu-matmul-performance-20261005-01')
OUT = ROOT / 'docs/evidence/execution-time-investigation/cpu-multiply'
OUT.mkdir(exist_ok=False)
for name in ('result.json', 'cpu-operator-trace.json'):
    shutil.copy2(SOURCE / name, OUT / name)
shutil.copy2(SOURCE.with_suffix('.py'), OUT / 'executed-diagnostic.py')
result = json.loads((OUT / 'result.json').read_text())
assert hashlib.sha256((OUT / 'executed-diagnostic.py').read_bytes()).hexdigest() == result['runner_sha256']
for name, digest in result['source_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
for pattern in result['patterns'].values():
    measurements = tuple(pattern['measurements'].values())
    assert all(m['exact_native_dtype_shape_and_bytes_equal'] for m in measurements)
    assert len({m['output_sha256'] for m in measurements}) == 1
    assert all(m['median_s'] > 0 and len(m['seconds']) == 5 for m in measurements)
trace = json.loads((OUT / 'cpu-operator-trace.json').read_text())
assert any(e.get('name') == 'aten::_sparse_mm_reduce_impl' for e in trace['traceEvents'])
torch.set_num_threads(1)
connectome, pin = pinned_inputs(ROOT)
weights = prepare(connectome, (), (), 1).weights
arrays = {
    'values': weights.values().numpy(),
    'column_indices': weights.col_indices().numpy(),
    'row_offsets': weights.crow_indices().numpy(),
}
row_absolute_sum = np.bincount(connectome.destinations, weights=np.abs(connectome.counts.astype(np.float64)), minlength=pin.neurons)
assert np.isfinite(arrays['values']).all()
assert np.array_equal(arrays['values'], np.floor(arrays['values']))
assert row_absolute_sum.max() == result['maximum_original_row_absolute_count_sum'] == 69948
assert weights._nnz() == result['coalesced_csr_entries'] == pin.edges
assert np.abs(connectome.counts).max() == arrays['values'].max() or np.abs(connectome.counts).max() == np.abs(arrays['values']).max()
busy = result['patterns']['actual_busiest_saved_step']['measurements']
verification = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'archived_runner_and_source_hashes_verified': True,
    'all_reported_native_output_hashes_agree': True,
    'specialized_reduce_operator_present_in_native_profile': True,
    'prepared_csr': {name: {'shape': list(a.shape), 'dtype': str(a.dtype), 'bytes': a.nbytes, 'sha256': hashlib.sha256(a.tobytes()).hexdigest()} for name, a in arrays.items()},
    'matrix_storage_bytes': sum(a.nbytes for a in arrays.values()),
    'row_bound_independently_recomputed': float(row_absolute_sum.max()),
    'actual_saved_step_component_speedup': busy['original_dense_times_csc']['median_s'] / busy['csr_times_dense_explicit_sum']['median_s'],
    'two_10000_step_original_multiply_extrapolation_s': 20000 * busy['original_dense_times_csc']['median_s'],
    'two_10000_step_explicit_sum_multiply_extrapolation_s': 20000 * busy['csr_times_dense_explicit_sum']['median_s'],
    'limits': 'Independent archive, invariant and profile checks. Selected operation equivalence is not full comparator-mode or whole-trajectory qualification. Extrapolations are component arithmetic budgets, not measured full runs.',
}
with (OUT / 'verification.json').open('x') as stream:
    json.dump(verification, stream, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps(verification, indent=2))
