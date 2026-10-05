from typing import cast

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend.arrays import as_host, evaluate
from fly_brain.simulation.backend.bucketed import Layout


def reduction_inputs(
    layout: Layout, neurons: tuple[int, ...], reference_weights: NDArray[np.float64]
) -> dict[str, NDArray[np.generic]]:
    arrays: dict[str, NDArray[np.generic]] = {}
    for neuron in neurons:
        for bucket in layout.buckets:
            with mx.stream(mx.gpu):
                rows = np.flatnonzero(as_host(bucket.targets) == neuron)
                if not len(rows):
                    continue
                row = int(rows[0])
                values = (
                    bucket.edge_ids[row],
                    bucket.counts[row],
                    bucket.occupied[row],
                )
                evaluate(*values)
                edges = cast(NDArray[np.int32], as_host(values[0])).copy()
                counts = as_host(values[1]).copy()
                occupied = cast(NDArray[np.bool_], as_host(values[2])).copy()
            prefix = f'neuron_{neuron}_'
            arrays[prefix + 'actual_mlx_leaf_edges'] = edges
            arrays[prefix + 'actual_mlx_leaf_counts'] = counts
            arrays[prefix + 'actual_mlx_leaf_occupied'] = occupied
            arrays[prefix + 'reference_native_weight_si'] = reference_weights[
                edges[occupied]
            ].copy()
            break
        else:
            raise ValueError('Cause neuron is absent from the actual device layout')
    return arrays
