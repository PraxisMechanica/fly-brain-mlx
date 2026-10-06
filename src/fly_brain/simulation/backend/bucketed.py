from dataclasses import dataclass
from functools import partial

import mlx.core as mx
import numpy as np

from fly_brain.simulation.mapping import (
    absolute_count_sums,
    bucket_destinations,
    silence_sources,
)
from fly_brain.simulation.models import Connectome
from fly_brain.simulation.observations import ReductionReader

from . import core
from .accumulation import exact_count_sum, factored_sum
from .arrays import boolean_input
from .engines import Execution
from .reduction_evidence import read_rows


@dataclass(frozen=True)
class DeviceBucket:
    targets: mx.array
    edge_ids: mx.array
    counts: mx.array
    occupied: mx.array


@dataclass(frozen=True)
class Layout:
    buckets: tuple[DeviceBucket, ...]
    inverse_targets: mx.array
    edges: int
    exact_counts: bool


def make_layout(connectome: Connectome, *, exact_counts: bool = False) -> Layout:
    buckets = bucket_destinations(connectome)
    target_order = np.concatenate([bucket.targets for bucket in buckets])
    inverse = np.argsort(target_order).astype(np.int32)
    with mx.stream(mx.gpu):
        return Layout(
            tuple(
                DeviceBucket(
                    mx.array(bucket.targets),
                    mx.array(bucket.edge_ids),
                    mx.array(bucket.counts),
                    boolean_input(bucket.occupied),
                )
                for bucket in buckets
            ),
            mx.array(inverse),
            connectome.sources.size,
            exact_counts and bool(np.all(absolute_count_sums(connectome) <= 2**24)),
        )


def accumulate(
    layout: Layout, accepted: mx.array, initial: mx.array
) -> tuple[mx.array, mx.array, mx.array]:
    if (
        accepted.dtype != mx.bool_
        or accepted.ndim != 2
        or accepted.shape[1] != layout.edges
        or initial.shape != (accepted.shape[0], layout.inverse_targets.size)
        or initial.dtype != mx.float32
    ):
        raise ValueError('Accumulation requires Boolean edges and native trial state')
    with mx.stream(mx.gpu):
        padded_events = mx.concatenate(
            [mx.zeros((accepted.shape[0], 1), dtype=mx.bool_), accepted], axis=1
        )
        outputs: list[mx.array] = []
        high_counts: list[mx.array] = []
        low_counts: list[mx.array] = []
        for bucket in layout.buckets:
            active = padded_events[:, bucket.edge_ids + 1] & bucket.occupied
            counts = mx.where(active, bucket.counts, 0)
            reduce_counts = exact_count_sum if layout.exact_counts else factored_sum
            result, high, low = reduce_counts(counts, initial[:, bucket.targets])
            outputs.append(result)
            high_counts.append(high)
            low_counts.append(low)
        return (
            mx.concatenate(outputs, axis=1)[:, layout.inverse_targets],
            mx.concatenate(high_counts, axis=1)[:, layout.inverse_targets],
            mx.concatenate(low_counts, axis=1)[:, layout.inverse_targets],
        )


def advance(
    network: core.Network, layout: Layout, state: core.State, events: mx.array
) -> tuple[core.State, core.StepTrace]:
    trials = state.voltage_mv.shape[0]
    if events.shape != (trials, network.input_targets.size) or events.dtype != mx.bool_:
        raise ValueError('Events must be Boolean with shape (trials, input channels)')
    with mx.stream(mx.gpu):
        available = state.step - state.last_spike_step >= network.refractory_steps
        voltage, synaptic = core.integrate(
            state.voltage_mv, state.synaptic_mv, available
        )
        pre_voltage, pre_synaptic = voltage, synaptic
        spikes = core.threshold_spikes(voltage, available)
        last_spike = mx.where(spikes, state.step, state.last_spike_step)
        receiving = available & ~spikes
        due = state.queue[state.step % core.QUEUE_SLOTS]
        accepted = due & receiving[:, network.destinations]
        discarded = due & ~receiving[:, network.destinations]
        synaptic, _, _ = accumulate(layout, accepted, synaptic)
        synaptic = mx.where(receiving, synaptic, pre_synaptic)
        accepted_inputs = events & receiving[:, network.input_targets]
        neurons = mx.arange(network.neurons)
        for channel in range(network.input_targets.size):
            target = neurons == network.input_targets[channel]
            voltage = mx.where(
                accepted_inputs[:, channel, None] & target, voltage + 68.75, voltage
            )
        slots = mx.arange(core.QUEUE_SLOTS)[:, None, None]
        queue = mx.where(slots == state.step % core.QUEUE_SLOTS, False, state.queue)
        queue = mx.where(
            slots == (state.step + core.DELAY_STEPS) % core.QUEUE_SLOTS,
            spikes[:, network.sources][None, :, :],
            queue,
        )
        trace = core.StepTrace(
            pre_voltage,
            pre_synaptic,
            available,
            spikes,
            receiving,
            due,
            accepted,
            discarded,
            accepted_inputs,
            voltage,
            synaptic,
        )
        updated = core.State(
            mx.where(spikes, -52, voltage),
            mx.where(spikes, 0, synaptic),
            last_spike,
            queue,
            state.step + 1,
        )
        return updated, trace


def _components(
    connectome: Connectome,
    input_targets: tuple[int, ...],
    silenced: tuple[int, ...],
    precision: str,
    *,
    exact_counts: bool = False,
) -> tuple[core.Network, Layout]:
    mx.disable_compile()
    connectome = silence_sources(connectome, silenced)
    network = core.make_network(
        connectome.neuron_ids.size,
        connectome.sources,
        connectome.destinations,
        connectome.weights_mv,
        input_targets,
        precision=precision,
    )
    layout = make_layout(connectome, exact_counts=exact_counts)
    return network, layout


def prepare(
    connectome: Connectome,
    input_targets: tuple[int, ...],
    silenced: tuple[int, ...],
    precision: str,
    *,
    exact_counts: bool = False,
) -> Execution:
    network, layout = _components(
        connectome, input_targets, silenced, precision, exact_counts=exact_counts
    )
    return Execution(network, partial(advance, network, layout))


def prepare_observed(
    connectome: Connectome,
    input_targets: tuple[int, ...],
    silenced: tuple[int, ...],
    precision: str,
    *,
    exact_counts: bool = False,
) -> tuple[Execution, ReductionReader]:
    network, layout = _components(
        connectome, input_targets, silenced, precision, exact_counts=exact_counts
    )
    return Execution(network, partial(advance, network, layout)), partial(
        read_rows, layout
    )
