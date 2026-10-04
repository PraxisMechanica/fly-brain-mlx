import brian2 as b
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.models import NetworkCase as Case

from . import brian_reference as reference

BoolArray = NDArray[np.bool_]
TraceArrays = dict[
    str, NDArray[np.float32 | np.float64 | np.int32 | np.int64 | np.bool_]
]


def run_reference(case: Case, events: BoolArray) -> TraceArrays:
    trials = events.shape[1]
    output: list[TraceArrays] = []
    initial_v = np.broadcast_to(case.voltage, (trials, case.neurons))
    initial_g = np.broadcast_to(case.synaptic, (trials, case.neurons))
    initial_last = np.broadcast_to(case.last_spike, (trials, case.neurons))
    sources = np.array(case.sources, dtype=np.int32)
    destinations = np.array(case.destinations, dtype=np.int32)
    targets = np.array(case.targets, dtype=np.int32)
    for trial in range(trials):
        b.set_device('runtime')
        b.start_scope()
        b.defaultclock.dt = 0.1 * b.ms
        b.prefs.codegen.target = 'numpy'
        params = reference.default_parameters()
        group = b.NeuronGroup(
            case.neurons,
            params['eqs'],
            method='linear',
            threshold=params['eq_th'],
            reset=params['eq_rst'],
            refractory='rfc',
            namespace=params,
        )
        group.v = initial_v[trial] * b.mV
        group.g = initial_g[trial] * b.mV
        group.lastspike = initial_last[trial] * 0.1 * b.ms
        refractory = np.full(case.neurons, 2.2)
        refractory[targets] = 0
        group.rfc = refractory * b.ms
        objects: list[b.BrianObject] = [group]
        if len(sources):
            synapses = b.Synapses(
                group, group, 'w : volt', on_pre='g += w', delay=1.8 * b.ms
            )
            synapses.connect(i=sources, j=destinations)
            synapses.w = np.array(case.weights) * b.mV
            reference.silence_neurons(synapses, case.silenced)
            objects.append(synapses)
        if len(targets):
            steps, channels = np.nonzero(events[:, trial])
            driver = b.SpikeGeneratorGroup(len(targets), channels, steps * 0.1 * b.ms)
            inputs = b.Synapses(driver, group, on_pre='v += 68.75*mV')
            inputs.connect(i=np.arange(len(targets)), j=targets)
            inputs.pre.order = 0
            objects.extend((driver, inputs))
        pre = b.StateMonitor(
            group,
            ('v', 'g', 'not_refractory'),
            record=True,
            when='thresholds',
            order=-1,
        )
        before = b.StateMonitor(
            group, ('v', 'g', 'not_refractory'), record=True, when='resets', order=-1
        )
        end = b.StateMonitor(group, ('v', 'g', 'lastspike'), record=True, when='end')
        spikes = b.SpikeMonitor(group)
        b.Network(*objects, pre, before, end, spikes).run(len(events) * 0.1 * b.ms)
        masks = np.zeros((len(events), case.neurons), dtype=np.bool_)
        spike_steps = np.rint(spikes.t[:] / b.defaultclock.dt).astype(np.int64)
        masks[spike_steps, spikes.i[:]] = True
        due = np.zeros((len(events), len(sources)), dtype=np.bool_)
        due[18:] = masks[:-18, sources] if len(events) >= 18 else due[18:]
        queue = np.zeros((len(events), 19, len(sources)), dtype=np.bool_)
        for spike_step, neuron in zip(spike_steps, spikes.i[:], strict=True):
            pending_until = min(len(events), spike_step + 18)
            for edge in np.flatnonzero(sources == neuron):
                queue[spike_step:pending_until, (spike_step + 18) % 19, edge] = True
        receiving = np.asarray(before.not_refractory[:]).T
        accepted = due & receiving[:, destinations]
        output.append(
            {
                'pre_voltage_mv': np.asarray(pre.v[:] / b.mV).T,
                'pre_synaptic_mv': np.asarray(pre.g[:] / b.mV).T,
                'available': np.asarray(pre.not_refractory[:]).T,
                'spikes': masks,
                'receiving': receiving,
                'due': due,
                'accepted': accepted,
                'discarded': due & ~receiving[:, destinations],
                'accepted_inputs': events[:, trial] & receiving[:, targets],
                'before_reset_voltage_mv': np.asarray(before.v[:] / b.mV).T,
                'before_reset_synaptic_mv': np.asarray(before.g[:] / b.mV).T,
                'voltage_mv': np.asarray(end.v[:] / b.mV).T,
                'synaptic_mv': np.asarray(end.g[:] / b.mV).T,
                'last_spike_step': np.rint(end.lastspike[:] / (0.1 * b.ms))
                .astype(np.int32)
                .T,
                'queue': queue,
            }
        )
    return {
        name: np.stack([trial[name] for trial in output], axis=1) for name in output[0]
    }
