import numpy as np
import pytest

from fly_brain.comparison.diagnostics import time_bin_counts

pytestmark = pytest.mark.unit


def test_half_open_bins_preserve_boundary_events_and_trailing_zeros() -> None:
    steps = np.asarray([1000, 0, 9999, 999], dtype=np.int64)
    assert time_bin_counts(steps, 10000).tolist() == [2, 1, 0, 0, 0, 0, 0, 0, 0, 1]


@pytest.mark.parametrize('horizon', [1000, 10000, 100000])
def test_valid_silence_retains_every_prescribed_time_bin(horizon: int) -> None:
    result = time_bin_counts(np.asarray([], dtype=np.int64), horizon)
    assert result.dtype == np.int64 and result.tolist() == [0] * (horizon // 1000)


@pytest.mark.parametrize('step', [-1, 10000])
def test_invalid_steps_cannot_disappear_from_reported_bin_counts(step: int) -> None:
    with pytest.raises(ValueError, match='within the horizon'):
        time_bin_counts(np.asarray([step], dtype=np.int64), 10000)


@pytest.mark.parametrize('horizon', [0, 1001])
def test_unprescribed_bin_horizon_is_rejected(horizon: int) -> None:
    with pytest.raises(ValueError, match='complete 100 ms bins'):
        time_bin_counts(np.asarray([], dtype=np.int64), horizon)
