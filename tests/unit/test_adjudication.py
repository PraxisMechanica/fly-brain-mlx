import pytest

from fly_brain.qualification.adjudication import (
    CASE_CHECKS,
    FIRST_SPIKE_CHECK,
    METRIC_CHECKS,
    require_reviewable,
)
from fly_brain.qualification.causality import CausalAudit
from fly_brain.qualification.models import ParityCase

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('failed_gate', (None, *sorted(METRIC_CHECKS)))
def test_explained_first_spike_cannot_waive_any_frozen_metric(
    failed_gate: str | None,
) -> None:
    case = ParityCase('sugar', 1000, 1)
    audit = CausalAudit()
    audit.step, audit.first_spike_step, audit.first_spike_neurons = 1000, 999, (41514,)
    checks = {name: name != FIRST_SPIKE_CHECK for name in CASE_CHECKS}
    gates = {name: name != failed_gate for name in METRIC_CHECKS}
    if failed_gate is None:
        require_reviewable(case, checks, gates, audit)
    else:
        with pytest.raises(ValueError, match='every frozen metric'):
            require_reviewable(case, checks, gates, audit)
