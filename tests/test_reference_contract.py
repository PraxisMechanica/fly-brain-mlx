from pathlib import Path
import sys

import brian2 as b
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import run_brian2_cuda as reference
from run_pytorch import AlphaLIF, MODEL_PARAMS
import torch


@pytest.fixture(autouse=True)
def runtime_reference():
    b.set_device('runtime')
    b.start_scope()
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'


def neurons(size, **overrides):
    params = dict(reference.default_params)
    params.update(overrides)
    group = b.NeuronGroup(
        size,
        params['eqs'],
        method='linear',
        threshold=params['eq_th'],
        reset=params['eq_rst'],
        refractory='rfc',
        namespace=params,
        name='reference_neurons*',
    )
    group.v = params['v_0']
    group.g = 0 * b.mV
    group.rfc = params['t_rfc']
    return group, params


def test_leak_uses_exact_linear_decay():
    group, _ = neurons(1)
    group.v = -50 * b.mV
    b.Network(group).run(1 * b.ms)
    expected = -52 + 2 * np.exp(-1 / 20)
    assert float(group.v[0] / b.mV) == pytest.approx(expected, rel=0, abs=1e-11)


def test_linear_membrane_step_uses_coupled_synaptic_decay():
    group, _ = neurons(1)
    group.g = 1 * b.mV
    b.Network(group).run(0.1 * b.ms)
    membrane_decay = np.exp(-0.1 / 20)
    synaptic_decay = np.exp(-0.1 / 5)
    expected = (-52 + (5 / 15) * (membrane_decay - synaptic_decay), synaptic_decay)
    state = (float(group.v[0] / b.mV), float(group.g[0] / b.mV))
    assert state == pytest.approx(expected, rel=0, abs=1e-11)


def test_threshold_equality_does_not_emit_a_spike():
    group, _ = neurons(2, v_0=-45 * b.mV)
    group.v = [-45, -44.99] * b.mV
    monitor = b.SpikeMonitor(group)
    b.Network(group, monitor).run(0.1 * b.ms)
    assert monitor.i[:].tolist() == [1]


def test_reset_clears_neuron_state_without_modifying_synaptic_weights():
    group, params = neurons(2)
    group.v[0] = -44 * b.mV
    group.g[0] = 1 * b.mV
    synapses = b.Synapses(group, group, 'w : volt', on_pre='g += w', delay=params['t_dly'])
    synapses.connect(i=[0], j=[1])
    synapses.w = 0.275 * b.mV
    b.Network(group, synapses).run(0.1 * b.ms)
    state = (float(group.v[0] / b.mV), float(group.g[0] / b.mV), float(synapses.w[0] / b.mV))
    assert state == pytest.approx((-52, 0, 0.275), rel=0, abs=1e-11)


def test_poisson_voltage_kick_occurs_after_threshold_and_before_reset():
    group, params = neurons(1, r_poi=10000 * b.Hz)
    inputs = reference.add_poisson_inputs(group, [0], [], params)
    monitor = b.SpikeMonitor(group)
    b.Network(group, monitor, *inputs).run(0.5 * b.ms)
    assert list(monitor.t / b.ms) == pytest.approx([0.1, 0.3], rel=0, abs=1e-12)


def test_delayed_input_arrives_after_integration_at_the_recorded_delay():
    group, params = neurons(2)
    group.v[0] = -44 * b.mV
    synapses = b.Synapses(group, group, 'w : volt', on_pre='g += w', delay=params['t_dly'])
    synapses.connect(i=[0], j=[1])
    synapses.w = 1 * b.mV
    monitor = b.StateMonitor(group, ('v', 'g'), record=True, when='end')
    b.Network(group, synapses, monitor).run(2 * b.ms)
    arrival = (float(monitor.g[1, 17] / b.mV), float(monitor.g[1, 18] / b.mV), float(monitor.v[1, 18] / b.mV))
    assert arrival == pytest.approx((0, 1, -52), rel=0, abs=1e-11)


