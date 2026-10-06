import hashlib

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.observations import (
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationOperands,
    PhysicalQueueObservation,
)

from . import core
from .arrays import as_host, boolean_input, evaluate
from .engines import Advance


def _native_int32(value: mx.array) -> NDArray[np.int32]:
    if value.dtype != mx.int32:
        raise ValueError('Native configuration requires actual int32 fields')
    return np.asarray(value, dtype=np.int32)


def _native_float32(value: mx.array) -> NDArray[np.float32]:
    if value.dtype != mx.float32:
        raise ValueError('Native configuration requires actual float32 fields')
    return np.asarray(value, dtype=np.float32)


class NativeObservationSession:
    def __init__(
        self,
        advance: Advance,
        network: core.Network,
        state: core.State,
        trial_indices: tuple[int, ...],
    ) -> None:
        self._advance = advance
        self._network = network
        self._state = state
        self._trial_indices = trial_indices
        self._initial_step = state.step
        self._initial_voltage = state.voltage_mv
        self._initial_synaptic = state.synaptic_mv
        self._initial_last = state.last_spike_step
        self._trace: core.StepTrace | None = None

    @property
    def configuration(self) -> ObservationConfiguration:
        with mx.stream(mx.gpu):
            return ObservationConfiguration(
                self._network.neurons,
                self._state.queue.shape[0],
                self._initial_step,
                self._trial_indices,
                _native_int32(self._network.sources),
                _native_int32(self._network.destinations),
                _native_int32(self._network.input_targets),
                _native_int32(self._network.refractory_steps),
                _native_float32(self._initial_voltage),
                _native_float32(self._initial_synaptic),
                _native_int32(self._initial_last),
            )

    def advance(self, events: NDArray[np.bool_]) -> NativeObservation:
        if self._trace is not None:
            raise ValueError(
                'The previous observation lacks a complete matching comparison'
            )
        with mx.stream(mx.gpu):
            inputs = boolean_input(events)
            self._state, trace = self._advance(self._state, inputs)
            fields = {
                'pre_v': trace.pre_voltage_mv,
                'pre_g': trace.pre_synaptic_mv,
                'pre_not_refractory': trace.available,
                'spikes': trace.spikes,
                'before_v': trace.before_reset_voltage_mv,
                'before_g': trace.before_reset_synaptic_mv,
                'before_not_refractory': trace.receiving,
                'end_v': self._state.voltage_mv,
                'end_g': self._state.synaptic_mv,
                'end_last_spike_step': self._state.last_spike_step,
                'end_not_refractory': trace.receiving,
                'accepted_inputs': trace.accepted_inputs,
            }
            evaluate(
                *self._state[:-1],
                *fields.values(),
                trace.due,
                trace.accepted,
                trace.discarded,
            )
            self._trace = trace
            if trace.due.dtype != mx.bool_ or trace.due.shape != (
                len(self._trial_indices),
                self._network.sources.size,
            ):
                raise ValueError('Native due masks have incomplete actual coverage')
            due = np.asarray(trace.due, dtype=np.bool_)
            recorded = {name: as_host(value) for name, value in fields.items()}
            return NativeObservation(
                self._state.step,
                self._trial_indices,
                recorded,
                tuple(np.flatnonzero(trial).astype(np.int32) for trial in due),
                tuple(hashlib.sha256(memoryview(trial)).hexdigest() for trial in due),
            )

    def compare(self, operands: ObservationOperands) -> NativeComparison:
        trace = self._trace
        if trace is None:
            raise ValueError('Comparison requires an actual pending observation')
        trials, neurons = self._state.voltage_mv.shape
        if (
            operands.available.shape != (trials, neurons)
            or operands.sources.shape != (self._network.sources.size,)
            or operands.pending_sources.shape
            != (self._state.queue.shape[0], trials, neurons)
            or operands.accepted_inputs.shape != trace.accepted_inputs.shape
            or np.any(operands.sources < 0)
            or np.any(operands.sources >= neurons)
            or np.any(operands.destinations < 0)
            or np.any(operands.destinations >= neurons)
        ):
            raise ValueError(
                'Native comparison operands have incomplete actual coverage'
            )
        with mx.stream(mx.gpu):
            sources = mx.array(operands.sources)
            destinations = mx.array(operands.destinations)
            due = boolean_input(operands.due_sources)[:, sources]
            accepted = (
                due & boolean_input(operands.accepted_destinations)[:, destinations]
            )
            discarded = (
                due & boolean_input(operands.discarded_destinations)[:, destinations]
            )
            columns = [
                mx.all(actual == expected, axis=1)
                for actual, expected in (
                    (trace.available, boolean_input(operands.available)),
                    (trace.spikes, boolean_input(operands.spikes)),
                    (trace.receiving, boolean_input(operands.receiving)),
                    (trace.due, due),
                    (trace.accepted, accepted),
                    (trace.discarded, discarded),
                    (trace.accepted_inputs, boolean_input(operands.accepted_inputs)),
                    (self._state.last_spike_step, mx.array(operands.last_spike_step)),
                )
            ]
            pending = boolean_input(operands.pending_sources)[:, :, sources]
            queues = mx.all(self._state.queue == pending, axis=2).T
            gates = mx.stack(columns, axis=1)
            evaluate(gates, queues)
            result = NativeComparison(
                self._state.step,
                self._trial_indices,
                np.asarray(gates, dtype=np.bool_),
                np.asarray(queues, dtype=np.bool_),
            )
        if result.gates_equal.all() and result.queue_equal.all():
            self._trace = None
        return result

    def physical_queue(self) -> PhysicalQueueObservation:
        if self._state.queue.dtype != mx.bool_:
            raise ValueError('Physical queue must preserve the actual Boolean dtype')
        with mx.stream(mx.gpu):
            queue = np.asarray(self._state.queue, dtype=np.bool_)
        return PhysicalQueueObservation(self._state.step, self._trial_indices, queue)
