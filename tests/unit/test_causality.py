import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.causality import CausalAudit

pytestmark = pytest.mark.unit


def fields() -> dict[str, NDArray[np.float64]]:
    return {
        phase + '_' + field: np.zeros(3, dtype=np.float64)
        for phase in ('pre', 'before', 'end')
        for field in ('v', 'g')
    }


@pytest.mark.parametrize('phase', ('pre', 'before', 'end'))
def test_every_neuron_and_phase_is_checked_while_spike_history_is_common(
    phase: str,
) -> None:
    reference, mlx = fields(), fields()
    mlx[phase + '_g'][2] = 0.00101
    spikes = np.zeros(3, dtype=np.bool_)
    audit = CausalAudit()
    audit.check(0, reference, mlx, spikes, spikes)
    failure = audit.first_budget_violation
    assert failure is not None and (
        failure.step,
        failure.phase,
        failure.field,
        failure.neuron,
    ) == (0, phase, 'g', 2)


@pytest.mark.parametrize('pre_violation', (False, True))
def test_first_different_spikes_keep_pre_state_in_scope_and_later_state_out_of_scope(
    pre_violation: bool,
) -> None:
    reference, mlx = fields(), fields()
    quiet = np.zeros(3, dtype=np.bool_)
    different = np.array([False, True, False])
    audit = CausalAudit()
    audit.check(0, reference, mlx, quiet, quiet)
    mlx['pre_v'][2] = 0.00101 if pre_violation else 0.001
    mlx['before_v'][:] = mlx['end_v'][:] = 100
    audit.check(1, reference, mlx, quiet, different)
    mlx['pre_g'][:] = 100
    audit.check(2, reference, mlx, quiet, quiet)
    assert (audit.first_spike_step, audit.first_spike_neurons) == (1, (1,))
    failure = audit.first_budget_violation
    assert (failure is not None) is pre_violation
    if failure is not None:
        assert (failure.step, failure.phase, failure.field, failure.neuron) == (
            1,
            'pre',
            'v',
            2,
        )


@pytest.mark.parametrize('over', (False, True))
def test_trajectory_budget_is_inclusive_without_extra_comparison_slack(
    over: bool,
) -> None:
    reference, mlx = fields(), fields()
    mlx['end_g'][0] = np.nextafter(0.001, np.inf) if over else 0.001
    quiet = np.zeros(3, dtype=np.bool_)
    audit = CausalAudit()
    audit.check(0, reference, mlx, quiet, quiet)
    assert (audit.first_budget_violation is not None) is over


def test_earliest_phase_error_is_retained_instead_of_the_largest_later_error() -> None:
    reference, mlx = fields(), fields()
    mlx['pre_v'][2] = 0.002
    mlx['pre_g'][0] = mlx['before_v'][0] = 100
    quiet = np.zeros(3, dtype=np.bool_)
    audit = CausalAudit()
    audit.check(0, reference, mlx, quiet, quiet)
    mlx['pre_v'][0] = 100
    audit.check(1, reference, mlx, quiet, quiet)
    failure = audit.first_budget_violation
    assert failure is not None and (
        failure.step,
        failure.phase,
        failure.field,
        failure.neuron,
    ) == (0, 'pre', 'v', 2)


@pytest.mark.parametrize('phase', ('pre', 'before', 'end'))
def test_nonfinite_state_still_fails_after_spike_history_differs(phase: str) -> None:
    reference, mlx = fields(), fields()
    quiet = np.zeros(3, dtype=np.bool_)
    audit = CausalAudit()
    audit.check(0, reference, mlx, quiet, ~quiet)
    mlx[phase + '_g'][2] = np.nan
    with pytest.raises(ValueError, match='finite'):
        audit.check(1, reference, mlx, quiet, quiet)


def test_a_missing_step_cannot_hide_the_first_cause() -> None:
    quiet = np.zeros(3, dtype=np.bool_)
    with pytest.raises(ValueError, match='consecutive'):
        CausalAudit().check(1, fields(), fields(), quiet, quiet)


@pytest.mark.parametrize('reference_mv', (-100.0, 100.0))
def test_relative_state_budget_applies_to_both_signs(reference_mv: float) -> None:
    reference, mlx = fields(), fields()
    reference['pre_g'][:] = mlx['pre_g'][:] = reference_mv
    mlx['pre_g'][2] += 0.0015
    quiet = np.zeros(3, dtype=np.bool_)
    audit = CausalAudit()
    audit.check(0, reference, mlx, quiet, quiet)
    assert audit.first_budget_violation is None
