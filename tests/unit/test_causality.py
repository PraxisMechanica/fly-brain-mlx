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
