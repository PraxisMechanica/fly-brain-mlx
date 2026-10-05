import hashlib
import importlib.util
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
from fly_brain.qualification.adapters.case_binding import (
    require_bound_files,
    require_cause_binding,
    scientific_files,
)
from fly_brain.qualification.adapters.case_replay import require_complete_replay
from fly_brain.qualification.adjudication import (
    CASE_CHECKS,
    FIRST_SPIKE_CHECK,
    METRIC_CHECKS,
    require_reviewable,
)
from fly_brain.qualification.causality import CausalAudit
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.rounding_review import require_rounding_prerequisites
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def read(path):
    return json.loads(path.read_text())


def sha(value):
    return hashlib.sha256(value).hexdigest()


def equal_archives(first, second):
    with (
        np.load(first, allow_pickle=False) as a,
        np.load(second, allow_pickle=False) as b,
    ):
        assert set(a.files) == set(b.files)
        for name in a.files:
            one, two = a[name], b[name]
            assert (one.dtype, one.shape, one.tobytes()) == (
                two.dtype,
                two.shape,
                two.tobytes(),
            ), name


root = Path.cwd()
run = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
launch = sys.argv[3]
review = Path(sys.argv[4]).resolve()
report = read(run / 'case.json')
environment = read(run / 'environment.json')
case = ParityCase(**report['case'])
assert case in required_cases() and case == ParityCase('sugar', 10000, 0)
horizon = case.steps
experiment = EXPERIMENTS[case.experiment]
assert (
    not report['case_accepted']
    and not report['full_matrix_accepted']
    and report['scientific_review_required']
)
audit = CausalAudit()
audit.step = report['causal']['steps']
audit.first_spike_step = report['causal']['first_spike_step']
audit.first_spike_neurons = tuple(report['causal']['first_spike_neurons'])
assert report['causal']['first_budget_violation'] is None
assert report['case_checks'] == {
    name: name != FIRST_SPIKE_CHECK for name in CASE_CHECKS
}
assert report['metric_acceptance']['checks'] == {
    name: name != 'timing_floor' for name in METRIC_CHECKS
}
try:
    require_reviewable(
        case, report['case_checks'], report['metric_acceptance']['checks'], audit
    )
except ValueError as error:
    assert str(error) == 'Review requires every frozen metric check'
else:
    raise AssertionError('A timing failure must be refused by the case acceptance gate')
review_hashes = require_cause_binding(run, review, case, audit, launch)
cause_step, cause_neurons = audit.first_spike_step, audit.first_spike_neurons
require_complete_replay(run, horizon)
assert (
    environment['MLX_ENABLE_TF32'] == '0' and environment['compilation'] == 'disabled'
)
assert (
    environment['cpu_threads'] == 1
    and environment['cpu_default_dtype'] == 'torch.float32'
)
assert environment['versions']['brian2'] == '2.8.0'
for module, digest in environment['source_sha256'].items():
    base = Path('src').joinpath(*module.split('.'))
    path = (
        base.with_suffix('.py')
        if base.with_suffix('.py').is_file()
        else base / '__init__.py'
    )
    assert sha((root / path).read_bytes()) == digest
    assert (
        sha(subprocess.check_output(['git', 'show', launch + ':' + str(path)]))
        == digest
    )

connectome, pin = pinned_inputs(root)
assert asdict(pin) == report['input_pins'] and (pin.neurons, pin.edges) == (
    138639,
    15091983,
)
assert sha(connectome.neuron_ids.tobytes()) == report['neuron_mapping_sha256']
stimulus = generate(connectome, experiment, horizon, (case.trial,))
metadata = read(run / 'stimulus.json')
with np.load(run / 'stimulus.npz', allow_pickle=False) as saved:
    assert saved['events'].dtype == np.uint8 and saved['events'].shape == (
        1,
        horizon,
        len(experiment.activated_ids),
    )
    assert saved['events'].tobytes() == stimulus.events.tobytes()
