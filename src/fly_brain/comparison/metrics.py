from collections import defaultdict

import numpy as np
from numpy.typing import NDArray

from .models import (
    ComparisonRequest,
    ComparisonResult,
    Metrics,
    MetricValue,
    Spikes,
)


def prepare_metrics(spikes: Spikes, duration_s: float, trials: int) -> Metrics:
    neurons, counts = np.unique(spikes.neuron_ids, return_counts=True)
    rates = {
        int(neuron): float(count / (duration_s * trials))
        for neuron, count in zip(neurons, counts, strict=True)
    }
    grouped: dict[tuple[int, int], list[float]] = defaultdict(list)
    for trial, neuron, time in zip(
        spikes.trials, spikes.neuron_ids, spikes.time_s, strict=True
    ):
        grouped[int(trial), int(neuron)].append(float(time))
    groups = {
        key: np.sort(np.asarray(times, dtype=np.float64))
        for key, times in grouped.items()
    }
    return Metrics(rates, set(rates), groups, len(spikes.time_s))


def pearson_or_none(a: NDArray[np.float64], b: NDArray[np.float64]) -> float | None:
    if len(a) < 2:
        return None
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def count_timing_matches(
    times_a: NDArray[np.float64], times_b: NDArray[np.float64], tolerance_s: float
) -> tuple[int, list[float]]:
    """Greedy one-to-one spike matching within tolerance."""
    i = 0
    j = 0
    matches = 0
    diffs: list[float] = []
    while i < len(times_a) and j < len(times_b):
        diff = times_b[j] - times_a[i]
        if abs(diff) <= tolerance_s:
            matches += 1
            diffs.append(float(abs(diff)))
            i += 1
            j += 1
        elif times_a[i] < times_b[j]:
            i += 1
        else:
            j += 1
    return matches, diffs


def compare_pair(
    key_a: str,
    data_a: Metrics,
    key_b: str,
    data_b: Metrics,
    t_run: float,
    n_run: int,
    tolerance_ms: float,
) -> dict[str, MetricValue]:
    rates_a = data_a.rates
    rates_b = data_b.rates

    active_a = data_a.active
    active_b = data_b.active
    active_union = active_a | active_b
    active_shared = active_a & active_b

    jaccard = len(active_shared) / len(active_union) if active_union else 0.0
    precision = len(active_shared) / len(active_b) if active_b else 0.0
    recall = len(active_shared) / len(active_a) if active_a else 0.0

    if active_shared:
        shared_ids = sorted(active_shared)
        rate_a = np.array([rates_a[n] for n in shared_ids], dtype=np.float64)
        rate_b = np.array([rates_b[n] for n in shared_ids], dtype=np.float64)
        rate_corr = pearson_or_none(rate_a, rate_b)
        rate_rmse = float(np.sqrt(np.mean((rate_a - rate_b) ** 2)))
        rate_mae = float(np.mean(np.abs(rate_a - rate_b)))
    else:
        rate_corr = None
        rate_rmse = None
        rate_mae = None

    tolerance_s = tolerance_ms / 1000.0
    groups_a = data_a.groups
    groups_b = data_b.groups

    timing_matches = 0
    timing_diffs: list[float] = []
    for group_key in set(groups_a) & set(groups_b):
        matches, diffs = count_timing_matches(
            groups_a[group_key],
            groups_b[group_key],
            tolerance_s,
        )
        timing_matches += matches
        timing_diffs.extend(diffs)

    spikes_a = data_a.spikes
    spikes_b = data_b.spikes
    timing_f1 = (
        2.0 * timing_matches / (spikes_a + spikes_b) if (spikes_a + spikes_b) else 0.0
    )
    timing_precision = timing_matches / spikes_b if spikes_b else 0.0
    timing_recall = timing_matches / spikes_a if spikes_a else 0.0

    return {
        'framework_a': key_a,
        'framework_b': key_b,
        'backend_a': key_a,
        'backend_b': key_b,
        't_run': t_run,
        'n_run': n_run,
        'tolerance_ms': tolerance_ms,
        'spikes_a': int(spikes_a),
        'spikes_b': int(spikes_b),
        'spike_count_ratio_b_over_a': (
            round(spikes_b / spikes_a, 6) if spikes_a else None
        ),
        'active_a': int(len(active_a)),
        'active_b': int(len(active_b)),
        'active_shared': int(len(active_shared)),
        'active_jaccard': round(float(jaccard), 6),
        'active_precision_b_over_a': round(float(precision), 6),
        'active_recall_b_over_a': round(float(recall), 6),
        'rate_pearson_shared': (round(rate_corr, 8) if rate_corr is not None else None),
        'rate_rmse_hz_shared': (round(rate_rmse, 6) if rate_rmse is not None else None),
        'rate_mae_hz_shared': (round(rate_mae, 6) if rate_mae is not None else None),
        'timing_matches': int(timing_matches),
        'timing_f1': round(float(timing_f1), 8),
        'timing_precision_b_over_a': round(float(timing_precision), 8),
        'timing_recall_b_over_a': round(float(timing_recall), 8),
        'timing_mean_abs_dt_ms': (
            round(float(np.mean(timing_diffs) * 1000.0), 6) if timing_diffs else None
        ),
        'timing_median_abs_dt_ms': (
            round(float(np.median(timing_diffs) * 1000.0), 6) if timing_diffs else None
        ),
    }


def compare_metrics(
    request: ComparisonRequest, first: Metrics, second: Metrics
) -> ComparisonResult:
    summary = compare_pair(
        request.first_label,
        first,
        request.second_label,
        second,
        request.duration_s,
        request.trials,
        request.tolerance_ms,
    )
    rates: tuple[dict[str, MetricValue], ...] = tuple(
        {
            'backend_a': request.first_label,
            'framework_a': request.first_label,
            'backend_b': request.second_label,
            'framework_b': request.second_label,
            't_run': request.duration_s,
            'n_run': request.trials,
            'flywire_id': neuron,
            'rate_a_hz': first.rates.get(neuron, 0.0),
            'rate_b_hz': second.rates.get(neuron, 0.0),
        }
        for neuron in sorted(first.active | second.active)
    )
    return ComparisonResult(summary, rates)