def test_refractory_state_freezes_both_variables_and_drops_incoming_events():
    group, _ = neurons(1)
    group.lastspike = 0 * b.ms
    group.v = -50 * b.mV
    group.g = 1 * b.mV
    source = b.SpikeGeneratorGroup(1, [0], [0.1] * b.ms)
    synapses = b.Synapses(source, group, on_pre='g += 3*mV')
    synapses.connect()
    monitor = b.StateMonitor(group, ('v', 'g', 'not_refractory'), record=True, when='end')
    b.Network(group, source, synapses, monitor).run(2.3 * b.ms)
    frozen = np.column_stack((monitor.v[0, :22] / b.mV, monitor.g[0, :22] / b.mV))
    np.testing.assert_array_equal(frozen, np.tile([-50, 1], (22, 1)))
    assert monitor.not_refractory[0, :].tolist() == [False] * 22 + [True]


def test_reference_silencing_only_zeroes_outgoing_edges():
    group, _ = neurons(3)
    synapses = b.Synapses(group, group, 'w : volt', on_pre='g += w')
    synapses.connect(i=[0, 1, 2], j=[1, 2, 1])
    synapses.w = [1, 2, 3] * b.mV
    reference.silence_neurons(synapses, [1])
    b.Network(group, synapses).run(0 * b.ms)
    assert list(synapses.w / b.mV) == [1, 0, 3]


def test_spiking_blocks_same_step_inputs_even_with_zero_refractory_duration():
    group, _ = neurons(2)
    group.v = -44 * b.mV
    group.rfc = [0, 2.2] * b.ms
    source = b.SpikeGeneratorGroup(1, [0], [0] * b.ms)
    synapses = b.Synapses(source, group, on_pre='g += 3*mV; v += 4*mV')
    synapses.connect()
    before = b.StateMonitor(group, ('v', 'g', 'not_refractory'), record=True, when='synapses', order=-2)
    after = b.StateMonitor(group, ('v', 'g', 'not_refractory'), record=True, when='synapses', order=1)
    b.Network(group, source, synapses, before, after).run(0.1 * b.ms)
    np.testing.assert_array_equal(after.v[:], before.v[:])
    np.testing.assert_array_equal(after.g[:], before.g[:])
    assert after.not_refractory[:, 0].tolist() == [False, False]


def test_refractory_release_accepts_only_events_at_or_after_step_22():
    group, _ = neurons(1)
    group.lastspike = 0 * b.ms
    source = b.SpikeGeneratorGroup(1, [0, 0], [2.1, 2.2] * b.ms)
    synapses = b.Synapses(source, group, on_pre='g += 3*mV')
    synapses.connect()
    monitor = b.StateMonitor(group, ('v', 'g'), record=True, when='end')
    b.Network(group, source, synapses, monitor).run(2.4 * b.ms)
    assert list(monitor.g[0, 21:23] / b.mV) == [0, 3]
    assert float(monitor.v[0, 22] / b.mV) == pytest.approx(-52, rel=0, abs=1e-11)
    assert float(monitor.v[0, 23] / b.mV) > -52


def test_deterministic_replay_matches_guaranteed_native_poisson_input():
    traces = []
    for native in (True, False):
        group, params = neurons(1, r_poi=10000 * b.Hz)
        group.rfc = 0 * b.ms
        if native:
            inputs = reference.add_poisson_inputs(group, [0], [], params)
        else:
            source = b.SpikeGeneratorGroup(1, [0] * 5, np.arange(5) * 0.1 * b.ms)
            synapses = b.Synapses(source, group, on_pre='v += 68.75*mV')
            synapses.connect()
            synapses.pre.order = 0
            inputs = [source, synapses]
        state = b.StateMonitor(group, ('v', 'g'), record=True, when='end')
        spikes = b.SpikeMonitor(group)
        b.Network(group, state, spikes, *inputs).run(0.5 * b.ms)
        traces.append((np.asarray(state.v[:]), np.asarray(state.g[:]), np.asarray(spikes.t[:])))
    for native, replay in zip(*traces):
        np.testing.assert_array_equal(native, replay)


def test_pytorch_refractory_counter_does_not_gate_voltage_or_threshold():
    model = AlphaLIF(1, 1, 0.1, MODEL_PARAMS)
    conductance, delay, spikes, voltage, refractory = model.state_init()
    spikes.fill_(1)
    with torch.no_grad():
        state = model(
            torch.zeros(1, 1), torch.full((1, 1), 68.75),
            conductance, delay, spikes, voltage, refractory,
        )
    assert (state[2].item(), state[4].item()) == (1, 0)