assert (
    stimulus.sha256 == report['stimulus_sha256'] == metadata['canonical_event_sha256']
)
assert metadata['targets'] == list(stimulus.targets) and metadata['rates_hz'] == list(
    experiment.rates_hz
)
assert metadata['activated_ids'] == list(experiment.activated_ids)
assert metadata['seed_tuples'] == [
    [20261004, experiment.generator_code, case.trial]
] and metadata['silenced_ids'] == list(experiment.silenced_ids)
assert sha((run / 'stimulus.npz').read_bytes()) == metadata['artifact_sha256']
if case.experiment == 'sugar-silenced':
    sugar = generate(connectome, EXPERIMENTS['sugar'], horizon, (case.trial,))
    assert stimulus.sha256 == sugar.sha256 and np.array_equal(
        stimulus.events, sugar.events
    )
    job = read(run / 'reference-job.json')
    weight_path = (
        run
        / 'observations'
        / 'paired-first'
        / 'reference-results'
        / job['files']['weights']
    )
    assert weight_path.stat().st_size == pin.edges * 8
    weights = np.memmap(weight_path, dtype=np.float64, mode='r', shape=(pin.edges,))
    silenced = np.flatnonzero(np.isin(connectome.neuron_ids, experiment.silenced_ids))
    outgoing = np.isin(connectome.sources, silenced)
    expected = connectome.counts * (0.275 * 0.001)
    expected[outgoing] = 0
    assert np.array_equal(weights, expected)
    assert sha(weights.tobytes()) == sha(expected.tobytes())
    assert sha(weight_path.read_bytes()) == sha(
        (
            run
            / 'observations'
            / 'paired-repeat'
            / 'reference-results'
            / job['files']['weights']
        ).read_bytes()
    )
    assert np.all(weights[outgoing] == 0)
    outgoing_count = int(outgoing.sum())
else:
    outgoing_count = None

observations = run / 'observations'
for prefix, texts, arrays in (
    (
        'paired',
        (
            'phase-digests.jsonl',
            'physical-digests.jsonl',
            'reference-final-physical.json',
            'causal.json',
        ),
        ('reference-native.npz', 'mlx-native.npz', 'reference-final-physical.npz'),
    ),
    ('cpu', ('native-digests.jsonl',), ('native.npz',)),
):
    first, repeat = (
        observations / (prefix + '-first'),
        observations / (prefix + '-repeat'),
    )
    for name in texts:
        assert (first / name).read_bytes() == (repeat / name).read_bytes(), name
    for name in arrays:
        equal_archives(first / name, repeat / name)
    records = [json.loads(line) for line in (first / texts[0]).read_text().splitlines()]
    if prefix == 'cpu':
        assert [row['step'] for row in records] == list(range(-1, horizon))
        assert all(len(row['native_sha256']) == 1 for row in records)
    else:
        assert [(row['begin'], row['rows']) for row in records] == [
            (step, min(32, horizon - step)) for step in range(0, horizon, 32)
        ]
        assert all(
            len(row['native_phase_sha256']) == 2
            and len(row['mlx_queue_sha256']) == 1
            and len(row['mlx_due_sha256']) == row['rows']
            for row in records
        )
        physical = [
            json.loads(line)
            for line in (first / 'physical-digests.jsonl').read_text().splitlines()
        ]
        assert [row['step'] for row in physical] == list(range(horizon + 1))
        cause = read(first / 'causal.json')
        assert (
            cause['steps'] == horizon
            and cause['first_budget_violation'] is None
            and cause['first_spike_step'] == cause_step
            and tuple(cause['first_spike_neurons']) == cause_neurons
        )
        assert cause == report['causal']

