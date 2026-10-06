from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.causal_reduction import reduction_inputs
from fly_brain.simulation.backend.bucketed import prepare_observed
from fly_brain.simulation.mapping import silence_sources
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.metal]


@pytest.mark.parametrize('empty', (False, True))
def test_actual_device_leaf_order_counts_padding_and_native_weights_are_retained(
    precision: str, empty: bool
) -> None:
    case = fixture(empty)
    _, read_rows = prepare_observed(case.connectome, case.targets, (3,), precision)
    original = silence_sources(case.connectome, (3,))
    weights = original.counts * (0.275 * 0.001)
    arrays = reduction_inputs(read_rows, tuple(range(6)), weights)
    for neuron in range(6):
        prefix = f'neuron_{neuron}_'
        edges = cast(NDArray[np.int32], arrays[prefix + 'actual_mlx_leaf_edges'])
        occupied = cast(NDArray[np.bool_], arrays[prefix + 'actual_mlx_leaf_occupied'])
        assert edges.dtype == np.int32 and occupied.dtype == np.bool_
        assert arrays[prefix + 'actual_mlx_leaf_counts'].dtype == np.float32
        assert arrays[prefix + 'reference_native_weight_si'].dtype == np.float64
        ids = edges[occupied]
        assert np.array_equal(ids, np.flatnonzero(original.destinations == neuron))
        assert (
            arrays[prefix + 'actual_mlx_leaf_counts'][occupied].tobytes()
            == original.counts[ids].astype(np.float32).tobytes()
        )
        assert (
            arrays[prefix + 'reference_native_weight_si'].tobytes()
            == weights[ids].tobytes()
        )
        assert not np.any(occupied[edges == -1])
