import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

root = Path.cwd()
checkpoint = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
case_names = ('p9', 'sugar-silenced', 'two-class', 'silent')
case_checks = {'required_frozen_case', 'full_connectome_geometry', 'input_geometry_equals_pin', 'canonical_stimulus_hash', 'single_case_horizon_and_trial', 'prescribed_seed_generator_targets_and_rates', 'complete_common_history_budget_check', 'first_different_spike_explicitly_none', 'actual_final_pending_events_equal_when_history_is_common'}
metric_checks = {'silent_reference_exact', 'activity_floor', 'activity_paired', 'count_floor', 'count_paired', 'neuron_count_floor', 'neuron_count_paired', 'correlation_floor_or_exact_counts', 'correlation_paired', 'timing_floor', 'timing_paired'}
for name in case_names:
    case = json.loads((root / f'docs/evidence/milestone-4/cases/{name}-1000-0/case.json').read_text())
    assert set(case['case_checks']) == case_checks and all(case['case_checks'].values())
    assert set(case['metric_acceptance']['checks']) == metric_checks and all(case['metric_acceptance']['checks'].values())
    assert case['case_accepted'] and not case['full_matrix_accepted']
historical = json.loads((root / 'docs/evidence/milestone-4/cases/sugar-1000-0/case.json').read_text())
assert historical['case_accepted'] and all(historical['case_checks'].values())
assert set(historical['metric_acceptance']['checks']) == metric_checks and all(historical['metric_acceptance']['checks'].values())
source = (root / 'src/fly_brain/qualification/adapters/case_report.py').read_text()
assert "'case_accepted': acceptance.accepted and all(checks.values())" in source
assert "'first_different_spike_explicitly_none': causal['first_spike_step'] is None" in source
contract = (root / 'docs/mlx-port-baseline.md').read_text()
assert 'This classification does not waive any full-network gate.' in contract
assert 'Final acceptance requires both this causal audit and every fixed/paired/repeatability gate.' in contract
context_path = root / 'docs/evidence/milestone-4/four-trial-memory/trial-1-spike-context.npz'
prior = json.loads((context_path.parent / 'astra-parent-verification.json').read_text())
with np.load(context_path, allow_pickle=False) as context:
    assert len(context.files) == 108
    reference = np.zeros(138639, dtype=np.bool_)
    reference[context['current_reference_spikes']] = True
    different = np.flatnonzero(reference != context['current_mlx_spikes'])
    assert different.tolist() == [prior['neuron']] == [41514]
    expected = float(context['current_reference_pre_v'][41514]) * 1000
    actual = float(context['current_mlx_pre_v'][41514])
    budget = 1e-3 + 1e-5 * abs(expected)
    assert expected > -45 and actual <= -45
    assert abs(expected - actual) <= budget and abs(expected + 45) <= budget
    assert context['current_reference_pre_not_refractory'][41514]
    assert context['current_mlx_pre_not_refractory'][41514]
    for label in ('current', 'previous'):
        assert set(map(int, context[label + '_reference_path_0_delivered'])) == set(map(int, context[label + '_mlx_due_edges']))
paths = [
    'AGENTS.md', 'docs/mlx-port-baseline.md', 'src/fly_brain/qualification/adapters/case_report.py',
    'src/fly_brain/comparison/acceptance.py', 'src/fly_brain/qualification/causality.py',
    'src/fly_brain/qualification/adapters/paired_observer.py', 'src/fly_brain/qualification/adapters/paired_causes.py',
    'src/fly_brain/qualification/adapters/replay_evidence.py',
    'docs/evidence/milestone-4/four-trial-memory/astra-review.md',
    'docs/evidence/milestone-4/four-trial-memory/astra-parent-verification.json',
    str(context_path.relative_to(root)),
]
result = {
    'parent_checkpoint': checkpoint, 'review_assignment_checkpoint': '361c748',
    'reviewer': '/root/review_case_adjudication', 'model': 'gpt-6-astra', 'reasoning_effort': 'xhigh',
    'decision': 'Use a separate parent-recorded decision tied to one complete execution; preserve original automatic report.',
    'confidence_percent': 99, 'only_permitted_false_case_check': 'first_different_spike_explicitly_none',
    'exact_case_check_names': sorted(case_checks), 'exact_metric_check_names': sorted(metric_checks),
    'complete_case_metrics_native_repeats_and_own_ledger_checks_remain_mandatory': True,
    'any_common_history_budget_failure_blocks_reviewed_acceptance': True,
    'prior_batch_first_difference_identity_and_local_rounding_prerequisites_rechecked': True,
    'singleton_accepted_by_this_review': False, 'full_matrix_accepted': False,
    'full_device_execution_rerun_for_policy_review': False,
    'existing_batch_classification_scope': 'Cause classification only; singleton requires its own complete metrics, replay, audit, and explicit parent applicability evidence.',
    'historical_sugar_report_preserved_with_its_original_explicit_checks': True,
    'schema_change': False, 'application_output_or_exit_contract_change': False,
    'inspected_source_and_prior_evidence_sha256': {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in paths},
}
output = root / 'data/results/milestone-4-adjudication-policy-verification-20261005-01.json'
with output.open('x') as destination:
    json.dump(result, destination, indent=2, allow_nan=False)
print(json.dumps({'verified_policy': True, 'accepted_cases_checked': len(case_names), 'case_checks': len(case_checks), 'metric_checks': len(metric_checks), 'first_difference_neurons': different.tolist(), 'error_mv': abs(expected-actual), 'budget_mv': budget}))