paired = observations / 'paired-first'
pending_counts = {'brian': [], 'mlx': []}
with (
    np.load(paired / 'mlx-native.npz', allow_pickle=False) as m,
    np.load(paired / 'reference-final-physical.npz', allow_pickle=False) as b,
    np.load(paired / 'reference-native.npz', allow_pickle=False) as r,
):
    queue = m['queue']
    assert (
        queue.dtype == np.bool_
        and queue.shape == (19, 1, pin.edges)
        and not queue[(horizon - 1) % 19].any()
    )
    offset = b['reference_pathway_0_queue_0_offset']
    assert (
        offset.dtype == np.int32 and offset.shape == () and int(offset) == horizon % 19
    )
    for engine, indices, times in (
        ('brian', r['spike_i'], np.rint(r['spike_t'] / 0.0001).astype(np.int64)),
        ('mlx', m['spike_neurons'], m['spike_steps']),
    ):
        for future in range(horizon, horizon + 18):
            active = np.zeros(pin.neurons, dtype=np.bool_)
            active[indices[times == future - 18]] = True
            expected = np.flatnonzero(active[connectome.sources])
            if engine == 'brian':
                actual = b[
                    f'reference_pathway_0_queue_0_slot_{(int(offset) + future - (horizon - 1)) % 19}'
                ]
                assert actual.dtype == np.int32 and actual.ndim == 1
            else:
                actual = np.flatnonzero(queue[future % 19, 0])
            assert len(set(map(int, actual))) == len(actual)
            assert np.array_equal(np.sort(actual), expected), (engine, future)
            pending_counts[engine].append(len(actual))
assert report['final_pending_original_row_counts'] is None

counts, spikes = {}, {}
expected_native = {
    'brian': paired / 'reference-native.npz',
    'mlx': paired / 'mlx-native.npz',
    'torch': observations / 'cpu-first/native.npz',
}
assert set(report['native_inputs_before_conversion']) == set(expected_native)
with np.load(run / 'normalized-spikes.npz', allow_pickle=False) as normalized:
    for engine, native in report['native_inputs_before_conversion'].items():
        assert Path(native['file']).resolve() == expected_native[engine]
        with np.load(native['file'], allow_pickle=False) as actual:
            for name, record in native['arrays'].items():
                array = actual[name]
                assert record == {
                    'dtype': array.dtype.str,
                    'shape': list(array.shape),
                    'sha256': sha(array.tobytes()),
                }
            indices = (
                actual['spike_i'] if engine == 'brian' else actual['spike_neurons']
            )
            times = actual['spike_t'] if engine == 'brian' else actual['spike_steps']
            assert indices.dtype == (np.int32 if engine == 'brian' else np.int64)
            steps = (
                np.rint(times / 0.0001).astype(np.int64) if engine == 'brian' else times
            )
            assert times.dtype == (np.float64 if engine == 'brian' else np.int64)
            if engine == 'brian':
                assert np.array_equal(times, steps * 0.0001)
            if engine == 'torch':
                assert (
                    actual['spike_trials'].dtype == np.int64
                    and actual['spike_trials'].shape == indices.shape
                    and not actual['spike_trials'].any()
                )
            assert np.all((indices >= 0) & (indices < pin.neurons)) and np.all(
                (steps >= 0) & (steps < horizon)
            )
            assert len(
                set(zip(map(int, indices), map(int, steps), strict=True))
            ) == len(steps)
            assert (
                normalized[engine + '_neurons'].dtype == np.int64
                and normalized[engine + '_steps'].dtype == np.int64
            )
            assert np.array_equal(
                normalized[engine + '_neurons'], connectome.neuron_ids[indices]
            )
            assert np.array_equal(normalized[engine + '_steps'], steps)
            counts[engine] = Counter(map(int, normalized[engine + '_neurons']))
            spikes[engine] = (
                normalized[engine + '_neurons'],
                normalized[engine + '_steps'],
            )
    assert len(spikes) == 3
reference_events = set(
    zip(map(int, spikes['brian'][0]), map(int, spikes['brian'][1]), strict=True)
)
mlx_events = set(
    zip(map(int, spikes['mlx'][0]), map(int, spikes['mlx'][1]), strict=True)
)
assert {event for event in reference_events if event[1] < cause_step} == {
    event for event in mlx_events if event[1] < cause_step
}
assert {
    event[0] for event in reference_events ^ mlx_events if event[1] == cause_step
} == {int(connectome.neuron_ids[index]) for index in cause_neurons}

