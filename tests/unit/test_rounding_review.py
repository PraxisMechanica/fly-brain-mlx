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
        'offset-predicate',
        'offset-nonfinite',
        'projection',
    ),
)
def test_near_threshold_state_alone_cannot_explain_a_first_spike(fault: str) -> None:
    reference = np.full(2, np.nextafter(-0.045, np.inf), dtype=np.float64)
    mlx = np.full(2, -45, dtype=np.float32)
    offset = np.zeros(2, dtype=np.float32)
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
        offset[0] = -1
    if fault == 'nonfinite':
        reference[0] = np.nan
    if fault == 'dtype':
        reference = cast(NDArray[np.float64], reference.astype(np.float32))
    if fault == 'shape':
        mlx = mlx.reshape(1, 2)
    if fault == 'offset-predicate':
        offset[0] = np.float32(1e-6)
    if fault == 'offset-nonfinite':
        offset[0] = np.nan
    if fault == 'projection':
        offset[0] = 1
    args = (
        reference,
        mlx,
        offset,
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


def test_offset_crossing_is_valid_when_projected_voltage_equals_threshold() -> None:
    reference = np.array([-0.045], dtype=np.float64)
    voltage = np.array([-45], dtype=np.float32)
    offset = np.array([1e-6], dtype=np.float32)
    available = np.array([True])
    require_rounding_prerequisites(
        reference,
        voltage,
        offset,
        available,
        available,
        np.array([False]),
        np.array([True]),
        (0,),
    )
