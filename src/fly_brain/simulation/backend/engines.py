from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

import mlx.core as mx
import numpy as np

from fly_brain.simulation.models import NetworkCase

from . import core
from .accumulation import SCALE, factored_sum

Advance = Callable[[core.State, mx.array], tuple[core.State, core.StepTrace]]


@dataclass(frozen=True)
class Execution:
    network: core.Network
    advance: Advance


Compiler = Callable[[NetworkCase], Execution]
Factory = Callable[[NetworkCase, str], Execution]


def serial(case: NetworkCase, precision: str) -> Execution:
    network = core.make_network(
        case.neurons,
        case.sources,
        case.destinations,
        case.weights,
        case.targets,
        case.silenced,
        precision=precision,
    )
    return Execution(network, partial(core.advance, network))


def factored(case: NetworkCase, precision: str) -> Execution:
    execution = serial(case, precision)
    counts = np.rint(np.asarray(case.weights) / SCALE).astype(np.int64)
    if not np.array_equal(counts * SCALE, case.weights):
        raise ValueError('Factored weights must be exact multiples of 0.275')
    if not np.array_equal(counts.astype(np.float32).astype(np.int64), counts):
        raise ValueError('Connectivity counts must be exactly representable in float32')
    counts[np.isin(case.sources, case.silenced)] = 0
    degree = np.bincount(case.destinations, minlength=case.neurons)
    width = 1 << (max(1, int(degree.max())) - 1).bit_length()
    edge_ids = np.zeros((case.neurons, width), dtype=np.int32)
    packed = np.zeros((case.neurons, width), dtype=np.float32)
    for target in range(case.neurons):
        edges = np.flatnonzero(np.asarray(case.destinations) == target)
        edge_ids[target, : len(edges)] = edges + 1
        packed[target, : len(edges)] = counts[edges]
    with mx.stream(mx.gpu):
        device_edges, device_counts = mx.array(edge_ids), mx.array(packed)

    def advance(
        state: core.State, events: mx.array
    ) -> tuple[core.State, core.StepTrace]:
        with mx.stream(mx.gpu):
            updated, trace = execution.advance(state, events)
            accepted = mx.concatenate(
                [mx.zeros((events.shape[0], 1), dtype=mx.bool_), trace.accepted], axis=1
            )
            active_counts = mx.where(accepted[:, device_edges], device_counts, 0)
            synaptic, _, _ = factored_sum(active_counts, trace.pre_synaptic_mv)
            synaptic = mx.where(trace.receiving, synaptic, trace.pre_synaptic_mv)
            return updated._replace(
                synaptic_mv=mx.where(trace.spikes, 0, synaptic)
            ), trace._replace(before_reset_synaptic_mv=synaptic)

    return Execution(execution.network, advance)
