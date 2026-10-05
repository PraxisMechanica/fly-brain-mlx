import numpy as np
from numpy.typing import NDArray

TIME_BIN_STEPS = 1000


def time_bin_counts(spike_steps: NDArray[np.int64], horizon: int) -> NDArray[np.int64]:
    if horizon <= 0 or horizon % TIME_BIN_STEPS:
        raise ValueError('Diagnostic horizon requires complete 100 ms bins')
    if (
        spike_steps.dtype != np.int64
        or spike_steps.ndim != 1
        or np.any(spike_steps < 0)
        or np.any(spike_steps >= horizon)
    ):
        raise ValueError(
            'Bin coordinates require native int64 steps within the horizon'
        )
    return np.bincount(
        spike_steps // TIME_BIN_STEPS, minlength=horizon // TIME_BIN_STEPS
    )
