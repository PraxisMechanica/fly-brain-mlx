from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from numpy.typing import NDArray

from fly_brain.simulation.inputs import file_sha256, load_connectome
from fly_brain.simulation.mapping import group_destinations, silence_sources
from fly_brain.simulation.models import InputPin

pytestmark = pytest.mark.integration


def inputs(
    path: Path, changed: dict[str, NDArray[np.int64]] | None = None
) -> tuple[Path, Path, InputPin]:
    completeness, connectivity = path / 'neurons.csv', path / 'connections.parquet'
    completeness.write_text(',Completed\n30,True\n10,True\n20,True\n')
    columns = {
        'Presynaptic_ID': np.array([30, 10, 20, 30], dtype=np.int64),
        'Postsynaptic_ID': np.array([20, 20, 30, 20], dtype=np.int64),
        'Presynaptic_Index': np.array([0, 1, 2, 0], dtype=np.int64),
        'Postsynaptic_Index': np.array([2, 2, 0, 2], dtype=np.int64),
        'Connectivity': np.array([3, 1, 0, 3], dtype=np.int64),
        'Excitatory': np.array([1, -1, 1, 1], dtype=np.int64),
        'Excitatory x Connectivity': np.array([3, -1, 0, 3], dtype=np.int64),
    }
    columns.update(changed or {})
    pq.write_table(pa.table(columns), connectivity)
    return (
        completeness,
        connectivity,
        InputPin(file_sha256(completeness), file_sha256(connectivity), 3, 4),
    )


def test_loading_preserves_file_order_direction_duplicates_and_zero_edges(
    tmp_path: Path,
) -> None:
    connectome = load_connectome(*inputs(tmp_path))
    assert connectome.neuron_ids.tolist() == [30, 10, 20]
    assert list(
        zip(
            connectome.sources,
            connectome.destinations,
            connectome.counts,
            strict=True,
        )
    ) == [(0, 2, 3), (1, 2, -1), (2, 0, 0), (0, 2, 3)]
    np.testing.assert_array_equal(
        connectome.weights_mv, np.array([3, -1, 0, 3], dtype=np.float64) * 0.275
    )


def test_destination_grouping_is_stable_and_reversible(tmp_path: Path) -> None:
    connectome = load_connectome(*inputs(tmp_path))
    grouping = group_destinations(connectome)
    assert grouping.edge_ids.tolist() == [2, 0, 1, 3]
    assert grouping.offsets.tolist() == [0, 1, 1, 4]
    np.testing.assert_array_equal(
        connectome.counts[grouping.edge_ids][grouping.inverse], connectome.counts
    )


def test_silencing_retains_edge_identity_and_only_changes_outgoing_weights(
    tmp_path: Path,
) -> None:
    original = load_connectome(*inputs(tmp_path))
    silenced = silence_sources(original, (0,))
    assert silenced.sources is original.sources
    assert silenced.destinations is original.destinations
    assert silenced.counts.tolist() == [0, -1, 0, 0]
    assert original.counts.tolist() == [3, -1, 0, 3]


def test_loading_rejects_a_changed_pinned_file(tmp_path: Path) -> None:
    completeness, connectivity, pin = inputs(tmp_path)
    completeness.write_text(',Completed\n10,True\n30,True\n20,True\n')
    with pytest.raises(ValueError, match='hash'):
        load_connectome(completeness, connectivity, pin)


@pytest.mark.parametrize(
    'column,values,message',
    [
        ('Presynaptic_ID', [10, 10, 20, 30], 'orientation'),
        ('Postsynaptic_ID', [30, 20, 30, 20], 'orientation'),
        ('Presynaptic_Index', [-1, 1, 2, 0], 'outside'),
        ('Postsynaptic_Index', [3, 2, 0, 2], 'outside'),
        ('Excitatory x Connectivity', [3, 1, 0, 3], 'Signed counts'),
        ('Connectivity', [2**24 + 1, 1, 0, 3], r'2\^24'),
        ('Excitatory', [0, -1, 1, 1], 'signs'),
    ],
)
def test_loading_rejects_inputs_that_break_mapping_or_arithmetic_guards(
    tmp_path: Path, column: str, values: list[int], message: str
) -> None:
    paths = inputs(tmp_path, {column: np.array(values, dtype=np.int64)})
    with pytest.raises(ValueError, match=message):
        load_connectome(*paths)