score_path = root / 'docs/evidence/milestone-4/case-adjudication/independent-score.py'
spec = importlib.util.spec_from_file_location(
    'independent_reviewed_case_score', score_path
)
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)
score_proof = read(score_path.with_name('independent-score-verification.json'))
assert sha(score_path.read_bytes()) == score_proof['executed_program_sha256']
support = sorted(set().union(*counts.values()))
independent = {
    engine: scorer.score(
        ((spikes['brian'], spikes[engine]),), support, horizon * 0.0001
    )
    for engine in ('mlx', 'torch')
}
for engine in independent:
    scorer.verify_metrics(report['metric_acceptance'][engine], independent[engine])
checks = scorer.gates(independent['mlx'], independent['torch'])
assert checks == report['metric_acceptance']['checks']
assert checks == {name: name != 'timing_floor' for name in METRIC_CHECKS}
for engine, native in report['native_inputs_before_conversion'].items():
    with np.load(native['file'], allow_pickle=False) as arrays:
        assert all(
            arrays[name].dtype == (np.float64 if engine == 'brian' else np.float32)
            and np.isfinite(arrays[name]).all()
            for name in arrays.files
            if np.issubdtype(arrays[name].dtype, np.floating)
        ), engine

context = report['causal']['contexts']['spike']
assert report['causal']['contexts']['budget'] is None and context['neurons'] == list(
    cause_neurons
)
with np.load(paired / 'spike-context.npz', allow_pickle=False) as current:
    assert set(current.files) == set(context['arrays'])
    for name, descriptor in context['arrays'].items():
        value = current[name]
        assert descriptor == {
            'dtype': value.dtype.str,
            'shape': list(value.shape),
            'sha256': sha(value.tobytes()),
        }
        if np.issubdtype(value.dtype, np.floating):
            assert np.isfinite(value).all()
    reference_spikes = np.zeros(pin.neurons, dtype=np.bool_)
    reference_spikes[current['current_reference_spikes']] = True
    require_rounding_prerequisites(
        current['current_reference_pre_v'],
        current['current_mlx_pre_v'],
        current['current_reference_pre_not_refractory'],
        current['current_mlx_pre_not_refractory'],
        reference_spikes,
        current['current_mlx_spikes'],
        cause_neurons,
    )
    assert current['affected_neuron_ids'].dtype == np.int64 and current[
        'affected_neuron_ids'
    ].tolist() == [int(connectome.neuron_ids[index]) for index in cause_neurons]
    assert current['stimulus_targets'].dtype == np.int32 and current[
        'stimulus_targets'
    ].tolist() == list(stimulus.targets)
    for position, step in (('current', cause_step), ('previous', cause_step - 1)):
        assert np.array_equal(
            current[position + '_stimulus_bits'], stimulus.events[0, step]
        )
    assert {
        (step['position'], step['actual_snapshot']['step']) for step in context['steps']
    } == {('current', cause_step), ('previous', cause_step - 1)}

external_hashes = {
    str((review / name).relative_to(root)): digest
    for name, digest in review_hashes.items()
}
for name in (
    'astra-review.md',
    'parent-verification.json',
    'independent-score.py',
    'independent-score-verification.json',
):
    path = score_path.parent / name
    external_hashes[str(path.relative_to(root))] = sha(path.read_bytes())
for name, digest in external_hashes.items():
    assert sha(subprocess.check_output(['git', 'show', 'HEAD:' + name])) == digest
preflight = read(review / 'first-cause-preflight.json')
for name, digest in preflight['executed_source_sha256'].items():
    assert sha((root / name).read_bytes()) == digest
    assert sha(subprocess.check_output(['git', 'show', launch + ':' + name])) == digest
proof = read(review / 'parent-host-proof.json')
assert (
    proof['verified'] is True
    and proof['first_step'] == cause_step
    and proof['complete_affected_neurons'] == list(cause_neurons)
)
assert proof['program_sha256'] == review_hashes['executed-host-proof.py']
assert proof['archive_sha256'] == review_hashes['first-observation.zip']
for name, digest in proof['auxiliary_sha256'].items():
    assert sha((paired / 'reference-results' / name).read_bytes()) == digest
