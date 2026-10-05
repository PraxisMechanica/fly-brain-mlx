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


def test_missing_trials_cannot_receive_perfect_empty_agreement() -> None:
    with pytest.raises(ValueError, match='Missing trials'):
        measure_trials((), np.asarray([], dtype=np.int64), 0.1)


def test_valid_empty_trials_keep_exact_silence_and_unavailable_rates() -> None:
    result = measure_trials(
        ((spikes(), spikes()), (spikes(), spikes())),
        np.asarray([], dtype=np.int64),
        0.1,
    )
    assert (result.active_jaccard, result.timing_f1, result.count_error) == (1, 1, 0)
    assert result.rate_correlation is None and result.common_rate_mae_hz is None


def test_added_spikes_against_silence_keep_normalized_errors_undefined() -> None:
    result = measure_trials(
        ((spikes(), spikes(1)),), np.asarray([1], dtype=np.int64), 0.1
    )
    assert (
        result.count_error,
        result.neuron_count_error,
        result.signed_count_ratio,
    ) == (None, None, None)
    assert result.timing_f1 == 0 and not result.counts_equal


def test_silent_trial_contributes_rate_exposure_and_cpu_only_support_is_retained() -> (
    None
):
    result = measure_trials(
        ((spikes(1), spikes(1, 30)), (spikes(), spikes())),
        np.asarray([1, 9], dtype=np.int64),
        0.1,
    )
    assert result.common_rate_mae_hz == 2.5
    assert result.common_rate_rmse_hz == pytest.approx(5 / np.sqrt(2))


def test_pooled_timing_f1_uses_event_totals_instead_of_average_trial_scores() -> None:
    result = measure_trials(
        ((spikes(1, 20, 40), spikes(1, 20, 40)), (spikes(70), spikes())),
        np.asarray([1], dtype=np.int64),
        0.1,
    )
    assert (result.timing_f1, result.timing_precision, result.timing_recall) == (
        Fraction(6, 7),
        1,
        Fraction(3, 4),
    )


def test_pooled_timing_errors_use_all_matched_events_instead_of_trial_means() -> None:
    result = measure_trials(
        ((spikes(1, 20, 40), spikes(1, 20, 40)), (spikes(70), spikes(80))),
        np.asarray([1], dtype=np.int64),
        0.1,
    )
    assert (result.mean_timing_error_ms, result.median_timing_error_ms) == (0.25, 0.0)


def test_exact_and_one_step_windows_are_matched_independently() -> None:
    result = measure_trials(
        ((spikes(0, 2), spikes(2)),), np.asarray([1], dtype=np.int64), 0.1
    )
    assert (result.exact_step_f1, result.one_step_f1, result.mean_timing_error_ms) == (
        Fraction(2, 3),
        Fraction(2, 3),
        0.2,
    )


def test_within_trial_timing_can_match_across_a_count_bin_boundary() -> None:
    result = measure_trials(
        ((spikes(999), spikes(1000)),), np.asarray([1], dtype=np.int64), 1.0
    )
    assert result.one_step_f1 == 1 and result.timing_f1 == 1
