from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.rounding_review import require_rounding_prerequisites

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    'fault',
    (
        'none',
        'omitted',
        'predicate',
        'eligibility',
        'budget',
        'nonfinite',
        'dtype',
        'shape',
    ),
)
def test_near_threshold_state_alone_cannot_explain_a_first_spike(fault: str) -> None:
    reference = np.full(2, np.nextafter(-0.045, np.inf), dtype=np.float64)
    mlx = np.full(2, -45, dtype=np.float32)
    available = np.ones(2, dtype=np.bool_)
    mlx_available = available.copy()
    reference_spikes, mlx_spikes = available.copy(), ~available
    neurons = (0,) if fault == 'omitted' else (0, 1)
    if fault == 'predicate':
        reference_spikes[0] = False
    if fault == 'eligibility':
        mlx_available[0] = False
    if fault == 'budget':
        mlx[0] = -46
    if fault == 'nonfinite':
        reference[0] = np.nan
    if fault == 'dtype':
        reference = cast(NDArray[np.float64], reference.astype(np.float32))
    if fault == 'shape':
        mlx = mlx.reshape(1, 2)
    args = (
        reference,
        mlx,
        available,
        mlx_available,
        reference_spikes,
        mlx_spikes,
        neurons,
    )
    if fault == 'none':
        require_rounding_prerequisites(*args)
    else:
        with pytest.raises(ValueError):
            require_rounding_prerequisites(*args)
