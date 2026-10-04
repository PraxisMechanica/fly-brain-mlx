from fractions import Fraction

import numpy as np
import pytest

from fly_brain.comparison.acceptance import common_support, measure
from fly_brain.comparison.models import SpikeSteps

pytestmark = pytest.mark.unit


def spikes(*events: tuple[int, int]) -> SpikeSteps:
    return SpikeSteps(
        np.asarray([neuron for neuron, _ in events], dtype=np.int64),
        np.asarray([step for _, step in events], dtype=np.int64),
    )


def test_common_support_retains_neurons_unique_to_each_engine() -> None:
    result = common_support(spikes((10, 1)), spikes((20, 2)), spikes((30, 3)))
    assert result.tolist() == [10, 20, 30]


def test_primary_correlation_includes_missing_neurons_on_shared_three_engine_support() -> (
    None
):
    reference = spikes((1, 1), (1, 22), (2, 1))
    candidate = spikes((1, 11), (1, 32), (3, 1))
    support = common_support(reference, candidate, spikes((4, 1)))
    result = measure(reference, candidate, support, 0.1)
    assert result.rate_correlation == pytest.approx(7 / 11)
    assert result.shared_rate_correlation is None


def test_count_errors_keep_exact_ratios_and_include_absent_neurons() -> None:
    reference = spikes((1, 1), (1, 22), (2, 1))
    candidate = spikes((1, 11), (1, 32), (3, 1))
    result = measure(
        reference, candidate, common_support(reference, candidate, spikes()), 0.1
    )
    assert (result.active_jaccard, result.count_error, result.neuron_count_error) == (
        Fraction(1, 3),
        Fraction(0),
        Fraction(2, 3),
    )


def test_integer_matching_includes_ten_steps_and_never_reuses_or_crosses_neurons() -> (
    None
):
    reference = spikes((1, 100), (1, 101), (2, 100))
    candidate = spikes((1, 110), (3, 100))
    result = measure(
        reference, candidate, common_support(reference, candidate, spikes()), 0.1
    )
    assert (result.timing_matches, result.timing_f1, result.mean_timing_error_ms) == (
        1,
        Fraction(2, 5),
        1.0,
    )


def test_timing_diagnostics_use_distinct_zero_one_and_ten_step_windows() -> None:
    reference = spikes((1, 100), (2, 100), (3, 100))
    candidate = spikes((1, 100), (2, 101), (3, 110))
    result = measure(
        reference, candidate, common_support(reference, candidate, spikes()), 0.1
    )
    assert (result.exact_step_f1, result.one_step_f1, result.timing_f1) == (
        Fraction(1, 3),
        Fraction(2, 3),
        Fraction(1),
    )


def test_exact_silence_remains_agreement_when_torch_adds_a_spike() -> None:
    silent = spikes()
    result = measure(
        silent, silent, common_support(silent, silent, spikes((1, 1))), 0.1
    )
    assert (
        result.active_jaccard,
        result.timing_f1,
        result.count_error,
        result.neuron_count_error,
        result.counts_equal,
    ) == (Fraction(1), Fraction(1), Fraction(0), Fraction(0), True)
    assert result.rate_correlation is None


def test_empty_candidate_cannot_look_like_agreement_with_active_reference() -> None:
    reference = spikes((1, 1))
    candidate = spikes()
    result = measure(
        reference, candidate, common_support(reference, candidate, spikes()), 0.1
    )
    assert (
        result.active_jaccard,
        result.timing_f1,
        result.count_error,
        result.neuron_count_error,
    ) == (Fraction(0), Fraction(0), Fraction(1), Fraction(1))


def test_added_spike_to_silence_keeps_zero_denominator_explicit() -> None:
    reference = spikes()
    candidate = spikes((1, 1))
    result = measure(
        reference, candidate, common_support(reference, candidate, spikes()), 0.1
    )
    assert (
        result.count_error,
        result.neuron_count_error,
        result.signed_count_ratio,
        result.counts_equal,
    ) == (None, None, None, False)


def test_matching_is_independent_of_neuron_and_row_order() -> None:
    reference = spikes((2, 20), (1, 10), (2, 10))
    candidate = spikes((2, 10), (2, 20), (1, 10))
    result = measure(
        reference, candidate, common_support(reference, candidate, spikes()), 0.1
    )
    assert result.exact_step_f1 == 1
