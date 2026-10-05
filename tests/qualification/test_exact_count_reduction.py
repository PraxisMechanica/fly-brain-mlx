import mlx.core as mx
import numpy as np
import pytest

from fly_brain.simulation.backend.arrays import as_host, boolean_input
from fly_brain.simulation.backend.bucketed import accumulate, make_layout
from fly_brain.simulation.models import Connectome

pytestmark = [pytest.mark.integration, pytest.mark.metal]


@pytest.mark.parametrize(
    'counts,eligible',
    [
        ((), True),
        ((0, 0), True),
        ((3, -3, 1, 1), True),
        ((2**24 - 1,), True),
        ((2**24,), True),
        ((2**23, -(2**23)), True),
        ((2**24, 1), False),
        ((-(2**24), -1), False),
    ],
)
def test_guarded_whole_layout_preserves_every_count_and_scaled_native_bit(
    precision: str,
    counts: tuple[int, ...],
    eligible: bool,
) -> None:
    integer_counts = np.asarray(counts, dtype=np.int32)
    connectome = Connectome(
        np.arange(2, dtype=np.int64),
        np.zeros(len(counts), dtype=np.int32),
        np.ones(len(counts), dtype=np.int32),
        integer_counts,
        integer_counts.astype(np.float64) * 0.275,
    )
    oracle = make_layout(connectome)
    candidate = make_layout(connectome, exact_counts=True)
    assert candidate.exact_counts is eligible
    events = np.ones((4, len(counts)), dtype=np.bool_)
    events[1] = False
    events[2, ::2] = False
    events[3, 1::2] = False
    initial = np.broadcast_to(
        np.array([0.0, -0.0, 1024.0, -1024.0], dtype=np.float32)[:, None], (4, 2)
    ).copy()
    with mx.stream(mx.gpu):
        accepted, state = boolean_input(events), mx.array(initial)
        original = accumulate(oracle, accepted, state)
        actual = accumulate(candidate, accepted, state)
        repeated = accumulate(candidate, accepted, state)
        for expected, observed, again in zip(original, actual, repeated, strict=True):
            a, b, c = as_host(expected), as_host(observed), as_host(again)
            assert (a.dtype, a.shape, a.tobytes()) == (b.dtype, b.shape, b.tobytes())
            assert b.tobytes() == c.tobytes()
        for trial in range(4):
            one = accumulate(
                candidate, accepted[trial : trial + 1], state[trial : trial + 1]
            )
            for batch, single in zip(actual, one, strict=True):
                assert (
                    as_host(batch[trial : trial + 1]).tobytes()
                    == as_host(single).tobytes()
                )


def test_accumulator_rejects_nonboolean_edge_membership(precision: str) -> None:
    counts = np.array([1], dtype=np.int32)
    connectome = Connectome(
        np.arange(2, dtype=np.int64), counts * 0, counts, counts, counts * 0.275
    )
    layout = make_layout(connectome, exact_counts=True)
    with mx.stream(mx.gpu), pytest.raises(ValueError, match='Boolean edges'):
        accumulate(layout, mx.ones((1, 1), dtype=mx.float32), mx.zeros((1, 2)))
