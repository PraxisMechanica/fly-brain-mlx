from typing import TYPE_CHECKING, cast

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.observations import (
    COMPENSATED_ORDER,
    EXACT_ORDER,
    ReductionEvidence,
    ReductionRow,
)

from .arrays import as_host, evaluate

if TYPE_CHECKING:
    from .bucketed import Layout


def read_rows(layout: 'Layout', neurons: tuple[int, ...]) -> ReductionEvidence:
    records: list[ReductionRow] = []
    for neuron in neurons:
        for bucket in layout.buckets:
            with mx.stream(mx.gpu):
                rows = np.flatnonzero(as_host(bucket.targets) == neuron)
                if not len(rows):
                    continue
                row = int(rows[0])
                values = (
                    bucket.edge_ids[row],
                    bucket.counts[row],
                    bucket.occupied[row],
                )
                evaluate(*values)
                edges = cast(NDArray[np.int32], as_host(values[0]))
                counts = cast(NDArray[np.float32], as_host(values[1]))
                occupied = cast(NDArray[np.bool_], as_host(values[2]))
                records.append(ReductionRow(neuron, edges, counts, occupied))
            break
        else:
            raise ValueError('Cause neuron is absent from the actual device layout')
    return ReductionEvidence(
        tuple(records), EXACT_ORDER if layout.exact_counts else COMPENSATED_ORDER
    )
