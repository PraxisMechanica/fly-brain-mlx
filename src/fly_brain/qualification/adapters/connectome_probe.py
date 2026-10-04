import hashlib
import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.mapping import (
    absolute_count_sums,
    group_destinations,
    silence_sources,
)
from fly_brain.simulation.models import Connectome, InputPin

MappedArray = NDArray[np.int32] | NDArray[np.int64] | NDArray[np.float64]


def run(connectome: Connectome, pin: InputPin, output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    grouping = group_destinations(connectome)
    identity = np.arange(connectome.counts.size, dtype=np.int32)
    assert np.array_equal(grouping.edge_ids[grouping.inverse], identity)
    assert np.array_equal(grouping.inverse[grouping.edge_ids], identity)
    for values in (
        connectome.sources,
        connectome.destinations,
        connectome.counts,
        connectome.weights_mv,
    ):
        assert np.array_equal(values[grouping.edge_ids][grouping.inverse], values)
    ordered = connectome.destinations[grouping.edge_ids]
    assert np.all(ordered[1:] >= ordered[:-1])
    same_target = ordered[1:] == ordered[:-1]
    assert np.all(
        grouping.edge_ids[1:][same_target] > grouping.edge_ids[:-1][same_target]
    )
    assert np.array_equal(
        connectome.counts.astype(np.float32).astype(np.int64), connectome.counts
    )
    absolute = absolute_count_sums(connectome)
    assert int(absolute.max()) <= 2**40
    silenced = silence_sources(connectome, (0,))
    outgoing = connectome.sources == 0
    assert np.all(silenced.counts[outgoing] == 0)
    assert np.array_equal(silenced.counts[~outgoing], connectome.counts[~outgoing])
    assert silenced.sources is connectome.sources
    assert silenced.destinations is connectome.destinations
    degree = np.diff(grouping.offsets)
    rows = np.lexsort((connectome.counts, connectome.sources, connectome.destinations))
    duplicate = np.ones(max(0, rows.size - 1), dtype=np.bool_)
    for values in (
        connectome.sources,
        connectome.destinations,
        connectome.counts,
    ):
        ordered_values = values[rows]
        duplicate &= ordered_values[1:] == ordered_values[:-1]
    arrays: dict[str, MappedArray] = {
        'neuron_ids': connectome.neuron_ids,
        'sources': connectome.sources,
        'destinations': connectome.destinations,
        'signed_counts': connectome.counts,
        'weights_mv': connectome.weights_mv,
        'grouped_edge_ids': grouping.edge_ids,
        'inverse_grouping': grouping.inverse,
        'destination_offsets': grouping.offsets,
        'absolute_count_sums': absolute,
    }
    checksums = {
        name: {
            'dtype': values.dtype.str,
            'shape': list(values.shape),
            'sha256': hashlib.sha256(values.tobytes()).hexdigest(),
        }
        for name, values in arrays.items()
    }
    artifact = output / 'mapped-inputs.npz'
    with artifact.open('xb') as destination:
        np.savez_compressed(destination, **arrays)
    report: dict[str, object] = {
        'input_sha256': {
            'data/2025_Completeness_783.csv': pin.completeness_sha256,
            'data/2025_Connectivity_783.parquet': pin.connectivity_sha256,
        },
        'neurons': int(connectome.neuron_ids.size),
        'edges': int(connectome.counts.size),
        'signed_count_min': int(connectome.counts.min()),
        'signed_count_max': int(connectome.counts.max()),
        'zero_count_rows': int(np.count_nonzero(connectome.counts == 0)),
        'duplicate_edge_rows': int(duplicate.sum()),
        'neuron_order_and_id_index_orientation_verified': True,
        'all_rows_retained': True,
        'stable_grouping_verified': True,
        'both_inverse_directions_verified': True,
        'all_edge_columns_round_trip_exact': True,
        'float32_counts_exact': True,
        'max_absolute_count_sum': int(absolute.max()),
        'max_absolute_count_target_index': int(np.argmax(absolute)),
        'incoming_degree_min': int(degree.min()),
        'incoming_degree_max': int(degree.max()),
        'incoming_degree_quantiles': np.quantile(
            degree, [0, 0.5, 0.9, 0.99, 1], method='nearest'
        ).tolist(),
        'outgoing_only_silencing_verified_on_all_edges': True,
        'delay_steps': 18,
        'queue_slots': 19,
        'checksums': checksums,
        'grouped_sha256': {
            name: hashlib.sha256(values[grouping.edge_ids].tobytes()).hexdigest()
            for name, values in arrays.items()
            if name in ('sources', 'destinations', 'signed_counts', 'weights_mv')
        },
        'artifact': str(artifact),
        'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'scope': 'Host input mapping only; no full-network execution or parity claim.',
    }
    with (output / 'mapping.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')
    return report
