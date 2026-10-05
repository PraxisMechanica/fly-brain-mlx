import ast
import hashlib
import json
import shutil
import statistics
import struct
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path('/Users/ocasta/Code/fly-brain')
SOURCE = Path('/private/tmp/fly-brain-writer-performance-20261005-01')
OUT = ROOT / 'docs/evidence/execution-time-investigation/reference-writer'
OUT.mkdir(exist_ok=False)
for name in ('result.json', 'writer.cpp'):
    shutil.copy2(SOURCE / name, OUT / name)
shutil.copy2(SOURCE.with_suffix('.py'), OUT / 'executed-diagnostic.py')
result = json.loads((OUT / 'result.json').read_text())
assert hashlib.sha256((OUT / 'executed-diagnostic.py').read_bytes()).hexdigest() == result['runner_sha256']
assert hashlib.sha256((OUT / 'writer.cpp').read_bytes()).hexdigest() == result['cpp_sha256']
observer = ROOT / 'src/fly_brain/qualification/adapters/brian_observer.py'
assert hashlib.sha256(observer.read_bytes()).hexdigest() == result['brian_observer_source_sha256']
install = next(n for n in ast.parse(observer.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'install')
setup = next(n.value.value for n in install.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'setup' for t in n.targets))
assert setup in (OUT / 'writer.cpp').read_text()
endpoint = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/paired-first/reference-native.npz'
assert hashlib.sha256(endpoint.read_bytes()).hexdigest() == result['reference_artifact_sha256']
input_digest = hashlib.sha256(struct.pack('<QQ', result['neurons'], result['rows']))
with np.load(endpoint, allow_pickle=False) as saved:
    for name in ('v', 'g', 'lastspike', 'not_refractory'):
        input_digest.update(saved[name].tobytes())
assert input_digest.hexdigest() == result['input_sha256']
digests = set()
for mode in result['measurements'].values():
    assert len(mode['samples']) == 3
    assert statistics.median(s['wall_s'] for s in mode['samples']) == mode['median_wall_s']
    assert statistics.median(s['producer_cpu_s'] for s in mode['samples']) == mode['median_producer_cpu_s']
    for sample in mode['samples']:
        assert sample['stream_checksum_independently_matches']
        assert sample['output_bytes'] == 32 * 138639 * 59 + 3 * 32 * 8 + 4
        digests.add(sample['output_sha256'])
assert len(digests) == 1
modes = tuple(result['measurements'].values())
verification = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'exact_original_writer_setup_present_in_executed_cpp': True,
    'runner_cpp_application_source_endpoint_and_reconstructed_input_hashes_verified': True,
    'all_nine_recorded_output_digests_agree': True,
    'all_medians_recomputed': True,
    'compiled_diagnostic_binary_sha256': hashlib.sha256((SOURCE / 'writer').read_bytes()).hexdigest(),
    'buffered_boolean_component_speedup': modes[0]['median_wall_s'] / modes[1]['median_wall_s'],
    'buffered_native_checksum_component_speedup': modes[0]['median_wall_s'] / modes[2]['median_wall_s'],
    'limits': 'Archive and diagnostic result assertions verified. Repeated native endpoint planes form only a serialization workload; no complete observer-frame or scientific capture-mode qualification.',
}
with (OUT / 'verification.json').open('x') as stream:
    json.dump(verification, stream, indent=2)
    stream.write('\n')
print(json.dumps(verification, indent=2))
