from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.mapping import absolute_count_sums
from fly_brain.simulation.models import Connectome


@dataclass(frozen=True)
class InputPatterns:
    degree: NDArray[np.int64]
    absolute_weight_mv: NDArray[np.float64]
    positive_cast_error_mv: NDArray[np.float64]
    negative_cast_error_mv: NDArray[np.float64]
    positive_source_error_mv: NDArray[np.float64]
    negative_source_error_mv: NDArray[np.float64]
    absolute_counts: NDArray[np.int64]
    targets: NDArray[np.int32]


def analyze_inputs(connectome: Connectome) -> InputPatterns:
    neurons = connectome.neuron_ids.size
    degree = np.bincount(connectome.destinations, minlength=neurons)
    error = connectome.weights_mv.astype(np.float32).astype(np.float64)
    error -= connectome.weights_mv
    absolute_weight = np.zeros(neurons, dtype=np.float64)
    positive_error = np.zeros(neurons, dtype=np.float64)
    negative_error = np.zeros(neurons, dtype=np.float64)
    np.add.at(absolute_weight, connectome.destinations, np.abs(connectome.weights_mv))
    np.add.at(positive_error, connectome.destinations, np.maximum(error, 0))
    np.add.at(negative_error, connectome.destinations, np.minimum(error, 0))
    order = np.lexsort((connectome.sources, connectome.destinations))
    sources, destinations = connectome.sources[order], connectome.destinations[order]
    start = np.concatenate(
        (
            np.array([True]),
            (sources[1:] != sources[:-1]) | (destinations[1:] != destinations[:-1]),
        )
    )
    boundaries = np.flatnonzero(start)
    group_error = np.add.reduceat(error[order], boundaries)
    positive_source = np.zeros(neurons, dtype=np.float64)
    negative_source = np.zeros(neurons, dtype=np.float64)
    np.add.at(positive_source, destinations[boundaries], np.maximum(group_error, 0))
    np.add.at(negative_source, destinations[boundaries], np.minimum(group_error, 0))
    indices = np.arange(neurons)
    selected: set[int] = set()
    for metric in (degree, absolute_weight, positive_source, -negative_source):
        selected.update(int(index) for index in np.lexsort((indices, -metric))[:16])
    for value in np.quantile(degree, [0, 0.5, 0.9, 0.99, 1], method='nearest'):
        selected.add(int(np.flatnonzero(degree == value)[0]))
    absolute_counts = absolute_count_sums(connectome)
    selected.add(int(np.argmax(absolute_counts)))
    return InputPatterns(
        degree,
        absolute_weight,
        positive_error,
        negative_error,
        positive_source,
        negative_source,
        absolute_counts,
        np.array(sorted(selected), dtype=np.int32),
    )


def source_masks(
    target: int, sources: NDArray[np.int32], weights: NDArray[np.float64]
) -> dict[str, NDArray[np.bool_]]:
    unique, inverse = np.unique(sources, return_inverse=True)
    group_weight = np.zeros(unique.size, dtype=np.float64)
    group_error = np.zeros(unique.size, dtype=np.float64)
    np.add.at(group_weight, inverse, weights)
    np.add.at(
        group_error, inverse, weights.astype(np.float32).astype(np.float64) - weights
    )
    masks = {
        'none': np.zeros(sources.size, dtype=np.bool_),
        'all': np.ones(sources.size, dtype=np.bool_),
        'positive-weight': (group_weight > 0)[inverse],
        'negative-weight': (group_weight < 0)[inverse],
        'positive-error': (group_error > 0)[inverse],
        'negative-error': (group_error < 0)[inverse],
    }
    for probability_index, probability in enumerate((0.001, 0.01, 0.1, 0.5)):
        for replicate in range(16):
            generator = np.random.Generator(
                np.random.PCG64(
                    np.random.SeedSequence(
                        [20261004, 783, target, probability_index, replicate]
                    )
                )
            )
            active = generator.random(unique.size) < probability
            masks[f'p{probability}-r{replicate:02}'] = active[inverse]
    return masks
