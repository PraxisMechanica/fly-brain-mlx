from dataclasses import fields

import numpy as np
import pytest

from fly_brain.simulation.identifiers import (
    EdgeRows32,
    FlyWireIds64,
    NeuronRows32,
    PaddedEdgeRows32,
)
from fly_brain.simulation.models import (
    Connectome,
    DestinationBucket,
    DestinationGrouping,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('readonly', (False, True))
@pytest.mark.parametrize('empty', (False, True))
def test_connectome_and_edge_records_preserve_array_aliases_and_public_fields(
    readonly: bool, empty: bool
) -> None:
    neuron_ids = np.arange(6, dtype=np.int64)[::2]
    sources = np.array([1, 0, 2], dtype=np.int32)[::-1]
    destinations = np.array([2, 1, 2], dtype=np.int32)
    counts = np.array([3, -1, 0], dtype=np.int32)
    weights = counts.astype(np.float64) * 0.275
    edges = np.array([1, 0, 2], dtype=np.int32)
    inverse = np.array([1, 0, 2], dtype=np.int32)
    offsets = np.array([0, 0, 1, 3], dtype=np.int64)
    targets = np.array([1, 2], dtype=np.int32)
    padded = np.array([[1, -1], [0, 2]], dtype=np.int32)
    bucket_counts = np.array([[-1, 0], [3, 0]], dtype=np.float32)
    occupied = np.array([[True, False], [True, True]], dtype=np.bool_)
    if empty:
        neuron_ids, sources, destinations = (
            neuron_ids[:0],
            sources[:0],
            destinations[:0],
        )
        counts, weights, edges = counts[:0], weights[:0], edges[:0]
        inverse, offsets, targets = inverse[:0], offsets[:0], targets[:0]
        padded, bucket_counts, occupied = (
            padded[:0],
            bucket_counts[:0],
            occupied[:0],
        )
    arrays = (
        neuron_ids,
        sources,
        destinations,
        counts,
        weights,
        edges,
        inverse,
        offsets,
        targets,
        padded,
        bucket_counts,
        occupied,
    )
    for array in arrays:
        array.setflags(write=not readonly)
    connectome = Connectome(
        FlyWireIds64(neuron_ids),
        NeuronRows32(sources),
        NeuronRows32(destinations),
        counts,
        weights,
    )
    grouping = DestinationGrouping(EdgeRows32(edges), inverse, offsets)
    bucket = DestinationBucket(
        NeuronRows32(targets),
        PaddedEdgeRows32(padded),
        bucket_counts,
        occupied,
    )
    assert tuple(field.name for field in fields(connectome)) == (
        'neuron_ids',
        'sources',
        'destinations',
        'counts',
        'weights_mv',
    )
    assert tuple(field.name for field in fields(grouping)) == (
        'edge_ids',
        'inverse',
        'offsets',
    )
    assert tuple(field.name for field in fields(bucket)) == (
        'targets',
        'edge_ids',
        'counts',
        'occupied',
    )
    stored = (
        connectome.neuron_ids,
        connectome.sources,
        connectome.destinations,
        connectome.counts,
        connectome.weights_mv,
        grouping.edge_ids,
        grouping.inverse,
        grouping.offsets,
        bucket.targets,
        bucket.edge_ids,
        bucket.counts,
        bucket.occupied,
    )
    for value, original in zip(stored, arrays, strict=True):
        assert value is original
        assert (value.dtype, value.shape, value.strides, value.flags.writeable) == (
            original.dtype,
            original.shape,
            original.strides,
            original.flags.writeable,
        )
        assert value.tobytes(order='A') == original.tobytes(order='A')
