from dataclasses import replace
from fractions import Fraction

import numpy as np
import pytest

from fly_brain.comparison.acceptance import apply_gates, evaluate_case
from fly_brain.comparison.models import ParityMetrics, SpikeSteps

pytestmark = pytest.mark.unit


def spikes(*events: tuple[int, int]) -> SpikeSteps:
    return SpikeSteps(
        np.asarray([neuron for neuron, _ in events], dtype=np.int64),
        np.asarray([step for _, step in events], dtype=np.int64),
    )


def exact_metrics() -> ParityMetrics:
    events = spikes((1, 10), (2, 20), (2, 50), (3, 90))
    return evaluate_case(events, events, events, 0.1).mlx


def test_all_fixed_and_paired_gates_accept_exact_ordinary_agreement() -> None:
    events = spikes((1, 10), (2, 20), (2, 50), (3, 90))
    assert evaluate_case(events, events, events, 0.1).accepted


@pytest.mark.parametrize(
    ('field', 'boundary', 'failure', 'check'),
    [
        (
            'active_jaccard',
            Fraction(19, 20),
            Fraction(19, 20) - Fraction(1, 1000000),
            'activity_floor',
        ),
        (
            'count_error',
            Fraction(1, 50),
            Fraction(1, 50) + Fraction(1, 1000000),
            'count_floor',
        ),
        (
            'neuron_count_error',
            Fraction(1, 20),
            Fraction(1, 20) + Fraction(1, 1000000),
            'neuron_count_floor',
        ),
        (
            'timing_f1',
            Fraction(19, 20),
            Fraction(19, 20) - Fraction(1, 1000000),
            'timing_floor',
        ),
    ],
)
def test_absolute_rational_gates_include_boundary_and_reject_one_count_beyond(
    field: str, boundary: Fraction, failure: Fraction, check: str
) -> None:
    exact = exact_metrics()
    assert apply_gates(replace(exact, **{field: boundary}), exact)[check]
    assert not apply_gates(replace(exact, **{field: failure}), exact)[check]


@pytest.mark.parametrize(
    ('field', 'worse', 'check'),
    [
        ('active_jaccard', Fraction(999999, 1000000), 'activity_paired'),
        ('count_error', Fraction(1, 1000000), 'count_paired'),
        ('neuron_count_error', Fraction(1, 1000000), 'neuron_count_paired'),
        ('timing_f1', Fraction(999999, 1000000), 'timing_paired'),
    ],
)
def test_no_spike_degradation_allowance_in_paired_rational_metrics(
    field: str, worse: Fraction, check: str
) -> None:
    exact = exact_metrics()
    assert not apply_gates(replace(exact, **{field: worse}), exact)[check]


def test_weak_torch_agreement_cannot_rescue_an_absolute_floor_failure() -> None:
    exact = exact_metrics()
    candidate = replace(exact, active_jaccard=Fraction(94, 100))
    torch = replace(exact, active_jaccard=Fraction(1, 2))
    checks = apply_gates(candidate, torch)
    assert checks['activity_paired'] and not all(checks.values())


def test_reference_silence_accepts_exact_mlx_even_if_torch_adds_spikes() -> None:
    assert evaluate_case(spikes(), spikes(), spikes((1, 1)), 0.1).accepted


def test_any_mlx_spike_fails_a_silent_reference() -> None:
    assert not evaluate_case(spikes(), spikes((1, 1)), spikes((1, 1)), 0.1).accepted


def test_empty_mlx_cannot_pass_a_nonempty_reference() -> None:
    assert not evaluate_case(spikes((1, 1)), spikes(), spikes(), 0.1).accepted


def test_undefined_correlation_requires_exact_full_count_vectors() -> None:
    reference = spikes((1, 1), (2, 1))
    candidate = spikes((1, 1), (1, 3), (2, 1), (2, 3))
    result = evaluate_case(reference, candidate, reference, 0.1)
    assert result.mlx.rate_correlation is None
    assert not result.checks['correlation_floor_or_exact_counts']


def test_equal_constant_vectors_satisfy_the_undefined_correlation_rule() -> None:
    events = spikes((1, 1), (2, 1))
    assert evaluate_case(events, events, events, 0.1).accepted


def test_undefined_torch_correlation_keeps_mlx_own_floor() -> None:
    exact = exact_metrics()
    checks = apply_gates(
        replace(exact, rate_correlation=0.98), replace(exact, rate_correlation=None)
    )
    assert (
        checks['correlation_paired'] and not checks['correlation_floor_or_exact_counts']
    )


@pytest.mark.parametrize(('degradation', 'passed'), [(0.5e-12, True), (2e-12, False)])
def test_paired_correlation_slack_is_bounded_to_host_evaluation(
    degradation: float, passed: bool
) -> None:
    exact = exact_metrics()
    candidate = replace(exact, rate_correlation=0.999 - degradation)
    torch = replace(exact, rate_correlation=0.999)
    assert apply_gates(candidate, torch)['correlation_paired'] is passed
