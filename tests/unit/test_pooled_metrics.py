from fractions import Fraction

import numpy as np
import pytest

from fly_brain.comparison.models import SpikeSteps
from fly_brain.comparison.pooling import measure_trials

pytestmark = pytest.mark.unit


def spikes(*steps: int) -> SpikeSteps:
    return SpikeSteps(
        np.ones(len(steps), dtype=np.int64), np.asarray(steps, dtype=np.int64)
    )


def test_exchanged_trials_cannot_create_matches_from_equal_pooled_counts() -> None:
    result = measure_trials(
        ((spikes(99), spikes()), (spikes(), spikes(99))),
        np.asarray([1], dtype=np.int64),
        0.1,
    )
    assert (result.counts_equal, result.timing_matches, result.timing_f1) == (
        True,
        0,
        Fraction(0),
    )


def test_adjacent_trial_endpoints_cannot_create_a_timing_match() -> None:
    result = measure_trials(
        ((spikes(999), spikes()), (spikes(), spikes(0))),
        np.asarray([1], dtype=np.int64),
        0.1,
    )
    assert result.one_step_f1 == 0 and result.timing_f1 == 0
