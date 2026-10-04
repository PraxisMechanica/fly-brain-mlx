import numpy as np
import pytest

from fly_brain.simulation.mapping import bucket_destinations, silence_sources
from fly_brain.simulation.models import Connectome

pytestmark = pytest.mark.unit


def connectome() -> Connectome:
    counts = np.array([3, 0, -3, 2, 1], dtype=np.int32)
    return Connectome(
        np.array([30, 10, 20], dtype=np.int64),
        np.array([1, 0, 0, 2, 0], dtype=np.int32),
        np.array([2, 1, 2, 2, 1], dtype=np.int32),
        counts,
        counts.astype(np.float64) * 0.275,
    )


def test_buckets_preserve_original_order_and_distinguish_padding_from_zero_edges() -> (
    None
):
    empty, pairs, padded = bucket_destinations(connectome())
    assert [bucket.edge_ids.shape[1] for bucket in (empty, pairs, padded)] == [1, 2, 4]
    assert empty.targets.tolist() == [0]
    assert empty.edge_ids.tolist() == [[-1]]
    assert not empty.occupied.any()
    assert pairs.edge_ids.tolist() == [[1, 4]]
    assert pairs.occupied.tolist() == [[True, True]]
    assert padded.edge_ids.tolist() == [[0, 2, 3, -1]]
    assert padded.counts.tolist() == [[3, -3, 2, 0]]
    assert padded.occupied.tolist() == [[True, True, True, False]]


def test_every_edge_has_exactly_one_destination_and_unchanged_signed_count() -> None:
    original = connectome()
    restored_counts = np.empty_like(original.counts)
    restored_targets = np.empty_like(original.destinations)
    edges: list[int] = []
    for bucket in bucket_destinations(original):
        identities = bucket.edge_ids[bucket.occupied]
        edges.extend(int(index) for index in identities)
        restored_counts[identities] = bucket.counts[bucket.occupied]
        targets = np.broadcast_to(bucket.targets[:, None], bucket.edge_ids.shape)
        restored_targets[identities] = targets[bucket.occupied]
    assert sorted(edges) == list(range(original.counts.size))
    np.testing.assert_array_equal(restored_counts, original.counts)
    np.testing.assert_array_equal(restored_targets, original.destinations)


def test_outgoing_silencing_retains_every_occupied_leaf_identity() -> None:
    original = connectome()
    silenced = silence_sources(original, (0,))
    for before, after in zip(
        bucket_destinations(original), bucket_destinations(silenced), strict=True
    ):
        np.testing.assert_array_equal(before.edge_ids, after.edge_ids)
        np.testing.assert_array_equal(before.occupied, after.occupied)
        identities = after.edge_ids[after.occupied]
        expected = np.where(
            original.sources[identities] == 0, 0, original.counts[identities]
        )
        np.testing.assert_array_equal(after.counts[after.occupied], expected)
