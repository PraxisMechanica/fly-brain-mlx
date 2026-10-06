import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.ports import ReductionReader


def reduction_inputs(
    read_rows: ReductionReader,
    neurons: tuple[int, ...],
    reference_weights: NDArray[np.float64],
) -> dict[str, NDArray[np.generic]]:
    evidence = read_rows(neurons)
    if tuple(row.neuron for row in evidence.rows) != neurons:
        raise ValueError(
            'Actual device reduction rows differ from the requested coverage'
        )
    arrays: dict[str, NDArray[np.generic]] = {}
    for row in evidence.rows:
        prefix = f'neuron_{row.neuron}_'
        arrays[prefix + 'actual_mlx_leaf_edges'] = row.edges
        arrays[prefix + 'actual_mlx_leaf_counts'] = row.counts
        arrays[prefix + 'actual_mlx_leaf_occupied'] = row.occupied
        arrays[prefix + 'reference_native_weight_si'] = reference_weights[
            row.edges[row.occupied]
        ].copy()
    return arrays
