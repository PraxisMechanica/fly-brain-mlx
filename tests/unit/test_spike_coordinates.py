from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.comparison.acceptance import (
    steps_from_reference_clock,
    validate_coordinates,
)
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


@pytest.mark.parametrize('field', ('neurons', 'steps'))
@pytest.mark.parametrize('dtype', (np.int32, np.float64, np.bool_))
def test_coordinates_refuse_implicit_precision_conversion(
    field: str, dtype: type[np.int32] | type[np.float64] | type[np.bool_]
) -> None:
    wrong = cast(NDArray[np.int64], np.array([0], dtype=dtype))
    native = np.array([0], dtype=np.int64)
    spikes = SpikeSteps(
        wrong if field == 'neurons' else native, wrong if field == 'steps' else native
    )
    with pytest.raises(ValueError, match='native int64'):
        validate_coordinates(spikes, 4, 100)


@pytest.mark.parametrize('values', ((), (0, 1, 3, 773, 999)))
def test_reference_clock_normalization_preserves_exact_steps_and_silence(
    values: tuple[int, ...],
) -> None:
    expected = np.asarray(values, dtype=np.int64)
    actual = steps_from_reference_clock(expected * 0.0001, 1000)
    assert actual.dtype == np.int64 and np.array_equal(actual, expected)


@pytest.mark.parametrize('time', (float('nan'), float('inf'), -0.0001, 0.1, 0.00015))
def test_invalid_reference_times_cannot_be_rounded_into_valid_spikes(
    time: float,
) -> None:
    with pytest.raises(ValueError):
        steps_from_reference_clock(np.array([time], dtype=np.float64), 1000)
