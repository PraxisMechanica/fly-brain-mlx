from collections.abc import Mapping

from .causality import CausalAudit
from .matrix import required_cases
from .models import ParityCase

CASE_CHECKS: frozenset[str] = frozenset(
    (
        'required_frozen_case',
        'full_connectome_geometry',
        'input_geometry_equals_pin',
        'canonical_stimulus_hash',
        'single_case_horizon_and_trial',
        'prescribed_seed_generator_targets_and_rates',
        'complete_common_history_budget_check',
        'first_different_spike_explicitly_none',
        'actual_final_pending_events_equal_when_history_is_common',
    )
)
METRIC_CHECKS: frozenset[str] = frozenset(
    (
        'silent_reference_exact',
        'activity_floor',
        'activity_paired',
        'count_floor',
        'count_paired',
        'neuron_count_floor',
        'neuron_count_paired',
        'correlation_floor_or_exact_counts',
        'correlation_paired',
        'timing_floor',
        'timing_paired',
    )
)
FIRST_SPIKE_CHECK = 'first_different_spike_explicitly_none'


def require_reviewable(
    case: ParityCase,
    checks: Mapping[str, bool],
    gates: Mapping[str, bool],
    audit: CausalAudit,
) -> None:
    if case not in required_cases():
        raise ValueError('Review requires a prescribed case')
    if frozenset(checks) != CASE_CHECKS or any(
        value is not (name != FIRST_SPIKE_CHECK) for name, value in checks.items()
    ):
        raise ValueError('Only the first-spike check can remain false')
    if frozenset(gates) != METRIC_CHECKS or any(
        value is not True for value in gates.values()
    ):
        raise ValueError('Review requires every frozen metric check')
    if audit.step != case.steps or audit.first_budget_violation is not None:
        raise ValueError('Review requires complete common-history budget coverage')
    if (
        audit.first_spike_step is None
        or not 0 <= audit.first_spike_step < case.steps
        or not audit.first_spike_neurons
    ):
        raise ValueError('Review requires an explicit first-spike cause')


def require_same_cause(
    case: ParityCase,
    audit: CausalAudit,
    reviewed_case: ParityCase,
    reviewed_step: int,
    reviewed_neurons: tuple[int, ...],
) -> None:
    if case != reviewed_case or (
        audit.first_spike_step,
        audit.first_spike_neurons,
    ) != (reviewed_step, reviewed_neurons):
        raise ValueError(
            'Reviewed decision must identify this exact case and first cause'
        )
