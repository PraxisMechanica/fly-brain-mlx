import json
from pathlib import Path

import brian2 as b
import torch

from . import brian_reference as reference
from . import torch_reference as pt


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    b.set_device('runtime')
    b.start_scope()
    b.prefs.codegen.target = 'numpy'
    b.defaultclock.dt = 0.1 * b.ms
    params = reference.default_parameters()
    params['r_poi'] = 10000 * b.Hz
    group = b.NeuronGroup(
        2,
        params['eqs'],
        method='linear',
        threshold=params['eq_th'],
        reset=params['eq_rst'],
        refractory='rfc',
        namespace=params,
        name='contract_neurons',
    )
    group.v = params['v_0']
    group.g = 0
    group.rfc = params['t_rfc']
    synapses = b.Synapses(
        group,
        group,
        'w : volt',
        on_pre='g += w',
        delay=params['t_dly'],
        name='contract_synapses',
    )
    synapses.connect(i=[0], j=[1])
    synapses.w = params['w_syn']
    inputs = reference.add_poisson_inputs(group, [0], [], params)
    spikes = b.SpikeMonitor(group)
    state = b.StateMonitor(group, ('v', 'g'), record=True, when='end')
    network = b.Network(group, synapses, spikes, state, *inputs)
    network.run(0.5 * b.ms)

    weights = torch.tensor([[0.0, 0.0], [1.0, 0.0]])
    model = pt.TorchModel(1, 2, 0.1, pt.model_parameters(), weights)
    torch_state = model.state_init()
    torch_state[3][0, 0] = -44
    trace: list[dict[str, int | float]] = []
    with torch.no_grad():
        for step in range(25):
            torch_state = model.forward(torch.zeros(1, 2), *torch_state)
            trace.append(
                {
                    'step': step,
                    'g_mv': torch_state[0][0, 1].item(),
                    'v_mv': torch_state[3][0, 1].item(),
                }
            )

    report: dict[str, object] = {
        'brian2_version': b.__version__,
        'timestep_ms': float(b.defaultclock.dt / b.ms),
        'voltage_dtype': str(group.variables['v'].dtype),
        'schedule': str(network.scheduling_summary()),
        'generated_state_update': group.state_updater.abstract_code,
        'reset': group.resetter['spike'].abstract_code,
        'synaptic_delay_ms': float(synapses.delay[:] / b.ms),
        'guaranteed_stimulation': {
            'rate_hz': 10000,
            'end_voltage_mv': (state.v[0] / b.mV).tolist(),
            'spike_times_ms': (spikes.t / b.ms).tolist(),
        },
        'pytorch_single_spike_delay': {
            'setup': 'Two neurons, source initialized at -44 mV, destination at -52 mV, weight[post=1,pre=0]=1, no external input; source spikes at step 0',
            'first_destination_g_step': next(
                row['step'] for row in trace if row['g_mv'] != 0
            ),
            'first_destination_v_step': next(
                row['step'] for row in trace if row['v_mv'] != -52
            ),
            'trace': trace,
        },
    }
    with (output / 'reference-schedule.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')
    return report
