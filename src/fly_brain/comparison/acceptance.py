from fractions import Fraction

import numpy as np
from numpy.typing import NDArray

from .models import ParityMetrics, SpikeSteps
from .service import pearson_or_none


def common_support(
    reference: SpikeSteps, mlx: SpikeSteps, torch: SpikeSteps
) -> NDArray[np.int64]:
    return np.unique(np.concatenate((reference.neurons, mlx.neurons, torch.neurons)))


def counts_on_support(
    spikes: SpikeSteps, support: NDArray[np.int64]
) -> NDArray[np.int64]:
    neurons, counts = np.unique(spikes.neurons, return_counts=True)
    lookup = {
        int(neuron): int(count) for neuron, count in zip(neurons, counts, strict=True)
    }
    return np.asarray(
        [lookup.get(int(neuron), 0) for neuron in support], dtype=np.int64
    )


def groups_by_neuron(spikes: SpikeSteps) -> dict[int, NDArray[np.int64]]:
    order = np.lexsort((spikes.steps, spikes.neurons))
    neurons = spikes.neurons[order]
    steps = spikes.steps[order]
    values, starts, counts = np.unique(neurons, return_index=True, return_counts=True)
    ends = starts + counts
    return {
        int(neuron): steps[int(begin) : int(end)]
        for neuron, begin, end in zip(values, starts, ends, strict=True)
    }


def match_steps(
    reference: dict[int, NDArray[np.int64]],
    candidate: dict[int, NDArray[np.int64]],
    window: int,
) -> list[int]:
    differences: list[int] = []
    for neuron in sorted(reference.keys() & candidate.keys()):
        first, second = reference[neuron], candidate[neuron]
        i = j = 0
        while i < len(first) and j < len(second):
            difference = int(second[j]) - int(first[i])
            if abs(difference) <= window:
                differences.append(abs(difference))
                i += 1
                j += 1
            elif difference > 0:
                i += 1
            else:
                j += 1
    return differences


def measure(
    reference: SpikeSteps,
    candidate: SpikeSteps,
    support: NDArray[np.int64],
    duration_s: float,
) -> ParityMetrics:
    first = counts_on_support(reference, support)
    second = counts_on_support(candidate, support)
    reference_spikes = len(reference.steps)
    candidate_spikes = len(candidate.steps)
    union = int(np.count_nonzero((first > 0) | (second > 0)))
    intersection = (first > 0) & (second > 0)
    count_difference = int(np.abs(first - second).sum())
    first_groups = groups_by_neuron(reference)
    second_groups = groups_by_neuron(candidate)
    differences = match_steps(first_groups, second_groups, 10)
    matches = len(differences)
    total = reference_spikes + candidate_spikes
    exact = len(match_steps(first_groups, second_groups, 0))
    one_step = len(match_steps(first_groups, second_groups, 1))
    common_errors = (second.astype(np.float64) - first) / duration_s
    if reference_spikes:
        count_error = Fraction(
            abs(candidate_spikes - reference_spikes), reference_spikes
        )
        neuron_count_error = Fraction(count_difference, reference_spikes)
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
