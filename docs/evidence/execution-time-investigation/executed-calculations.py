import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

root = Path('/Users/ocasta/Code/fly-brain')


def read(name):
    return json.loads((root / name).read_text())


matrix_source = root / 'src/fly_brain/qualification/matrix.py'
function = next(node for node in ast.parse(matrix_source.read_text()).body if isinstance(node, ast.FunctionDef))
long = ast.literal_eval(function.body[0].value)
configurations = []
for row in function.body[1].value.elts:
    experiment, horizons, trials = row.elts
    if isinstance(horizons, ast.Name):
        steps = long
    else:
        steps = long[:ast.literal_eval(horizons.slice.upper)]
    configurations.append((ast.literal_eval(experiment), steps, ast.literal_eval(trials)))
cases = [(experiment, horizon, trial) for experiment, horizons, trials in configurations for horizon in horizons for trial in range(trials)]
separate_steps = sum(horizon for _, horizon, _ in cases)
prefix_steps = sum((max(horizons) if experiment in ('sugar', 'p9') else sum(horizons)) * trials for experiment, horizons, trials in configurations)
assert len(cases) == len(set(cases)) == 52 and separate_steps == 1231000
assert prefix_steps == 1121000

cpu = read('docs/evidence/milestone-4/full-cpu-observer/cpu-observer.json')['modes']
reference = read('docs/evidence/milestone-4/full-reference-observer/reference-observer.json')['records']
assert reference['ordinary']['native'] == reference['observed']['native'] == reference['repeat']['native']
assert cpu['ordinary']['final'] == cpu['observed']['final'] == cpu['repeat']['final']
production = read('docs/evidence/milestone-3/production-sugar/simulation.json')
finished = read('docs/evidence/milestone-4/timing-remediation/review-decision.json')['existing_sugar_session']
stack = (root / 'docs/evidence/execution-time-investigation/p9-cpu-stack-sample.txt').read_text()
main_samples = int(re.search(r'(\d+) Thread_\d+\s+DispatchQueue_1: com.apple.main-thread', stack).group(1))
sparse_samples = int(re.search(r'(\d+) at::native::_sparse_csr_mm', stack).group(1))
assert (main_samples, sparse_samples) == (207, 183)

neurons, edges, slots, steps, block = 138639, 15091983, 19, 10000, 32
blocks = (steps + block - 1) // block
queue_bytes = slots * edges
record = {
    'scope': 'Read-only calculations from preserved evidence and source; no tests, simulations, benchmarks, or production changes.',
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'matrix': {
        'case_identities': len(cases),
        'separate_duration_steps_per_engine_before_repeats': separate_steps,
        'expressly_authorized_sugar_p9_prefix_steps_per_engine_before_repeats': prefix_steps,
        'avoided_steps': separate_steps - prefix_steps,
        'avoided_step_percent': 100 * (separate_steps - prefix_steps) / separate_steps,
        'repeats_per_engine': 2,
        'all_case_obligations_preserved': True,
        'prefix_collector_not_implemented_or_qualified': True,
    },
    'measured_seconds': {
        'complete_one_second_sugar_case': finished['elapsed_s'],
        'complete_one_second_sugar_case_minutes': finished['elapsed_s'] / 60,
        'cpu_proof': {name: row['execution_and_capture_s'] for name, row in cpu.items()},
        'cpu_observer_wrapper_increment_percent': 100 * (cpu['observed']['execution_and_capture_s'] / cpu['ordinary']['execution_and_capture_s'] - 1),
        'cpu_proof_limit': 'Both ordinary and observed modes already capture/check/hash state; their difference is not total observation overhead.',
        'reference_proof': {name: row['seconds'] for name, row in reference.items()},
        'reference_observed_to_ordinary_ratio': reference['observed']['seconds'] / reference['ordinary']['seconds'],
        'production_mlx_total': production['elapsed_s'],
        'production_mlx_warm': production['timings']['warm_simulation_s'],
        'reference_and_cpu_native_descriptor_repeat_agreement': True,
    },
    'short_cpu_sample': {
        'main_thread_samples': main_samples,
        'native_sparse_matmul_samples': sparse_samples,
        'native_sparse_matmul_sample_percent': 100 * sparse_samples / main_samples,
        'limit': 'One short snapshot of the P9 CPU phase, not a whole-run profile or a GPU profile.',
    },
    'one_second_one_trial_logical_volumes': {
        'neurons': neurons, 'original_edges': edges, 'steps': steps, 'queue_slots': slots, 'blocks': blocks,
        'dense_bool_queue_bytes': queue_bytes,
        'due_mask_bytes_hashed_on_host': edges * steps,
        'boundary_queue_bytes_hashed_on_host': queue_bytes * blocks,
        'two_dense_queue_selection_output_elements': 2 * queue_bytes * steps,
        'ledger_queue_slot_element_comparisons': queue_bytes * steps,
        'reference_phase_bytes_excluding_times_queues_events': neurons * (7 * 8 + 3) * steps,
        'reference_one_byte_boolean_field_write_calls': neurons * 3 * steps,
        'possible_source_spike_ring_bytes': neurons * slots,
        'source_ring_is_an_unapproved_representation_candidate': True,
        'limit': 'Logical volumes from source geometry, not measured copies, physical traffic, allocation, kernel time, or speedup.',
    },
    'source_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (
        matrix_source,
        root / 'src/fly_brain/simulation/backend/bucketed.py',
        root / 'src/fly_brain/qualification/adapters/mlx_observer.py',
        root / 'src/fly_brain/qualification/adapters/mlx_ledger.py',
        root / 'src/fly_brain/qualification/adapters/brian_observer.py',
        root / 'src/fly_brain/qualification/adapters/observer_stream.py',
        root / 'src/fly_brain/qualification/adapters/torch_reference.py',
        root / 'src/fly_brain/qualification/adapters/case_execution.py',
    )},
    'development_resumed': False,
    'completion_forecast_supported': False,
}
output = Path(__file__).with_name('calculations.json')
with output.open('x') as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps({key: record[key] for key in ('matrix', 'measured_seconds', 'short_cpu_sample', 'development_resumed')}, indent=2))
