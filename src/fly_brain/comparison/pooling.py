from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

from .acceptance import counts_on_support, groups_by_neuron, match_steps
from .models import ParityMetrics, SpikeSteps
from .service import pearson_or_none


def measure_trials(
    trials: tuple[tuple[SpikeSteps, SpikeSteps], ...],
    support: NDArray[np.int64],
    duration_s: float,
) -> ParityMetrics:
    if not trials:
        raise ValueError('Missing trials have unavailable pooled diagnostics')
    first: NDArray[np.int64] = np.stack(
        [counts_on_support(b, support) for b, _ in trials]
    ).sum(axis=0, dtype=np.int64)
    second: NDArray[np.int64] = np.stack(
        [counts_on_support(x, support) for _, x in trials]
    ).sum(axis=0, dtype=np.int64)
    reference_spikes, candidate_spikes = int(first.sum()), int(second.sum())
    union = int(np.count_nonzero((first > 0) | (second > 0)))
    intersection = (first > 0) & (second > 0)
    grouped = tuple((groups_by_neuron(b), groups_by_neuron(x)) for b, x in trials)
    differences = [value for b, x in grouped for value in match_steps(b, x, 10)]
    matches = len(differences)
    total = reference_spikes + candidate_spikes
    exact = sum(len(match_steps(b, x, 0)) for b, x in grouped)
    one_step = sum(len(match_steps(b, x, 1)) for b, x in grouped)
    common_errors = (second.astype(np.float64) - first) / (duration_s * len(trials))
    if reference_spikes:
        count_error = Fraction(
            abs(candidate_spikes - reference_spikes), reference_spikes
        )
        neuron_count_error = Fraction(
            int(np.abs(first - second).sum()), reference_spikes
        )
    else:
        count_error = neuron_count_error = None if candidate_spikes else Fraction(0)
    return ParityMetrics(
        reference_spikes=reference_spikes,
        candidate_spikes=candidate_spikes,
        active_jaccard=Fraction(int(intersection.sum()), union)
        if union
        else Fraction(1),
        count_error=count_error,
        signed_count_ratio=Fraction(candidate_spikes, reference_spikes)
        if reference_spikes
        else None,
        neuron_count_error=neuron_count_error,
        rate_correlation=pearson_or_none(
            first.astype(np.float64), second.astype(np.float64)
        ),
        counts_equal=bool(np.array_equal(first, second)),
        timing_matches=matches,
        timing_f1=Fraction(2 * matches, total) if total else Fraction(1),
        timing_precision=Fraction(matches, candidate_spikes)
        if candidate_spikes
        else Fraction(not reference_spikes),
        timing_recall=Fraction(matches, reference_spikes)
        if reference_spikes
        else Fraction(not candidate_spikes),
        exact_step_f1=Fraction(2 * exact, total) if total else Fraction(1),
        one_step_f1=Fraction(2 * one_step, total) if total else Fraction(1),
        mean_timing_error_ms=float(np.mean(differences) * 0.1) if differences else None,
        median_timing_error_ms=float(np.median(differences) * 0.1)
        if differences
        else None,
        shared_rate_correlation=pearson_or_none(
            first[intersection].astype(np.float64),
            second[intersection].astype(np.float64),
        ),
        common_rate_mae_hz=float(np.mean(np.abs(common_errors)))
        if support.size
        else None,
        common_rate_rmse_hz=float(np.sqrt(np.mean(common_errors**2)))
        if support.size
        else None,
    )
