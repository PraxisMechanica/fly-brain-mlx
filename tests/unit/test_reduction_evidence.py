import numpy as np
import pytest

from fly_brain.qualification.adapters.causal_reduction import reduction_inputs
from fly_brain.simulation.observations import (
    COMPENSATED_ORDER,
    ReductionEvidence,
    ReductionRow,
)

pytestmark = pytest.mark.unit


def test_native_row_bits_are_detached_and_cannot_be_made_writable() -> None:
    edges = np.array([2, -1, 0], dtype=np.int32)
    counts = np.array([0x80000000, 0x7FC01234, 0x7F800000], dtype=np.uint32).view(
        np.float32
    )
    occupied = np.array([True, False, True], dtype=np.bool_)
    row = ReductionRow(3, edges, counts, occupied)
    original = tuple(value.tobytes() for value in (edges, counts, occupied))
    edges[:] = 0
    counts[:] = 1
    occupied[:] = False
    for value, expected in zip(
        (row.edges, row.counts, row.occupied), original, strict=True
    ):
        assert value.tobytes() == expected
        with pytest.raises(ValueError):
            value.setflags(write=True)


@pytest.mark.parametrize('size', (0, 1, 3))
def test_reduction_rows_reject_different_native_field_coverage(size: int) -> None:
    with pytest.raises(ValueError, match='equal native one-dimensional fields'):
        ReductionRow(
            0,
            np.array([0, 1], dtype=np.int32),
            np.zeros(size, dtype=np.float32),
            np.array([True, True], dtype=np.bool_),
        )


@pytest.mark.parametrize(
    'returned,requested',
    (((), (0,)), ((1,), (0,)), ((0, 1), (0,)), ((1, 0), (0, 1)), ((0, 0), (0,))),
)
def test_reader_rejects_missing_extra_or_reordered_neurons(
    returned: tuple[int, ...], requested: tuple[int, ...]
) -> None:
    rows = tuple(
        ReductionRow(
            neuron,
            np.array([], dtype=np.int32),
            np.array([], dtype=np.float32),
            np.array([], dtype=np.bool_),
        )
        for neuron in returned
    )

    def read(neurons: tuple[int, ...]) -> ReductionEvidence:
        return ReductionEvidence(rows, COMPENSATED_ORDER)

    with pytest.raises(ValueError, match='requested coverage'):
        reduction_inputs(read, requested, np.array([], dtype=np.float64))


def test_reader_binds_reference_weights_to_actual_occupied_edges() -> None:
    row = ReductionRow(
        3,
        np.array([2, -1, 0], dtype=np.int32),
        np.array([5, 0, -2], dtype=np.float32),
        np.array([True, False, True], dtype=np.bool_),
    )

    def read(neurons: tuple[int, ...]) -> ReductionEvidence:
        return ReductionEvidence((row,), COMPENSATED_ORDER)

    actual = reduction_inputs(read, (3,), np.array([2, 3, 4], dtype=np.float64))
    assert (
        actual['neuron_3_reference_native_weight_si'].tobytes()
        == np.array([4, 2], dtype=np.float64).tobytes()
    )
