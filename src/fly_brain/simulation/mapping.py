import numpy as np
from numpy.typing import NDArray

from .models import Connectome, DestinationGrouping


def absolute_count_sums(connectome: Connectome) -> NDArray[np.int64]:
    sums = np.zeros(connectome.neuron_ids.size, dtype=np.int64)
    np.add.at(sums, connectome.destinations, np.abs(connectome.counts.astype(np.int64)))
    return sums


def group_destinations(connectome: Connectome) -> DestinationGrouping:
    order = np.argsort(connectome.destinations, kind='stable').astype(np.int32)
    inverse = np.empty_like(order)
    inverse[order] = np.arange(order.size, dtype=np.int32)
    degree = np.bincount(connectome.destinations, minlength=connectome.neuron_ids.size)
    offsets = np.concatenate((np.zeros(1, dtype=np.int64), np.cumsum(degree)))
    return DestinationGrouping(order, inverse, offsets)


def silence_sources(connectome: Connectome, silenced: tuple[int, ...]) -> Connectome:
    if any(index < 0 or index >= connectome.neuron_ids.size for index in silenced):
        raise ValueError('Silenced source index is outside the neuron ordering')
    mask = np.isin(connectome.sources, silenced)
    counts, weights = connectome.counts.copy(), connectome.weights_mv.copy()
    counts[mask], weights[mask] = 0, 0
    counts.setflags(write=False)
    weights.setflags(write=False)
    return Connectome(
        connectome.neuron_ids,
        connectome.sources,
        connectome.destinations,
        counts,
        weights,
    )
