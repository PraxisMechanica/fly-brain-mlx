import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.fan_in import FanInCases
from fly_brain.simulation.backend.arrays import boolean_input
from fly_brain.simulation.backend.bucketed import Layout, accumulate, make_layout
from fly_brain.simulation.models import Connectome

from .fan_in_probe import Evaluation, Reduction


def execute(
    layout: Layout,
    accepted: NDArray[np.bool_],
    initial: NDArray[np.float32],
    target: int,
) -> Reduction:
    with mx.stream(mx.gpu):
        values = accumulate(layout, boolean_input(accepted), mx.array(initial))
        host = tuple(np.asarray(value, dtype=np.float32) for value in values)
    others = np.arange(initial.shape[1]) != target
    np.testing.assert_array_equal(
        host[0][:, others].view(np.uint32), initial[:, others].view(np.uint32)
    )
    for components in host[1:]:
        np.testing.assert_array_equal(components[:, others].view(np.uint32), 0)
    return host[0][:, target], host[1][:, target], host[2][:, target]


def evaluate_cases(
    connectome: Connectome,
    target: int,
    edges: NDArray[np.int32],
    cases: FanInCases,
    *,
    exact_counts: bool = False,
) -> Evaluation:
    nodes = np.unique(np.append(connectome.sources[edges], np.int32(target)))
    local_target = int(np.searchsorted(nodes, target))
    sources = np.searchsorted(nodes, connectome.sources[edges]).astype(np.int32)
    observed = tuple(
        tuple(np.empty(cases.initial64.size, dtype=np.float32) for _ in range(3))
        for _ in range(3)
    )
    for order_index, order in enumerate(cases.orders):
        local = Connectome(
            connectome.neuron_ids[nodes],
            sources[order],
            np.full(edges.size, local_target, dtype=np.int32),
            connectome.counts[edges][order],
            connectome.weights_mv[edges][order],
        )
        layout = make_layout(local, exact_counts=exact_counts)
        rows = np.flatnonzero(cases.order_indices == order_index)
        accepted = cases.masks[cases.mask_indices[rows]][:, order]
        initial = np.zeros((rows.size, nodes.size), dtype=np.float32)
        initial[:, local_target] = cases.initial64[rows].astype(np.float32)
        for group in observed[:2]:
            values = execute(layout, accepted, initial, local_target)
            for destination, values_at_target in zip(group, values, strict=True):
                destination[rows] = values_at_target
        for offset, row in enumerate(rows):
            own = execute(
                layout,
                accepted[offset : offset + 1],
                initial[offset : offset + 1],
                local_target,
            )
            for destination, value in zip(observed[2], own, strict=True):
                destination[row] = value[0]
    return (
        (observed[0][0], observed[0][1], observed[0][2]),
        (observed[1][0], observed[1][1], observed[1][2]),
        (observed[2][0], observed[2][1], observed[2][2]),
    )
