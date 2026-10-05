import numpy as np
from numpy.typing import NDArray


def require_rounding_prerequisites(
    reference_si: NDArray[np.float64],
    mlx_mv: NDArray[np.float32],
    reference_available: NDArray[np.bool_],
    mlx_available: NDArray[np.bool_],
    reference_spikes: NDArray[np.bool_],
    mlx_spikes: NDArray[np.bool_],
    reviewed_neurons: tuple[int, ...],
) -> None:
    arrays = (
        reference_si,
        mlx_mv,
        reference_available,
        mlx_available,
        reference_spikes,
        mlx_spikes,
    )
    if reference_si.ndim != 1 or any(
        value.shape != reference_si.shape for value in arrays
    ):
        raise ValueError('Cause requires aligned native neuron arrays')
    if (
        reference_si.dtype != np.float64
        or mlx_mv.dtype != np.float32
        or any(value.dtype != np.bool_ for value in arrays[2:])
        or not np.isfinite(reference_si).all()
        or not np.isfinite(mlx_mv).all()
    ):
        raise ValueError('Cause requires finite native precision and Boolean masks')
    if not np.array_equal(reference_available, mlx_available):
        raise ValueError('Cause eligibility must agree')
    if not np.array_equal(
        reference_spikes, reference_available & (reference_si > -0.045)
    ) or not np.array_equal(mlx_spikes, mlx_available & (mlx_mv > -45)):
        raise ValueError('Cause spikes must match actual strict native predicates')
    changed = tuple(
        int(index) for index in np.flatnonzero(reference_spikes != mlx_spikes)
    )
    if not changed or changed != reviewed_neurons:
        raise ValueError('Review must explain the complete first-difference set')
    indices = list(changed)
    expected = reference_si[indices] * 1000
    actual = mlx_mv[indices].astype(np.float64)
    budget = 1e-3 + 1e-5 * np.abs(expected)
    if np.any(np.abs(actual - expected) > budget) or np.any(
        np.abs(expected + 45) > budget
    ):
        raise ValueError('Cause exceeds the unchanged rounding budget or margin')
