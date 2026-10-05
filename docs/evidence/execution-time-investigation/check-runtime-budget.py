import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/ocasta/Code/fly-brain')
BASE = ROOT / 'docs/evidence/execution-time-investigation'


def read(path):
    return json.loads((BASE / path).read_text())


cpu = read('cpu-multiply/result.json')
mlx = read('mlx-components/result.json')
writer = read('reference-writer/result.json')
active = read('active-source-rows/result.json')
steps = 10000
repeats = 2
blocks = (steps + 31) // 32
cpu_busy = cpu['patterns']['actual_busiest_saved_step']['measurements']
device = mlx['device_components']
host = mlx['host_components']
serialized = writer['measurements']
original_writer = serialized['original_tiny_boolean_writes_bytewise_crc']
fast_writer = serialized['buffered_booleans_native_zlib_crc']
budgets = {
    'original_cpu_multiply_two_runs_s': repeats * steps * cpu_busy['original_dense_times_csc']['median_s'],
    'explicit_sum_cpu_multiply_two_runs_s': repeats * steps * cpu_busy['csr_times_dense_explicit_sum']['median_s'],
    'active_source_busy_input_operation_two_runs_s': repeats * steps * active['patterns']['actual_busiest_saved_step']['median_s'],
    'mlx_production_step_two_runs_s': repeats * steps * device['unchanged_full_production_step']['median_total_s'],
    'mlx_observed_step_two_runs_s': repeats * steps * device['unchanged_full_observed_step']['median_total_s'],
    'mlx_due_host_scan_two_runs_s': repeats * steps * host['due_mask_hash_and_nonzero_scan']['median_s'],
    'mlx_queue_hash_boundaries_two_runs_s': repeats * blocks * host['complete_queue_hash']['median_s'],
    'mlx_phase_hash_boundaries_two_runs_s': repeats * blocks * host['native_phase_block_hash_including_tobytes']['median_s'],
    'reference_original_phase_writer_cpu_two_runs_s': repeats * steps / 32 * original_writer['median_producer_cpu_s'],
    'reference_fast_phase_writer_cpu_two_runs_s': repeats * steps / 32 * fast_writer['median_producer_cpu_s'],
    'reference_original_phase_pipe_probe_two_runs_s': repeats * steps / 32 * original_writer['median_wall_s'],
    'reference_fast_phase_pipe_probe_two_runs_s': repeats * steps / 32 * fast_writer['median_wall_s'],
}
mlx_dense_audit_s = sum(budgets[name] for name in ('mlx_observed_step_two_runs_s', 'mlx_due_host_scan_two_runs_s', 'mlx_queue_hash_boundaries_two_runs_s', 'mlx_phase_hash_boundaries_two_runs_s'))
coarse_original_accounting_s = budgets['original_cpu_multiply_two_runs_s'] + mlx_dense_audit_s + budgets['reference_original_phase_writer_cpu_two_runs_s']
record = {
    'scope': 'First-principles work counts and component extrapolation. None of these are a new measured complete one-second check or completion forecast.',
    'biological_seconds': 1, 'step_ms': 0.1, 'steps_per_engine_run': steps,
    'complete_check_engine_runs': 6, 'complete_check_total_engine_steps': 6 * steps,
    'neuron_steps_per_trial': cpu['neurons'] * steps,
    'full_edge_visits_per_trial': cpu['coalesced_csr_entries'] * steps,
    'reference_phase_payload_bytes_per_trial': cpu['neurons'] * steps * 59,
    'reference_single_byte_boolean_calls_per_trial': 3 * cpu['neurons'] * steps,
    'cpu_matrix_storage_bytes': read('cpu-multiply/verification.json')['matrix_storage_bytes'],
    'cpu_matrix_logical_bytes_for_two_full_scans_per_step': repeats * steps * read('cpu-multiply/verification.json')['matrix_storage_bytes'],
    'component_extrapolations_seconds': budgets,
    'component_extrapolations_minutes': {name.removesuffix('_s'): value / 60 for name, value in budgets.items()},
    'mlx_dense_audit_coarse_two_run_accounting_minutes': mlx_dense_audit_s / 60,
    'current_original_cpu_mlx_audit_writer_coarse_accounting_minutes': coarse_original_accounting_s / 60,
    'ordinary_one_run_screen_core_component_minutes': device['unchanged_full_production_step']['median_total_s'] * steps / 60,
    'retained_full_cpu_raster_active_edge_visits': active['retained_cpu_one_second_active_outgoing_edge_visits'],
    'retained_full_scan_to_active_edge_work_ratio': active['dense_full_scan_edge_visits_per_10000_steps'] / active['retained_cpu_one_second_active_outgoing_edge_visits'],
    'provisional_planning_budgets_minutes': {
        'one_candidate_spike_screen_with_current_uncompiled_mlx_and_verified_reference_spikes': [5, 8],
        'two_run_full_mlx_audit_after_immutable_reference_reuse_retaining_current_dense_checks': [30, 40],
    },
    'budget_conditions': 'Engineering budgets, not measured performance, statistical confidence intervals or delivery estimates. Screening rejects completed-horizon absolute failures only; it is not full acceptance. Reference reuse requires verified engine-specific provenance and complete raw common-prefix reference values or digest-verified replay; existing phase hashes alone are insufficient.',
    'limits': 'One preserved endpoint and selected component inputs cannot establish horizon-average costs. Producers/consumers overlap or wait, and memory/cache contention changes timings; extrapolated terms are not exclusive whole-run shares and their coarse sums are not exact wall-time attribution. Setup, remaining CPU state/capture, reference model/monitors, reference phase parsing/hashing, causal comparisons, output compression and broader workloads remain outside these terms. Do not project the 243-fold sparse-input component result onto the whole check.',
    'source_sha256': {str((BASE / p).relative_to(ROOT)): hashlib.sha256((BASE / p).read_bytes()).hexdigest() for p in ('cpu-multiply/result.json', 'cpu-multiply/verification.json', 'mlx-components/result.json', 'reference-writer/result.json', 'active-source-rows/result.json')},
}
with (BASE / 'check-runtime-budget.json').open('x') as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
    stream.write('\n')
print(json.dumps({'coarse_current_accounting_minutes': record['current_original_cpu_mlx_audit_writer_coarse_accounting_minutes'], 'coarse_two_run_mlx_audit_minutes': record['mlx_dense_audit_coarse_two_run_accounting_minutes'], 'screen_core_minutes': record['ordinary_one_run_screen_core_component_minutes'], 'scope': record['scope']}, indent=2))
