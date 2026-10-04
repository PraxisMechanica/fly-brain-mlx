import mlx.core as mx
import numpy as np
from numpy.typing import ArrayLike

from fly_brain.simulation.backend.core import State, StepTrace
from fly_brain.simulation.models import Connectome

CHECK_NAMES = (
    'available',
    'threshold',
    'receiving',
    'due',
    'accepted',
    'discarded',
    'accepted_inputs',
    'last_spike_step',
    'finite_pre',
    'finite_before',
    'finite_end',
    *(f'queue-slot-{slot}' for slot in range(19)),
)


class EventLedger:
    def __init__(
        self,
        connectome: Connectome,
        targets: tuple[int, ...],
        trials: int,
        last_spike_step: ArrayLike = -100000000,
    ) -> None:
        neurons = connectome.neuron_ids.size
        last = np.broadcast_to(
            np.asarray(last_spike_step, dtype=np.int32), (trials, neurons)
        )
        refractory = np.full(neurons, 22, dtype=np.int32)
        refractory[list(targets)] = 0
        self.step = 0
        with mx.stream(mx.gpu):
            self.sources = mx.array(connectome.sources)
            self.destinations = mx.array(connectome.destinations)
            self.targets = mx.array(targets, dtype=mx.int32)
            self.refractory = mx.array(refractory)
            self.last = mx.array(last)
            self.empty_edges = mx.zeros(
                (trials, connectome.sources.size), dtype=mx.bool_
            )
            self.history = [mx.zeros((trials, neurons), dtype=mx.bool_)] * 19

    def check(self, state: State, trace: StepTrace, events: mx.array) -> mx.array:
        step = self.step
        if state.step != step + 1:
            raise ValueError('MLX observer step or clock is out of order')
        with mx.stream(mx.gpu):
            available = step - self.last >= self.refractory
            spikes = available & (trace.pre_voltage_mv > -45)
            receiving = available & ~trace.spikes
            due = (
                self.history[(step - 18) % 19][:, self.sources]
                if step >= 18
                else self.empty_edges
            )
            accepted = due & receiving[:, self.destinations]
            discarded = due & ~receiving[:, self.destinations]
            accepted_inputs = events & receiving[:, self.targets]
            self.last = mx.where(trace.spikes, step, self.last)
            self.history[step % 19] = trace.spikes
            columns = [
                mx.all(actual == expected, axis=1)
                for actual, expected in (
                    (trace.available, available),
                    (trace.spikes, spikes),
                    (trace.receiving, receiving),
                    (trace.due, due),
                    (trace.accepted, accepted),
                    (trace.discarded, discarded),
                    (trace.accepted_inputs, accepted_inputs),
                    (state.last_spike_step, self.last),
                )
            ]
            columns.extend(
                mx.all(mx.isfinite(voltage) & mx.isfinite(synaptic), axis=1)
                for voltage, synaptic in (
                    (trace.pre_voltage_mv, trace.pre_synaptic_mv),
                    (trace.before_reset_voltage_mv, trace.before_reset_synaptic_mv),
                    (state.voltage_mv, state.synaptic_mv),
                )
            )
            for slot in range(19):
                due_step = step + 1 + (slot - step - 1) % 19
                source_step = due_step - 18
                pending = (
                    self.history[source_step % 19][:, self.sources]
                    if 0 <= source_step <= step
                    else self.empty_edges
                )
                columns.append(mx.all(state.queue[slot] == pending, axis=1))
            result = mx.stack(columns, axis=1)
        self.step += 1
        return result
