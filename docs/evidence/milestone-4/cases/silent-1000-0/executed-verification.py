import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def read(path):
    return json.loads(path.read_text())


def sha(value):
    return hashlib.sha256(value).hexdigest()


def equal_archives(first, second):
    with np.load(first, allow_pickle=False) as a, np.load(second, allow_pickle=False) as b:
        assert set(a.files) == set(b.files)
        for name in a.files:
            one, two = a[name], b[name]
            assert (one.dtype, one.shape, one.tobytes()) == (two.dtype, two.shape, two.tobytes()), name


root = Path.cwd()
run = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
launch = sys.argv[3]
report = read(run / 'case.json')
environment = read(run / 'environment.json')
case = ParityCase(**report['case'])
assert case in required_cases() and case == ParityCase('silent', 1000, 0)
experiment = EXPERIMENTS[case.experiment]
assert report['case_accepted'] and not report['full_matrix_accepted'] and not report['scientific_review_required']
assert len(report['metric_acceptance']['checks']) == 11
assert all(report['case_checks'].values()) and all(report['metric_acceptance']['checks'].values())
assert environment['MLX_ENABLE_TF32'] == '0' and environment['compilation'] == 'disabled'
assert environment['cpu_threads'] == 1 and environment['cpu_default_dtype'] == 'torch.float32'
assert environment['versions']['brian2'] == '2.8.0'
for module, digest in environment['source_sha256'].items():
    base = Path('src').joinpath(*module.split('.'))
    path = base.with_suffix('.py') if base.with_suffix('.py').is_file() else base / '__init__.py'
    assert sha((root / path).read_bytes()) == digest
    assert sha(subprocess.check_output(['git', 'show', launch + ':' + str(path)])) == digest

connectome, pin = pinned_inputs(root)
assert asdict(pin) == report['input_pins'] and (pin.neurons, pin.edges) == (138639, 15091983)
assert sha(connectome.neuron_ids.tobytes()) == report['neuron_mapping_sha256']
stimulus = generate(connectome, experiment, 1000, (case.trial,))
metadata = read(run / 'stimulus.json')
with np.load(run / 'stimulus.npz', allow_pickle=False) as saved:
    assert saved['events'].dtype == np.uint8 and saved['events'].shape == (1, 1000, len(experiment.activated_ids))
    assert saved['events'].tobytes() == stimulus.events.tobytes()
assert stimulus.sha256 == report['stimulus_sha256'] == metadata['canonical_event_sha256']
assert metadata['targets'] == list(stimulus.targets) and metadata['rates_hz'] == list(experiment.rates_hz)
assert metadata['activated_ids'] == list(experiment.activated_ids)
assert metadata['seed_tuples'] == [[20261004, experiment.generator_code, case.trial]] and metadata['silenced_ids'] == list(experiment.silenced_ids)
assert sha((run / 'stimulus.npz').read_bytes()) == metadata['artifact_sha256']
assert stimulus.events.shape == (1, 1000, 0) and not stimulus.targets
job = read(run / 'reference-job.json')
assert job['shape']['channels'] == 0 and job['shape']['pathway_edges'] == [pin.edges]

observations = run / 'observations'
for prefix, texts, arrays in (
    ('paired', ('phase-digests.jsonl', 'physical-digests.jsonl', 'reference-final-physical.json', 'causal.json'), ('reference-native.npz', 'mlx-native.npz', 'reference-final-physical.npz')),
    ('cpu', ('native-digests.jsonl',), ('native.npz',)),
):
    first, repeat = observations / (prefix + '-first'), observations / (prefix + '-repeat')
    for name in texts:
        assert (first / name).read_bytes() == (repeat / name).read_bytes(), name
    for name in arrays:
        equal_archives(first / name, repeat / name)
    records = [json.loads(line) for line in (first / texts[0]).read_text().splitlines()]
    if prefix == 'cpu':
        assert [row['step'] for row in records] == list(range(-1, 1000))
        assert all(len(row['native_sha256']) == 1 for row in records)
    else:
        assert [(row['begin'], row['rows']) for row in records] == [(step, min(32, 1000 - step)) for step in range(0, 1000, 32)]
        assert all(len(row['native_phase_sha256']) == 2 and len(row['mlx_queue_sha256']) == 1 and len(row['mlx_due_sha256']) == row['rows'] for row in records)
        physical = [json.loads(line) for line in (first / 'physical-digests.jsonl').read_text().splitlines()]
        assert [row['step'] for row in physical] == list(range(1001))
        cause = read(first / 'causal.json')
        assert cause['steps'] == 1000 and cause['first_budget_violation'] is None and cause['first_spike_step'] is None
        assert cause == report['causal']

paired = observations / 'paired-first'
pending_counts = []
with np.load(paired / 'mlx-native.npz', allow_pickle=False) as m, np.load(paired / 'reference-final-physical.npz', allow_pickle=False) as b:
    queue = m['queue']
    assert queue.dtype == np.bool_ and queue.shape == (19, 1, pin.edges)
    assert not queue[999 % 19].any()
    offset = b['reference_pathway_0_queue_0_offset']
    assert offset.dtype == np.int32 and offset.shape == () and int(offset) == 1000 % 19
    for future in range(1000, 1018):
        native_ids = b[f'reference_pathway_0_queue_0_slot_{(int(offset) + future - 999) % 19}']
        assert native_ids.dtype == np.int32 and native_ids.ndim == 1
        ids = set(map(int, native_ids))
        assert len(ids) == len(native_ids) and all(0 <= row < pin.edges for row in ids)
        assert ids == set(map(int, np.flatnonzero(queue[future % 19, 0])))
        pending_counts.append(len(ids))
