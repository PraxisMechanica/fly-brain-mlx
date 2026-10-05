import hashlib
import json
import signal
import subprocess
import time
from pathlib import Path
import mlx.core as mx
import numpy as np
from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.device_layout_probe import run
root = Path('/Users/ocasta/Code/fly-brain')
output = root / 'data/results/performance-remediation-exact-count-layout-20261005'
signal.alarm(300)
started = time.perf_counter()
mx.disable_compile()
connectome, pin = pinned_inputs(root)
report = run(connectome, pin, output, '0', exact_counts=True)
assert report['accepted'] is True and report['count_reduction'] == 'exact-integer'
original = root / 'docs/evidence/milestone-2/buckets/device-layout/device-layout.npz'
with np.load(original, allow_pickle=False) as expected, np.load(output / 'device-layout.npz', allow_pickle=False) as actual:
    assert expected.files == actual.files
    for field in expected.files:
        a, b = expected[field], actual[field]
        assert (a.dtype, a.shape, a.tobytes()) == (b.dtype, b.shape, b.tobytes()), field
record = {'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'elapsed_s': time.perf_counter()-started, 'complete_native_array_bytes_equal_retained_oracle': True, 'report': report, 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'original_sha256': hashlib.sha256(original.read_bytes()).hexdigest(), 'candidate_sha256': hashlib.sha256((output/'device-layout.npz').read_bytes()).hexdigest()}
(output/'verification.json').write_text(json.dumps(record, indent=2)+'\n')
signal.alarm(0)
print(json.dumps({'completed':True,'elapsed_s':record['elapsed_s'],'output':str(output)}),flush=True)
