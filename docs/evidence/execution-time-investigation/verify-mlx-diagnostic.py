import hashlib
import json
import shutil
import statistics
import subprocess
from pathlib import Path

ROOT = Path('/Users/ocasta/Code/fly-brain')
SOURCE = Path('/private/tmp/fly-brain-mlx-component-performance-20261005-01')
OUT = ROOT / 'docs/evidence/execution-time-investigation/mlx-components'
OUT.mkdir(exist_ok=False)
shutil.copy2(SOURCE / 'result.json', OUT / 'result.json')
shutil.copy2(SOURCE.with_suffix('.py'), OUT / 'executed-diagnostic.py')
result = json.loads((OUT / 'result.json').read_text())
assert hashlib.sha256((OUT / 'executed-diagnostic.py').read_bytes()).hexdigest() == result['runner_sha256']
for name, digest in result['source_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
endpoint = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/paired-first/mlx-native.npz'
assert hashlib.sha256(endpoint.read_bytes()).hexdigest() == result['input_artifact_sha256']
for component in result['device_components'].values():
    assert len(component['samples']) == 5
    for name in ('graph_build', 'synchronized_evaluation', 'total'):
        assert statistics.median(s[name + '_s'] for s in component['samples']) == component['median_' + name + '_s']
        assert component['median_' + name + '_s'] > 0
for component in result['host_components'].values():
    assert len(component['seconds']) == 5
    assert statistics.median(component['seconds']) == component['median_s'] > 0
assert result['all_thirty_independent_ledger_checks_pass_on_probed_step']
assert result['separate_queue_expression_equals_unchanged_step_native_bytes']
assert result['host_logical_scan_bytes']['queue'] == 19 * 15091983
assert result['host_logical_scan_bytes']['due'] == 15091983
verification = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'archived_runner_application_source_and_retained_endpoint_hashes_verified': True,
    'all_medians_recomputed_from_five_samples': True,
    'queue_and_due_scan_byte_counts_independently_verified': True,
    'limits': 'Archive, timing arithmetic and executed diagnostic assertions verified. No new scientific trajectory or native hardware trace; no component times added into an exact whole-step profile.',
}
with (OUT / 'verification.json').open('x') as stream:
    json.dump(verification, stream, indent=2)
    stream.write('\n')
print(json.dumps(verification))
