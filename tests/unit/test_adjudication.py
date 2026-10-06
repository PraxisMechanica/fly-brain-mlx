from dataclasses import replace

import pytest

from fly_brain.qualification.adjudication import (
    CASE_CHECKS,
    FIRST_SPIKE_CHECK,
    METRIC_CHECKS,
    require_reviewable,
    require_same_cause,
)
from fly_brain.qualification.causality import BudgetViolation, CausalAudit
from fly_brain.qualification.models import ParityCase

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('failed_gate', (None, *sorted(METRIC_CHECKS)))
def test_explained_first_spike_cannot_waive_any_frozen_metric(
    failed_gate: str | None,
) -> None:
    case = ParityCase('sugar', 1000, 1)
    audit = CausalAudit(step=1000, first_spike_step=999, first_spike_neurons=(41514,))
    checks = {name: name != FIRST_SPIKE_CHECK for name in CASE_CHECKS}
    gates = {name: name != failed_gate for name in METRIC_CHECKS}
    if failed_gate is None:
        require_reviewable(case, checks, gates, audit)
    else:
        with pytest.raises(ValueError, match='every frozen metric'):
            require_reviewable(case, checks, gates, audit)


@pytest.mark.parametrize(
    'fault', ('none', 'experiment', 'horizon', 'trial', 'step', 'neuron', 'omitted')
)
def test_a_review_for_another_case_or_first_cause_cannot_grant_acceptance(
    fault: str,
) -> None:
    case = ParityCase('sugar', 1000, 1)
    audit = CausalAudit(step=1000, first_spike_step=999, first_spike_neurons=(41514,))
    reviewed = ParityCase(
        'p9' if fault == 'experiment' else 'sugar',
        10000 if fault == 'horizon' else 1000,
        0 if fault == 'trial' else 1,
    )
    step = 998 if fault == 'step' else 999
    neurons = () if fault == 'omitted' else (7,) if fault == 'neuron' else (41514,)
    if fault == 'none':
        require_same_cause(case, audit, reviewed, step, neurons)
    else:
        with pytest.raises(ValueError, match='this exact case and first cause'):
            require_same_cause(case, audit, reviewed, step, neurons)


@pytest.mark.parametrize('fault', (*sorted(CASE_CHECKS), 'missing', 'extra'))
def test_scientific_review_cannot_hide_a_changed_or_failed_validity_check(
    fault: str,
) -> None:
    case = ParityCase('sugar', 1000, 1)
    audit = CausalAudit(step=1000, first_spike_step=999, first_spike_neurons=(41514,))
    checks = {name: name != FIRST_SPIKE_CHECK for name in CASE_CHECKS}
    gates = dict.fromkeys(METRIC_CHECKS, True)
    if fault == 'missing':
        checks.pop('complete_common_history_budget_check')
    elif fault == 'extra':
        checks['another_check'] = True
    else:
        checks[fault] = not checks[fault]
    with pytest.raises(ValueError, match='Only the first-spike check'):
        require_reviewable(case, checks, gates, audit)


@pytest.mark.parametrize(
    'fault',
    (
        'missing_metric',
        'extra_metric',
        'budget',
        'truncated',
        'absent',
        'late',
        'empty',
        'unprescribed',
    ),
)
def test_review_requires_its_own_complete_valid_case_and_causal_audit(
    fault: str,
) -> None:
    case = ParityCase('sugar', 1000, 1)
    audit = CausalAudit(step=1000, first_spike_step=999, first_spike_neurons=(41514,))
    checks = {name: name != FIRST_SPIKE_CHECK for name in CASE_CHECKS}
    gates = dict.fromkeys(METRIC_CHECKS, True)
    if fault == 'missing_metric':
        gates.pop('count_paired')
    elif fault == 'extra_metric':
        gates['another_metric'] = True
    elif fault == 'budget':
        audit = replace(
            audit,
            first_budget_violation=BudgetViolation(
                999, 'pre', 'v', 1, -45, -46, 0.00145
            ),
        )
    elif fault == 'truncated':
        audit = replace(audit, step=999)
    elif fault == 'absent':
        audit = replace(audit, first_spike_step=None)
    elif fault == 'late':
        audit = replace(audit, first_spike_step=1000)
    elif fault == 'empty':
        audit = replace(audit, first_spike_neurons=())
    else:
        case = ParityCase('silent', 1000, 1)
    with pytest.raises(ValueError, match='Review requires'):
        require_reviewable(case, checks, gates, audit)
