import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.comparison.acceptance import evaluate_case, steps_from_reference_clock, validate_coordinates
from fly_brain.comparison.models import SpikeSteps
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def read_json(path):
    return json.loads(path.read_text())


def encode(value):
    if isinstance(value, Fraction):
        return {'numerator': value.numerator, 'denominator': value.denominator, 'value': float(value)}
    raise TypeError(type(value).__name__)


root = Path.cwd()
checkpoint = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
case = ParityCase('sugar', 1000, 0)
assert case in required_cases()
connectome, pin = pinned_inputs(root)
stimulus = generate(connectome, EXPERIMENTS[case.experiment], case.steps, (case.trial,))
paired = root / 'docs/evidence/milestone-4/full-paired-observer'
cpu = root / 'docs/evidence/milestone-4/full-cpu-observer'
paired_report, cpu_environment = read_json(paired / 'paired-observer.json'), read_json(cpu / 'environment.json')
assert paired_report['stimulus_sha256'] == cpu_environment['stimulus_sha256'] == stimulus.sha256
for path in (paired / 'stimulus.npz', cpu / 'stimulus.npz'):
    with np.load(path, allow_pickle=False) as f:
        assert f['events'].dtype == np.uint8 and np.array_equal(f['events'], stimulus.events)
        assert np.array_equal(f['targets'], stimulus.targets)
source_record = read_json(root / 'docs/evidence/milestone-4/cpu-observer/source-hashes.json')
for name in (
    'src/fly_brain/simulation/backend/core.py',
    'src/fly_brain/simulation/backend/bucketed.py',
    'src/fly_brain/simulation/backend/accumulation.py',
    'src/fly_brain/qualification/adapters/brian_jobs.py',
    'src/fly_brain/qualification/adapters/torch_reference.py',
    'src/fly_brain/qualification/adapters/torch_setup.py',
    'src/fly_brain/qualification/adapters/torch_observer.py',
):
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == source_record[name]
input_files = {
    'brian': paired / 'observed-reference-native.npz',
    'mlx': paired / 'observed-mlx-final.npz',
    'torch': cpu / 'observed-final.npz',
}
events, native_inputs = {}, {}
for engine, path in input_files.items():
    with np.load(path, allow_pickle=False) as f:
        names = ('spike_i', 'spike_t') if engine == 'brian' else ('spike_neurons', 'spike_steps')
        neurons, times = (f[name] for name in names)
        native_inputs[engine] = {'file': str(path.relative_to(root)), 'file_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'arrays': {name: {'dtype': f[name].dtype.str, 'shape': list(f[name].shape), 'sha256': hashlib.sha256(f[name].tobytes(order='C')).hexdigest()} for name in names}}
        if engine == 'brian':
            assert neurons.dtype == np.int32
            indices = neurons.astype(np.int64)
            steps = steps_from_reference_clock(times, case.steps)
        else:
            indices, steps = neurons, times
        validate_coordinates(SpikeSteps(indices, steps), pin.neurons, case.steps)
        events[engine] = SpikeSteps(connectome.neuron_ids[indices], steps)
assert np.array_equal(events['brian'].neurons, events['mlx'].neurons)
assert np.array_equal(events['brian'].steps, events['mlx'].steps)
paired_repeat = read_json(paired / 'repeat-verification.json')
cpu_repeat = read_json(cpu / 'verification.json')
observed, repeated = read_json(paired / 'observed.json'), read_json(paired / 'repeat.json')
case_checks = {
    'required_frozen_case': True,
    'pinned_inputs_and_unchanged_numerical_sources': True,
    'identical_canonical_events_targets_and_common_sugar_setup': True,
    'valid_unique_coordinates_and_exact_native_reference_clock': True,
    'mlx_native_state_and_queues_repeat': paired_repeat['every_mlx_native_phase_boundary_queue_and_due_mask_hash_repeats_exactly'],
    'reference_native_phases_and_physical_queues_repeat': paired_repeat['every_reference_native_phase_and_1001_physical_hashes_repeat_exactly'],
    'cpu_native_five_tensors_and_physical_buffers_repeat': cpu_repeat['all_1001_observed_and_repeat_native_five_tensor_digests_match_ordinary'],
    'no_common_history_state_budget_violation': observed['first_budget_violation'] is None and repeated['first_budget_violation'] is None,
    'first_different_spike_explicitly_none': observed['first_spike_step'] is None and repeated['first_spike_step'] is None,
}
acceptance = evaluate_case(events['brian'], events['mlx'], events['torch'], case.steps * 0.0001)
assert acceptance.accepted and all(case_checks.values())
with (output / 'normalized-spikes.npz').open('xb') as artifact:
    np.savez_compressed(artifact, **{engine + '_' + name: getattr(value, name) for engine, value in events.items() for name in ('neurons', 'steps')})
report = {
    'checkpoint': checkpoint, 'case': asdict(case), 'case_accepted': True, 'full_matrix_accepted': False,
    'case_checks': case_checks, 'metric_acceptance': asdict(acceptance), 'native_inputs_before_conversion': native_inputs,
    'stimulus_sha256': stimulus.sha256, 'input_pins': asdict(pin),
    'neuron_mapping_sha256': hashlib.sha256(connectome.neuron_ids.tobytes()).hexdigest(),
    'normalized_neurons': 'Exact FlyWire identifiers from pinned CSV order; coordinates validated before mapping.',
    'first_budget_violation': None, 'first_different_spike': None,
    'scope': 'Sugar trial 0 at 0.1 seconds: one of 52 required cases. All per-case fixed/paired/causal/replay gates pass. Prescribed one-second four-trial batches, remaining cases, pooled/time-bin matrix reports and performance remain open.',
}
with (output / 'case.json').open('x') as artifact:
    json.dump(report, artifact, indent=2, default=encode, allow_nan=False)
    artifact.write('\n')
print(json.dumps({'case_accepted': True, 'metric_checks': acceptance.checks, 'mlx_spikes': acceptance.mlx.candidate_spikes, 'torch_spikes': acceptance.torch.candidate_spikes, 'torch_jaccard': float(acceptance.torch.active_jaccard), 'torch_neuron_error': float(acceptance.torch.neuron_count_error), 'torch_correlation': acceptance.torch.rate_correlation, 'torch_timing_f1': float(acceptance.torch.timing_f1)}), flush=True)
