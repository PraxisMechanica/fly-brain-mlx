import numpy as np
import pytest

from fly_brain.qualification.input_patterns import analyze_inputs
from fly_brain.simulation.models import Connectome
from tests.support.seeded_inputs import source_masks

pytestmark = pytest.mark.unit


def test_equal_selector_scores_use_the_lowest_neuron_indices() -> None:
    counts = np.ones(20, dtype=np.int32)
    indices = np.arange(20, dtype=np.int32)
    connectome = Connectome(
        np.arange(20, dtype=np.int64),
        indices,
        indices,
        counts,
        counts.astype(np.float64) * 0.275,
    )
    assert analyze_inputs(connectome).targets.tolist() == list(range(16))


def test_source_masks_keep_duplicate_edges_synchronized() -> None:
    sources = np.array([0, 0, 1, 2], dtype=np.int32)
    weights = np.array([2405, -2404, -1, 7], dtype=np.float64) * 0.275
    masks = source_masks(3, sources, weights)
    assert len(masks) == 70
    assert masks['positive-error'].tolist() == [True, True, False, False]
    for mask in masks.values():
        assert mask[0] == mask[1]


def test_error_extrema_cannot_choose_duplicate_edges_independently() -> None:
    counts = np.array([1, -1], dtype=np.int32)
    sources = np.zeros(2, dtype=np.int32)
    destinations = np.ones(2, dtype=np.int32)
    weights = counts.astype(np.float64) * 0.275
    connectome = Connectome(
        np.array([10, 20], dtype=np.int64), sources, destinations, counts, weights
    )
    patterns = analyze_inputs(connectome)
    assert patterns.positive_cast_error_mv[1] > 0
    assert patterns.negative_cast_error_mv[1] < 0
    assert patterns.positive_source_error_mv[1] == 0
    assert patterns.negative_source_error_mv[1] == 0


def test_seeded_masks_repeat_and_keep_source_identity_across_edge_order() -> None:
    sources = np.array([7, 3, 7, 2, 5, 3], dtype=np.int32)
    weights = np.array([1, 2, -3, 4, -5, 6], dtype=np.float64) * 0.275
    first = source_masks(17, sources, weights)
    repeated = source_masks(17, sources[::-1], weights[::-1])
    for name in first:
        np.testing.assert_array_equal(first[name], repeated[name][::-1])
