import csv
import hashlib
import importlib.util
import json
import subprocess
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import numpy as np

from fly_brain.comparison.acceptance import (
    evaluate_case,
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.comparison.models import SpikeSteps
from fly_brain.simulation.inputs import file_sha256
from fly_brain.simulation.models import InputPin

root = Path.cwd()
run = root / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01'
output = root / 'data/results/milestone-4-sugar-one-second-first-metrics-20261005-01'
environment = json.loads((run / 'environment.json').read_text())
for module, digest in environment['source_sha256'].items():
    base = Path('src').joinpath(*module.split('.'))
    path = (
        base.with_suffix('.py')
        if base.with_suffix('.py').is_file()
        else base / '__init__.py'
    )
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    assert (
        hashlib.sha256(
            subprocess.check_output(['git', 'show', '55ea35f:' + str(path)])
        ).hexdigest()
        == digest
    )
pin = InputPin(
    **json.loads(
        (root / 'docs/evidence/milestone-4/cases/p9-1000-0/case.json').read_text()
    )['input_pins']
)
assert file_sha256(root / 'data/2025_Completeness_783.csv') == pin.completeness_sha256
assert (
    file_sha256(root / 'data/2025_Connectivity_783.parquet') == pin.connectivity_sha256
)
with (root / 'data/2025_Completeness_783.csv').open(newline='') as source:
    reader = csv.reader(source)
    assert next(reader) == ['', 'Completed']
    mapping = np.asarray([int(row[0]) for row in reader], dtype=np.int64)
assert mapping.shape == (138639,) and len(np.unique(mapping)) == 138639
paired = run / 'observations/paired-first'
causal = json.loads((paired / 'causal.json').read_text())
assert causal['steps'] == 10000 and causal['first_budget_violation'] is None
assert causal['first_spike_step'] == 5719 and causal['first_spike_neurons'] == [100750]
rows = [
    json.loads(line)
    for line in (run / 'observations/cpu-first/native-digests.jsonl')
    .read_text()
    .splitlines()
]
assert [row['step'] for row in rows] == list(range(-1, 10000))
paths = {
    'brian': paired / 'reference-native.npz',
    'mlx': paired / 'mlx-native.npz',
    'torch': run / 'observations/cpu-first/native.npz',
}
spikes, descriptors, archived = {}, {}, {}
for engine, path in paths.items():
    with np.load(path, allow_pickle=False) as native:
        if engine == 'brian':
            indices, times = native['spike_i'], native['spike_t']
            assert indices.dtype == np.int32 and times.dtype == np.float64
            steps = steps_from_reference_clock(times, 10000)
            positions = indices.astype(np.int64)
            coordinates = {'spike_i': indices, 'spike_t': times}
        else:
            positions, steps = native['spike_neurons'], native['spike_steps']
            assert positions.dtype == np.int64 and steps.dtype == np.int64
            coordinates = {'spike_neurons': positions, 'spike_steps': steps}
            if engine == 'torch':
                trials = native['spike_trials']
                assert (
                    trials.dtype == np.int64
                    and trials.shape == positions.shape
                    and not trials.any()
                )
                coordinates['spike_trials'] = trials
        validate_coordinates(SpikeSteps(positions, steps), pin.neurons, 10000)
        spikes[engine] = SpikeSteps(mapping[positions], steps)
        descriptors[engine] = {
            name: {
                'dtype': value.dtype.str,
                'shape': list(value.shape),
                'sha256': hashlib.sha256(value.tobytes()).hexdigest(),
            }
            for name, value in coordinates.items()
        }
        archived.update(
            {engine + '_' + name: value for name, value in coordinates.items()}
        )
        archived[engine + '_mapped_neurons'] = spikes[engine].neurons
        archived[engine + '_integer_steps'] = steps
score_path = root / 'docs/evidence/milestone-4/case-adjudication/independent-score.py'
spec = importlib.util.spec_from_file_location(
    'independent_sugar_first_score', score_path
)
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)
assert (
    hashlib.sha256(score_path.read_bytes()).hexdigest()
    == json.loads(
        score_path.with_name('independent-score-verification.json').read_text()
    )['executed_program_sha256']
)
support = sorted(
    set().union(*(Counter(map(int, value.neurons)) for value in spikes.values()))
)
independent = {
    engine: scorer.score(
        (
            (
                (spikes['brian'].neurons, spikes['brian'].steps),
                (spikes[engine].neurons, spikes[engine].steps),
            ),
        ),
        support,
        1.0,
    )
    for engine in ('mlx', 'torch')
}
application = evaluate_case(spikes['brian'], spikes['mlx'], spikes['torch'], 1.0)
for engine in independent:
    scorer.verify_metrics(
        json.loads(
            json.dumps(asdict(getattr(application, engine)), default=scorer.encode)
        ),
        independent[engine],
    )
checks = scorer.gates(independent['mlx'], independent['torch'])
assert checks == application.checks
output.mkdir(parents=True, exist_ok=False)
with (output / 'native-spikes.npz').open('xb') as destination:
    np.savez_compressed(destination, **archived)
record = {
    'parent_checkpoint': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True
    ).strip(),
    'launch_checkpoint': '55ea35f',
    'case': {'experiment': 'sugar', 'steps': 10000, 'trial': 0},
    'all_19_fields_independently_recomputed_and_application_equal': True,
    'checks': checks,
    'all_11_metric_gates_pass': all(checks.values()),
    'metrics': independent,
    'native_coordinate_descriptors': descriptors,
    'original_native_file_sha256': {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths.values()
    },
    'input_pins': asdict(pin),
    'neuron_mapping_sha256': hashlib.sha256(mapping.tobytes()).hexdigest(),
    'saved_native_spikes_sha256': hashlib.sha256(
        (output / 'native-spikes.npz').read_bytes()
    ).hexdigest(),
    'independent_scorer_sha256': hashlib.sha256(score_path.read_bytes()).hexdigest(),
    'executed_program_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'case_accepted': False,
    'scope': 'Complete first-run native spikes and all frozen metric gates only; fresh CPU repeat, complete replay, own future queues and final reviewed-case verification remain required.',
}
with (output / 'first-metrics.json').open('x') as destination:
    json.dump(record, destination, indent=2, default=scorer.encode, allow_nan=False)
print(
    json.dumps(
        {
            'verified': True,
            'checks': checks,
            'metrics': independent,
            'case_accepted': False,
        },
        default=scorer.encode,
    ),
    flush=True,
)