assert pending_counts == report['final_pending_original_row_counts']

counts = {}
with np.load(run / 'normalized-spikes.npz', allow_pickle=False) as normalized:
    for engine, native in report['native_inputs_before_conversion'].items():
        with np.load(native['file'], allow_pickle=False) as actual:
            for name, record in native['arrays'].items():
                array = actual[name]
                assert record == {'dtype': array.dtype.str, 'shape': list(array.shape), 'sha256': sha(array.tobytes())}
            indices = actual['spike_i'] if engine == 'brian' else actual['spike_neurons']
            times = actual['spike_t'] if engine == 'brian' else actual['spike_steps']
            assert indices.dtype == (np.int32 if engine == 'brian' else np.int64)
            steps = np.rint(times / 0.0001).astype(np.int64) if engine == 'brian' else times
            assert times.dtype == (np.float64 if engine == 'brian' else np.int64)
            if engine == 'brian':
                assert np.array_equal(times, steps * 0.0001)
            if engine == 'torch':
                assert actual['spike_trials'].dtype == np.int64 and actual['spike_trials'].shape == indices.shape and not actual['spike_trials'].any()
            assert np.all((indices >= 0) & (indices < pin.neurons)) and np.all((steps >= 0) & (steps < 1000))
            assert len(set(zip(map(int, indices), map(int, steps), strict=True))) == len(steps)
            assert normalized[engine + '_neurons'].dtype == np.int64 and normalized[engine + '_steps'].dtype == np.int64
            assert np.array_equal(normalized[engine + '_neurons'], connectome.neuron_ids[indices])
            assert np.array_equal(normalized[engine + '_steps'], steps)
            counts[engine] = Counter(map(int, normalized[engine + '_neurons']))
            assert len(indices) == len(times) == 0
    assert np.array_equal(normalized['brian_neurons'], normalized['mlx_neurons'])
    assert np.array_equal(normalized['brian_steps'], normalized['mlx_steps'])

assert all(not value for value in counts.values())
assert pending_counts == [0] * 18
one = {'numerator': 1, 'denominator': 1, 'value': 1.0}
zero = {'numerator': 0, 'denominator': 1, 'value': 0.0}
expected = {
    'reference_spikes': 0, 'candidate_spikes': 0,
    'active_jaccard': one, 'count_error': zero, 'signed_count_ratio': None,
    'neuron_count_error': zero, 'rate_correlation': None, 'counts_equal': True,
    'timing_matches': 0, 'timing_f1': one, 'timing_precision': one,
    'timing_recall': one, 'exact_step_f1': one, 'one_step_f1': one,
    'mean_timing_error_ms': None, 'median_timing_error_ms': None,
    'shared_rate_correlation': None, 'common_rate_mae_hz': None,
    'common_rate_rmse_hz': None,
}
for engine in ('mlx', 'torch'):
    assert report['metric_acceptance'][engine] == expected, engine
independent = {'all_three_actual_native_rasters_are_empty': True, 'both_candidates_match_all_19_frozen_empty_metric_fields': True, 'expected_metrics': expected}

output.mkdir(parents=True, exist_ok=False)
paths = sorted(set(run.glob('*.json')) | set(run.glob('*.npz')) | set(observations.rglob('*.json')) | set(observations.rglob('*.jsonl')) | set(observations.rglob('*.npz')))
manifest = {str(path.relative_to(run)): sha(path.read_bytes()) for path in paths}
with zipfile.ZipFile(output / 'observations.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in paths:
        archive.write(path, str(path.relative_to(run)))
with zipfile.ZipFile(output / 'observations.zip') as archive:
    assert set(archive.namelist()) == set(manifest)
    assert all(sha(archive.read(name)) == digest for name, digest in manifest.items())
for name in ('case.json', 'normalized-spikes.npz', 'environment.json', 'stimulus.json', 'reference-job.json'):
    shutil.copyfile(run / name, output / name)
shutil.copyfile(__file__, output / 'executed-verification.py')
verification = {
    'execution_checkpoint': launch, 'parent_verification_checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'case_accepted': True, 'full_matrix_accepted': False, 'case': asdict(case), 'scope': 'Full pinned-connectome silent control, 1000 steps, trial 0; one of 52 required cases only.',
    'all_recorded_executed_sources_equal_launch_checkpoint_and_current_source': True,
    'pinned_inputs_mapping_and_regenerated_canonical_stimulus_verified': True,
    'empty_canonical_channel_geometry_and_actual_reference_pathways_verified': True,
    'every_native_phase_physical_queue_due_and_final_array_repeats': True,
    'complete_32_block_paired_1001_physical_and_1001_cpu_digest_coverage': True,
    'every_actual_final_pending_original_row_set_equal': True, 'pending_counts': pending_counts,
    'complete_raw_mapped_mlx_reference_spikes_exact': True, 'independently_verified_exact_silence_and_frozen_empty_metrics': independent,
    'archive_file_count': len(paths), 'archive_manifest_sha256': manifest, 'every_archive_file_matches_preserved_original': True,
}
with (output / 'verification.json').open('x') as destination:
    json.dump(verification, destination, indent=2, allow_nan=False)
print(json.dumps({'verified': True, 'metrics': independent, 'archived_files': len(paths)}), flush=True)
