import hashlib
import json
import shutil
import statistics
import subprocess
from pathlib import Path

import numpy as np

from fly_brain.bootstrap import pinned_inputs

ROOT = Path('/Users/ocasta/Code/fly-brain')
SOURCE = Path('/private/tmp/fly-brain-active-rows-performance-20261005-01')
OUT = ROOT / 'docs/evidence/execution-time-investigation/active-source-rows'
OUT.mkdir(exist_ok=False)
shutil.copy2(SOURCE / 'result.json', OUT / 'result.json')
shutil.copy2(SOURCE.with_suffix('.py'), OUT / 'executed-diagnostic.py')
result = json.loads((OUT / 'result.json').read_text())
assert hashlib.sha256((OUT / 'executed-diagnostic.py').read_bytes()).hexdigest() == result['runner_sha256']
for name, digest in result['source_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
native = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/cpu-first/native.npz'
assert hashlib.sha256(native.read_bytes()).hexdigest() == result['input_artifact_sha256']
original = json.loads((ROOT / 'docs/evidence/execution-time-investigation/cpu-multiply/result.json').read_text())
for name, pattern in result['patterns'].items():
    assert len(pattern['seconds']) == 5
    assert statistics.median(pattern['seconds']) == pattern['median_s'] > 0
    assert pattern['exact_native_dtype_shape_and_bytes_equal']
    assert pattern['unchanged_post_sum_scale_bytes_equal']
    assert pattern['output_sha256'] == original['patterns'][name]['measurements']['original_dense_times_csc']['output_sha256']
connectome, pin = pinned_inputs(ROOT)
degree = np.bincount(connectome.sources, minlength=pin.neurons)
with np.load(native, allow_pickle=False) as saved:
    spike_steps, spike_neurons = saved['spike_steps'], saved['spike_neurons']
    busy = int(np.bincount(spike_steps, minlength=10000).argmax())
    assert int(degree[spike_neurons].sum()) == result['retained_cpu_one_second_active_outgoing_edge_visits']
    assert int(degree[spike_neurons[spike_steps == busy]].sum()) == result['patterns']['actual_busiest_saved_step']['selected_edge_visits_per_row'][0]
assert pin.edges * 10000 == result['dense_full_scan_edge_visits_per_10000_steps']
busy_original = original['patterns']['actual_busiest_saved_step']['measurements']['original_dense_times_csc']['median_s']
busy_active = result['patterns']['actual_busiest_saved_step']['median_s']
verification = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'runner_application_source_and_retained_input_hashes_verified': True,
    'native_output_hashes_independently_match_original_operation_probe': True,
    'all_medians_recomputed': True,
    'retained_raster_active_edge_work_independently_recomputed': True,
    'busiest_saved_step_component_speedup_against_earlier_original_probe': busy_original / busy_active,
    'retained_raster_full_scan_to_active_edge_visit_ratio': result['dense_full_scan_edge_visits_per_10000_steps'] / result['retained_cpu_one_second_active_outgoing_edge_visits'],
    'limits': 'Native-byte comparisons cover selected operations; no full comparator execution-mode replacement or whole-trajectory qualification. Component speedup uses separately measured original and active probes. Dense/all-firing rows are slower with this simple prototype.',
}
with (OUT / 'verification.json').open('x') as stream:
    json.dump(verification, stream, indent=2)
    stream.write('\n')
print(json.dumps(verification, indent=2))
