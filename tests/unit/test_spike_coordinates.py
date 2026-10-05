import numpy as np
import pytest

from fly_brain.comparison.acceptance import validate_coordinates
from fly_brain.comparison.models import SpikeSteps

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('events', ((), ((0, 0), (3, 99), (0, 1), (3, 98))))
def test_valid_coordinates_include_silence_and_every_horizon_boundary(
    events: tuple[tuple[int, int], ...],
) -> None:
    spikes = SpikeSteps(
        np.asarray([neuron for neuron, _ in events], dtype=np.int64),
        np.asarray([step for _, step in events], dtype=np.int64),
    )
    validate_coordinates(spikes, 4, 100)


@pytest.mark.parametrize(
    'neurons,steps',
    (
        ([-1], [0]),
        ([4], [0]),
        ([0], [-1]),
        ([0], [100]),
        ([0, 0], [1, 1]),
        ([0], [0, 1]),
        ([[0]], [0]),
    ),
)
def test_invalid_or_duplicate_coordinates_cannot_receive_a_parity_score(
    neurons: list[int], steps: list[int]
) -> None:
    spikes = SpikeSteps(
        np.asarray(neurons, dtype=np.int64), np.asarray(steps, dtype=np.int64)
    )
    with pytest.raises(ValueError):
        validate_coordinates(spikes, 4, 100)