for name, digest in proof['additional_auxiliary_sha256'].items():
    assert sha((root / name).read_bytes()) == digest

paths = scientific_files(run)
manifest = {str(path.relative_to(run)): sha(path.read_bytes()) for path in paths}
require_bound_files(run, manifest, has_spike_context=True)
output.mkdir(parents=True, exist_ok=False)
with zipfile.ZipFile(
    output / 'observations.zip', 'x', compression=zipfile.ZIP_DEFLATED
) as archive:
    for path in paths:
        archive.write(path, str(path.relative_to(run)))
with zipfile.ZipFile(output / 'observations.zip') as archive:
    assert set(archive.namelist()) == set(manifest)
    assert all(sha(archive.read(name)) == digest for name, digest in manifest.items())
for name in (
    'case.json',
    'normalized-spikes.npz',
    'environment.json',
    'stimulus.json',
    'reference-job.json',
):
    shutil.copyfile(run / name, output / name)
shutil.copyfile(__file__, output / 'executed-verification.py')
verification = {
    'execution_checkpoint': launch,
    'parent_verification_checkpoint': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True
    ).strip(),
    'case_accepted': False,
    'all_11_metric_gates_pass': False,
    'failed_metric_checks': ['timing_floor'],
    'executed_verifier_sha256': sha(Path(__file__).read_bytes()),
    'full_matrix_accepted': False,
    'case': asdict(case),
    'scope': 'Independent archival proof of the completed failed one-second sugar case; complete native repeats, own queues and metrics are verified without granting acceptance.',
    'automatic_report_accepted': False,
    'original_report_and_scientific_review_requirement_preserved': True,
    'scientific_adjudication': 'The fixed timing floor fails. The explained first cause grants no exception, and the original rejection remains in force.',
    'first_spike_step': cause_step,
    'first_spike_neurons': list(cause_neurons),
    'completed_review_policy_and_parent_verification_sha256': external_hashes,
    'all_recorded_executed_sources_equal_launch_checkpoint_and_current_source': True,
    'pinned_inputs_mapping_and_regenerated_canonical_stimulus_verified': True,
    'actual_reference_outgoing_silenced_weights_verified_original_rows_retained': True
    if case.experiment == 'sugar-silenced'
    else None,
    'actual_reference_weight_sha256': sha(weights.tobytes())
    if case.experiment == 'sugar-silenced'
    else None,
    'outgoing_silenced_original_row_count': outgoing_count,
    'every_native_phase_physical_queue_due_and_final_array_repeats': True,
    'complete_native_phase_physical_queue_and_cpu_digest_coverage': True,
    'observation_coverage': {
        'horizon_steps': horizon,
        'paired_blocks': (horizon + 31) // 32,
        'reference_physical_snapshots': horizon + 1,
        'cpu_native_snapshots': horizon + 1,
    },
    'every_actual_final_pending_original_row_set_matches_its_own_spike_history': True,
    'cross_engine_pending_equality_after_first_difference': 'inapplicable',
    'pending_counts': pending_counts,
    'complete_common_prefix_raw_mapped_spikes_exact': True,
    'complete_first_difference_set_and_native_threshold_prerequisites_verified': True,
    'native_cause_descriptors_verified': len(context['arrays']),
    'all_19_metric_fields_and_11_gates_independently_verified': True,
    'independent_scorer_sha256': sha(score_path.read_bytes()),
    'metrics_by_independent_counter_fraction_statistics_and_dynamic_program': independent,
    'archive_file_count': len(paths),
    'archive_manifest_sha256': manifest,
    'every_archive_file_matches_preserved_original': True,
}
with (output / 'verification.json').open('x') as destination:
    json.dump(
        verification, destination, indent=2, default=scorer.encode, allow_nan=False
    )
print(
    json.dumps(
        {
            'failed_case_verified': True,
            'case_accepted': False,
            'metrics': independent,
            'archived_files': len(paths),
        },
        default=scorer.encode,
    ),
    flush=True,
)
