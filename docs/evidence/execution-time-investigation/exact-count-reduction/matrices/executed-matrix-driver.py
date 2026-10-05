import hashlib
import json
import signal
import subprocess
import time
from functools import partial
from pathlib import Path

import mlx.core as mx
import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters import bucketed_scalars, device_layout_probe, fan_in_probe
from fly_brain.qualification.adapters.bucketed_fan_in import evaluate_cases
from fly_brain.simulation.backend.bucketed import make_layout

root = Path('/Users/ocasta/Code/fly-brain')
output = root / 'data/results/performance-remediation-exact-count-matrices-20261005'
output.mkdir(exist_ok=False)
signal.alarm(1800)
mx.disable_compile()
started = time.perf_counter()
connectome, pin = pinned_inputs(root)
record = {'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'mode': 'Guarded exact-count reduction; original fallback outside full absolute-count envelope.', 'compilation': 'disabled', 'MLX_ENABLE_TF32': '0', 'device': mx.device_info(), 'checks': {}}
print(json.dumps({'phase': 'scalar-matrix'}), flush=True)
record['checks']['scalars'] = bucketed_scalars.run(root, output / 'scalars', '0', exact_counts=True)
assert record['checks']['scalars']['accepted'] is True
scalar_report = json.loads((output / 'scalars/bucketed-scalars.json').read_text())
record['scalar_reducers'] = {name: sum(row['count_reduction'] == name for row in scalar_report['measurements']) for name in ('exact-integer', 'compensated-tree')}
print(json.dumps({'phase': 'scalar-matrix-passed', 'reducers': record['scalar_reducers']}), flush=True)
layout = make_layout(connectome, exact_counts=True)
assert layout.exact_counts is True
print(json.dumps({'phase': 'prescribed-pinned-matrix'}), flush=True)
record['checks']['pinned'] = fan_in_probe.run(connectome, pin, output / 'pinned', '0', evaluator=partial(evaluate_cases, exact_counts=True), scope='All prescribed pinned cases with guarded exact-count reduction active; unchanged reference budgets and conversion limitations.')
assert record['checks']['pinned']['accepted'] is True
print(json.dumps({'phase': 'pinned-matrix-passed', 'cases': record['checks']['pinned']['cases']}), flush=True)
print(json.dumps({'phase': 'complete-native-layout'}), flush=True)
record['checks']['layout'] = device_layout_probe.run(connectome, pin, output / 'layout', '0', exact_counts=True)
assert record['checks']['layout']['accepted'] is True
assert record['checks']['layout']['count_reduction'] == 'exact-integer'
record['elapsed_s'] = time.perf_counter() - started
record['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
record['source_sha256'] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (root / 'src/fly_brain/simulation/backend/accumulation.py', root / 'src/fly_brain/simulation/backend/bucketed.py', root / 'src/fly_brain/qualification/adapters/bucketed_scalars.py', root / 'src/fly_brain/qualification/adapters/bucketed_fan_in.py', root / 'src/fly_brain/qualification/adapters/device_layout_probe.py')}
(output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
signal.alarm(0)
print(json.dumps({'completed': True, 'elapsed_s': record['elapsed_s'], 'output': str(output)}), flush=True)
