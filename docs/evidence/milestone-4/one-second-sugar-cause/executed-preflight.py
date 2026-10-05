import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np

from fly_brain.qualification.rounding_review import require_rounding_prerequisites

root = Path.cwd()
run = root / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01'
first = run / 'observations/paired-first'
output = Path(sys.argv[1]).resolve()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
read = lambda path: json.loads(path.read_text())
sha = lambda data: hashlib.sha256(data).hexdigest()
causal = read(first / 'causal.json')
assert causal['steps'] == 10000 and causal['first_spike_step'] == 5719
assert causal['first_spike_neurons'] == [100750] and causal['first_budget_violation'] is None
context = causal['contexts']['spike']
assert context['neurons'] == [100750] and causal['contexts']['budget'] is None
sources = {}
for module, expected in read(run / 'environment.json')['source_sha256'].items():
    relative = Path('src') / module.replace('.', '/')
    path = relative.with_suffix('.py')
    if not path.is_file():
        path = relative / '__init__.py'
    assert sha(path.read_bytes()) == expected
    assert sha(subprocess.check_output(['git', 'show', f'55ea35f:{path}'])) == expected
    sources[str(path)] = expected
blocks = [json.loads(line) for line in (first / 'phase-digests.jsonl').read_text().splitlines()]
assert [(row['begin'], row['rows']) for row in blocks] == [(begin, min(32, 10000 - begin)) for begin in range(0, 10000, 32)]
physical = [json.loads(line) for line in (first / 'physical-digests.jsonl').read_text().splitlines()]
assert [row['step'] for row in physical] == list(range(10001))
with np.load(first / 'spike-context.npz', allow_pickle=False) as arrays:
    assert set(arrays.files) == set(context['arrays'])
    for name, descriptor in context['arrays'].items():
        value = arrays[name]
        assert {'dtype': value.dtype.str, 'shape': list(value.shape), 'sha256': sha(value.tobytes())} == descriptor
    reference = arrays['current_reference_pre_v']
    candidate = arrays['current_mlx_pre_v']
    spikes = np.zeros(reference.shape, dtype=np.bool_)
    spikes[arrays['current_reference_spikes']] = True
    require_rounding_prerequisites(reference, candidate, arrays['current_reference_pre_not_refractory'], arrays['current_mlx_pre_not_refractory'], spikes, arrays['current_mlx_spikes'], (100750,))
    comparisons = []
    for position, phase in (('current', 'pre'), ('previous', 'pre'), ('previous', 'before'), ('previous', 'end')):
        for field in ('v', 'g'):
            expected = arrays[f'{position}_reference_{phase}_{field}'] * 1000
            actual = arrays[f'{position}_mlx_{phase}_{field}'].astype(np.float64)
            error = np.abs(actual - expected)
            budget = 1e-3 + 1e-5 * np.abs(expected)
            assert actual.shape == expected.shape == (138639,)
            assert np.isfinite(actual).all() and np.isfinite(expected).all()
            assert np.all(error <= budget)
            comparisons.append({'position': position, 'phase': phase, 'field': field, 'neurons': 138639, 'maximum_error_mv': float(error.max()), 'maximum_budget_fraction': float((error / budget).max())})
    neuron = 100750
    values = {'neuron': neuron, 'neuron_id': int(arrays['affected_neuron_ids'][0]), 'reference_voltage_si': float(reference[neuron]), 'mlx_voltage_mv': float(candidate[neuron]), 'reference_margin_mv': float(reference[neuron] * 1000 + 45), 'mlx_margin_mv': float(np.float64(candidate[neuron]) + 45), 'voltage_error_mv': float(abs(reference[neuron] * 1000 - np.float64(candidate[neuron]))), 'budget_mv': float(1e-3 + 1e-5 * abs(reference[neuron] * 1000)), 'reference_spike': bool(spikes[neuron]), 'mlx_spike': bool(arrays['current_mlx_spikes'][neuron]), 'previous_mlx_last_spike_step': int(arrays['previous_mlx_end_last_spike_step'][neuron])}
files = sorted({*run.glob('*.json'), *run.glob('*.npz'), *first.glob('*.json'), *first.glob('*.jsonl'), *first.glob('*.npz')})
manifest = {str(path.relative_to(run)): sha(path.read_bytes()) for path in files}
output.mkdir(parents=True, exist_ok=False)
with zipfile.ZipFile(output / 'first-observation.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in files:
        archive.write(path, str(path.relative_to(run)))
with zipfile.ZipFile(output / 'first-observation.zip') as archive:
    assert set(archive.namelist()) == set(manifest)
    assert all(sha(archive.read(name)) == digest for name, digest in manifest.items())
shutil.copyfile(__file__, output / 'executed-preflight.py')
record = {'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(), 'launch_checkpoint': '55ea35f', 'execution': str(run.relative_to(root)), 'first_spike_step': 5719, 'first_spike_neurons': [100750], 'no_first_budget_violation_reported': True, 'all_native_context_descriptors_verified': len(context['arrays']), 'complete_first_phase_blocks': len(blocks), 'complete_first_physical_snapshots': len(physical), 'threshold_prerequisites_pass': True, 'native_threshold_values': values, 'direct_all_neuron_cause_budget_comparisons': comparisons, 'executed_source_sha256': sources, 'artifact_sha256': manifest, 'archive_sha256': sha((output / 'first-observation.zip').read_bytes()), 'executed_program_sha256': sha(Path(__file__).read_bytes()), 'case_accepted': False, 'scientific_classification': 'Unresolved; bounded Astra review required.', 'scope': 'Completed first paired execution and its direct native cause prerequisites only. Full repeat, CPU metrics, future own queues and final case acceptance remain unresolved.'}
with (output / 'first-cause-preflight.json').open('x') as target:
    json.dump(record, target, indent=2, allow_nan=False)
    target.write('\n')
print(json.dumps({'verified': True, 'cause': values, 'context_arrays': len(context['arrays']), 'case_accepted': False}, allow_nan=False))
