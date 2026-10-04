import math
import os
from dataclasses import dataclass
from typing import NamedTuple

import mlx.core as mx
import numpy as np
from numpy.typing import ArrayLike, NDArray

DT_MS = 0.1
DELAY_STEPS = 18
QUEUE_SLOTS = DELAY_STEPS + 1
INITIAL_LAST_SPIKE = -100000000
_a = math.exp(-DT_MS / 20)
COEFFICIENTS = tuple(
    float(np.float32(value))
    for value in (
        _a,
        math.exp(-DT_MS / 5),
        _a * -math.expm1(-DT_MS * (1 / 5 - 1 / 20)) / 3,
    )
)


@dataclass(frozen=True)
class Network:
    neurons: int
    sources: mx.array
    destinations: mx.array
    weights_mv: mx.array
    refractory_steps: mx.array
    input_targets: mx.array


class State(NamedTuple):
    voltage_mv: mx.array
    synaptic_mv: mx.array
    last_spike_step: mx.array
    queue: mx.array
    step: int


class StepTrace(NamedTuple):
    pre_voltage_mv: mx.array
    pre_synaptic_mv: mx.array
    available: mx.array
    spikes: mx.array
    receiving: mx.array
    due: mx.array
    accepted: mx.array
    discarded: mx.array
    accepted_inputs: mx.array
    before_reset_voltage_mv: mx.array
    before_reset_synaptic_mv: mx.array


def _indices(values: ArrayLike, neurons: int) -> NDArray[np.int32]:
    values = np.asarray(values)
    if values.ndim != 1 or (values.size and values.dtype.kind not in 'iu'):
        raise ValueError('Neuron indices must be a one-dimensional integer array')
    if np.any(values < 0) or np.any(values >= neurons):
        raise ValueError('Neuron index outside the network')
    return values.astype(np.int32)


def make_network(
    neurons: int,
    sources: ArrayLike = (),
    destinations: ArrayLike = (),
    weights_mv: ArrayLike = (),
    input_targets: ArrayLike = (),
    silenced: ArrayLike = (),
) -> Network:
    if os.environ.get('MLX_ENABLE_TF32') != '0':
        raise RuntimeError('Launch with MLX_ENABLE_TF32=0')
    if not mx.metal.is_available():
        raise RuntimeError('A Metal device is required; CPU fallback is unsupported')
    if neurons <= 0:
        raise ValueError('The network must contain neurons')
    source = _indices(sources, neurons)
    destination = _indices(destinations, neurons)
    targets = _indices(input_targets, neurons)
    silence = _indices(silenced, neurons)
    weights = np.asarray(weights_mv, dtype=np.float64)
    if weights.ndim != 1 or not (source.shape == destination.shape == weights.shape):
        raise ValueError('Each edge must have a source, destination, and weight')
    if not np.all(np.isfinite(weights)):
        raise ValueError('Weights must be finite')
    weights = np.where(np.isin(source, silence), 0, weights).astype(np.float32)
    refractory = np.full(neurons, 22, dtype=np.int32)
    refractory[targets] = 0
    with mx.stream(mx.gpu):
        return Network(
            neurons,
            mx.array(source),
            mx.array(destination),
            mx.array(weights),
            mx.array(refractory),
            mx.array(targets),
        )


def initial_state(
    network: Network,
    trials: int = 1,
    voltage_mv: ArrayLike = -52,
    synaptic_mv: ArrayLike = 0,
    last_spike_step: ArrayLike = INITIAL_LAST_SPIKE,
) -> State:
    if trials <= 0:
        raise ValueError('At least one trial is required')
    shape = (trials, network.neurons)
    voltage = np.broadcast_to(np.asarray(voltage_mv, dtype=np.float64), shape)
    synaptic = np.broadcast_to(np.asarray(synaptic_mv, dtype=np.float64), shape)
    last = np.broadcast_to(np.asarray(last_spike_step), shape)
    if not np.all(np.isfinite(voltage)) or not np.all(np.isfinite(synaptic)):
        raise ValueError('Initial state must be finite')
    if (
        last.dtype.kind not in 'iu'
        or np.any(last > 0)
        or np.any(last < INITIAL_LAST_SPIKE)
    ):
        raise ValueError(
            'Initial last-spike steps must be integers in the reference range'
        )
    with mx.stream(mx.gpu):
        return State(
            mx.array(voltage.astype(np.float32)),
            mx.array(synaptic.astype(np.float32)),
            mx.array(last.astype(np.int32)),
            mx.zeros((QUEUE_SLOTS, trials, network.sources.size), dtype=mx.bool_),
            0,
        )


def integrate(
    voltage_mv: mx.array, synaptic_mv: mx.array, available: mx.array
) -> tuple[mx.array, mx.array]:
    a, b, c = COEFFICIENTS
    with mx.stream(mx.gpu):
        voltage = -52 + a * (voltage_mv + 52) + c * synaptic_mv
        synaptic = b * synaptic_mv
        return mx.where(available, voltage, voltage_mv), mx.where(
            available, synaptic, synaptic_mv
        )


def threshold_spikes(voltage_mv: mx.array, available: mx.array) -> mx.array:
    with mx.stream(mx.gpu):
        return available & (voltage_mv > -45)


def advance(
    network: Network, state: State, events: mx.array
) -> tuple[State, StepTrace]:
    trials = state.voltage_mv.shape[0]
    if events.shape != (trials, network.input_targets.size) or events.dtype != mx.bool_:
        raise ValueError('Events must be Boolean with shape (trials, input channels)')
    with mx.stream(mx.gpu):
        available = state.step - state.last_spike_step >= network.refractory_steps
        voltage, synaptic = integrate(state.voltage_mv, state.synaptic_mv, available)
        pre_voltage, pre_synaptic = voltage, synaptic
        spikes = threshold_spikes(voltage, available)
        last_spike = mx.where(spikes, state.step, state.last_spike_step)
        receiving = available & ~spikes
        due = state.queue[state.step % QUEUE_SLOTS]
        accepted = due & receiving[:, network.destinations]
        discarded = due & ~receiving[:, network.destinations]
        neurons = mx.arange(network.neurons)
        # Ordered device updates avoid atomic accumulation in this small-network oracle.
        for edge in range(network.sources.size):
            target = neurons == network.destinations[edge]
            synaptic = mx.where(
                accepted[:, edge, None] & target,
                synaptic + network.weights_mv[edge],
                synaptic,
            )
        accepted_inputs = events & receiving[:, network.input_targets]
        for channel in range(network.input_targets.size):
            target = neurons == network.input_targets[channel]
            voltage = mx.where(
                accepted_inputs[:, channel, None] & target, voltage + 68.75, voltage
            )
        slots = mx.arange(QUEUE_SLOTS)[:, None, None]
        queue = mx.where(slots == state.step % QUEUE_SLOTS, False, state.queue)
        queue = mx.where(
            slots == (state.step + DELAY_STEPS) % QUEUE_SLOTS,
            spikes[:, network.sources][None, :, :],
            queue,
        )
        trace = StepTrace(
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
        next_state = State(
            mx.where(spikes, -52, voltage),
            mx.where(spikes, 0, synaptic),
            last_spike,
            queue,
            state.step + 1,
        )
        return next_state, trace
