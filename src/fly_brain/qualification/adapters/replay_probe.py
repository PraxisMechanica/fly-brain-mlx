import hashlib
import json
from pathlib import Path
from typing import Literal

import brian2 as b
import numpy as np
from numpy.typing import NDArray

from . import brian_reference as reference
from .brian_replay import TraceArrays


def linear_precision() -> dict[str, object]:
    a = np.exp(-0.1 / 20)
    decay = np.exp(-0.1 / 5)
    coupling = a * -np.expm1(-0.1 * (1 / 5 - 1 / 20)) / 3
    initial_v = np.array([-52, -50, -100, -52, -52, -52], dtype=np.float64)
    initial_g = np.array([0, 0, -100, 100, 1024, -1024], dtype=np.float64)
    b.start_scope()
    params = reference.default_parameters()
    group = b.NeuronGroup(
        6, params['eqs'], method='linear', refractory='rfc', namespace=params
    )
    group.v = initial_v * b.mV
    group.g = initial_g * b.mV
    group.rfc = 0 * b.ms
    monitor = b.StateMonitor(group, ('v', 'g'), record=True, when='end')
    b.Network(group, monitor).run(1000 * b.ms)
    expected = np.stack((monitor.v[:] / b.mV, monitor.g[:] / b.mV), axis=-1)
    observed: list[dict[str, object]] = []
    for dtype in (np.float64, np.float32):
        v, g = initial_v.astype(dtype), initial_g.astype(dtype)
        trace: list[NDArray[np.generic]] = []
        for _ in range(10000):
            v = dtype(-52) + dtype(a) * (v + dtype(52)) + dtype(coupling) * g
            g = dtype(decay) * g
            trace.append(np.stack((v, g), axis=-1))
        stacked = np.stack(trace, axis=1).astype(np.float64)
        error = np.abs(stacked - expected)
        observed.append(
            {
                'dtype': np.dtype(dtype).name,
                'max_abs_error_mv_by_variable_v_g': error.max(axis=(0, 1)).tolist(),
                'max_abs_error_mv_by_neuron_v_g': error.max(axis=1).tolist(),
                'first_step_max_abs_error_mv_v_g': error[:, 0].max(axis=0).tolist(),
                'within_trajectory_budget': bool(
                    np.all(error <= 1e-3 + 1e-5 * np.abs(expected))
                ),
                'within_first_step_budget': bool(
                    np.all(error[:, 0] <= 2e-5 + 2e-6 * np.abs(expected[:, 0]))
                ),
            }
        )
        assert observed[-1]['within_trajectory_budget']
        assert observed[-1]['within_first_step_budget']
    return {
        'steps': 10000,
        'threshold_disabled_for_linear_diagnostic': True,
        'initial_voltage_mv': initial_v.tolist(),
        'initial_synaptic_state_mv': initial_g.tolist(),
        'coefficients_float64': {
            'a': float(a),
            'b': float(decay),
            'c': float(coupling),
        },
        'coefficients_float32': {
            key: float(np.float32(value))
            for key, value in zip('abc', (a, decay, coupling), strict=True)
        },
        'coefficient_c_from_float32_exponential_subtraction': float(
            (np.float32(a) - np.float32(decay)) / np.float32(3)
        ),
        'brian2_state_range_mv_v_g': [
            expected.min(axis=(0, 1)).tolist(),
            expected.max(axis=(0, 1)).tolist(),
        ],
        'comparisons': observed,
        'euler_first_step_voltage_error_for_g100_mv': float(0.5 - 100 * coupling),
        'euler_first_step_synaptic_error_for_g100_mv': float(98 - 100 * decay),
    }


def threshold_and_summation() -> dict[str, object]:
    ulp = float(np.spacing(np.float32(45)))
    threshold_values = -45 + np.array([-1, -0.25, 0, 0.25, 1]) * ulp
    b.start_scope()
    params = reference.default_parameters()
    group = b.NeuronGroup(
        5,
        params['eqs'],
        method='linear',
        threshold=params['eq_th'],
        reset=params['eq_rst'],
        refractory='rfc',
        namespace=params,
    )
    group.v = threshold_values * b.mV
    group.g = 0 * b.mV
    group.rfc = 0 * b.ms
    group.state_updater.active = False
    monitor = b.SpikeMonitor(group)
    b.Network(group, monitor).run(0.1 * b.ms)
    weights = np.concatenate((np.full(2048, 2405), [1], np.full(2048, -2405))) * 0.275
    interleaved = np.concatenate((np.tile([2405, -2405], 2048), [1])) * 0.275
    serial = np.add.accumulate(weights.astype(np.float32))[-1]
    alternate = np.add.accumulate(interleaved.astype(np.float32))[-1]
    assert monitor.i[:].tolist() == [3, 4]
    assert np.flatnonzero(
        threshold_values.astype(np.float32) > np.float32(-45)
    ).tolist() == [4]
    assert serial != alternate
    return {
        'float32_ulp_at_threshold_mv': ulp,
        'threshold_only_probe_no_integration': True,
        'threshold_input_mv': threshold_values.tolist(),
        'threshold_input_float32_mv': threshold_values.astype(np.float32).tolist(),
        'brian2_float64_spiking_indices': monitor.i[:].tolist(),
        'float32_strict_comparison_spiking_indices': np.flatnonzero(
            threshold_values.astype(np.float32) > -45
        ).tolist(),
        'fanin_events': len(weights),
        'fanin_sum_abs_mv': float(np.abs(weights).sum()),
        'fanin_exact_real_sum_mv': 0.275,
        'fanin_float64_serial_mv': float(np.add.accumulate(weights)[-1]),
        'fanin_float32_serial_mv': float(serial),
        'fanin_float32_interleaved_serial_mv': float(alternate),
        'fanin_float32_numpy_sum_mv': float(np.sum(weights.astype(np.float32))),
    }


def stimulus(seed: int, trial: int, steps: int) -> NDArray[np.uint8]:
    generator = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence([seed, 2, trial]))
    )
    return (
        generator.random((steps, 3), dtype=np.float64) < np.array([200, 100, 0]) * 1e-4
    ).astype(np.uint8)


def replay(
    events: NDArray[np.uint8], output: Path, engine: Literal['numpy', 'cpp']
) -> TraceArrays:
    b.device.reinit()
    b.set_device(
        'runtime' if engine == 'numpy' else 'cpp_standalone', build_on_run=False
    )
    b.start_scope()
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'
    params = reference.default_parameters()
    group = b.NeuronGroup(
        3,
        params['eqs'],
        method='linear',
        threshold=params['eq_th'],
        reset=params['eq_rst'],
        refractory='rfc',
        namespace=params,
        name='review_neurons',
    )
    group.v = params['v_0']
    group.g = 0 * b.mV
    group.rfc = [0, 0, 2.2] * b.ms
    synapses = b.Synapses(
        group,
        group,
        'w : volt',
        on_pre='g += w',
        delay=params['t_dly'],
        name='review_recurrent',
    )
    synapses.connect(i=[0, 0, 1, 2], j=[1, 2, 2, 1])
    synapses.w = [0.275, 100, -0.55, 0.825] * b.mV
    steps, channels = np.nonzero(events)
    source = b.SpikeGeneratorGroup(
        3, channels, steps * 0.1 * b.ms, name='review_source'
    )
    inputs = b.Synapses(source, group, on_pre='v += 68.75*mV', name='review_replay')
    inputs.connect(i=[0, 1, 2], j=[0, 0, 1])
    inputs.pre.order = 0
    spikes = b.SpikeMonitor(group)
    state = b.StateMonitor(
        group, ('v', 'g', 'not_refractory', 'lastspike'), record=True, when='end'
    )
    network = b.Network(group, synapses, source, inputs, spikes, state)
    network.run(len(events) * 0.1 * b.ms)
    if engine == 'cpp':
        assert not (output / 'standalone').exists()
        b.prefs.devices.cpp_standalone.extra_make_args_unix = ['-j2']
        b.device.build(
            directory=str(output / 'standalone'), clean=False, with_output=False
        )
    arrays = {
        'voltage_mv': np.asarray(state.v[:] / b.mV),
        'synaptic_mv': np.asarray(state.g[:] / b.mV),
        'not_refractory': np.asarray(state.not_refractory[:]),
        'lastspike_ms': np.asarray(state.lastspike[:] / b.ms),
        'spike_steps': np.rint(spikes.t[:] / b.defaultclock.dt).astype(np.int64),
        'spike_neurons': np.asarray(spikes.i[:]),
    }
    with (output / 'trace.json').open('x') as destination:
        json.dump(
            {key: value.tolist() for key, value in arrays.items()},
            destination,
            indent=2,
        )
        destination.write('\n')
    return arrays


def run(output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    b.set_device('runtime')
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'
    report: dict[str, object] = {
        'brian2': b.__version__,
        'numpy': np.__version__,
        'linear_precision': linear_precision(),
        'threshold_and_summation': threshold_and_summation(),
    }
    events = stimulus(20261004, 0, 1000)
    np.testing.assert_array_equal(events, stimulus(20261004, 0, 1000))
    np.testing.assert_array_equal(events[:100], stimulus(20261004, 0, 100))
    assert not np.array_equal(events, stimulus(20261004, 1, 1000))
    with (output / 'stimulus.npy').open('xb') as destination:
        np.save(destination, events, allow_pickle=False)
    np.testing.assert_array_equal(
        events, np.load(output / 'stimulus.npy', allow_pickle=False)
    )
    report['stimulus'] = {
        'seed': 20261004,
        'experiment_code': 2,
        'trial': 0,
        'generator': 'PCG64(SeedSequence([seed, experiment_code, trial]))',
        'shape': list(events.shape),
        'rates_hz': [200, 100, 0],
        'channel_targets': [0, 0, 1],
        'events_per_channel': events.sum(axis=0).tolist(),
        'raw_uint8_sha256': hashlib.sha256(events.tobytes(order='C')).hexdigest(),
        'regeneration_roundtrip_and_duration_prefix_exact': True,
        'different_trial_changes_events': True,
    }
    runs: dict[str, TraceArrays] = {}
    engines: tuple[Literal['numpy', 'cpp'], ...] = ('numpy', 'cpp')
    for engine in engines:
        for repeat in range(2):
            name = f'{engine}-{repeat}'
            destination = output / name
            destination.mkdir()
            runs[name] = replay(events, destination, engine)
            print(f'Completed {name}', flush=True)
    comparisons = {}
    for name, arrays in runs.items():
        expected = runs['numpy-0']
        comparisons[name] = {
            'max_abs_voltage_error_mv': float(
                np.max(
                    np.abs(
                        np.asarray(arrays['voltage_mv'], dtype=np.float64)
                        - np.asarray(expected['voltage_mv'], dtype=np.float64)
                    )
                )
            ),
            'max_abs_synaptic_error_mv': float(
                np.max(
                    np.abs(
                        np.asarray(arrays['synaptic_mv'], dtype=np.float64)
                        - np.asarray(expected['synaptic_mv'], dtype=np.float64)
                    )
                )
            ),
            'discrete_and_lastspike_exact': all(
                np.array_equal(arrays[key], expected[key])
                for key in (
                    'spike_steps',
                    'spike_neurons',
                    'not_refractory',
                    'lastspike_ms',
                )
            ),
            'same_engine_repeat_bitwise': all(
                np.array_equal(value, runs[f'{name.split("-")[0]}-0'][key])
                for key, value in arrays.items()
            ),
            'spikes': len(arrays['spike_steps']),
        }
        np.testing.assert_allclose(
            arrays['voltage_mv'], expected['voltage_mv'], rtol=0, atol=1e-11
        )
        np.testing.assert_allclose(
            arrays['synaptic_mv'], expected['synaptic_mv'], rtol=0, atol=1e-11
        )
        assert comparisons[name]['discrete_and_lastspike_exact']
        assert comparisons[name]['same_engine_repeat_bitwise']
    report['replay_comparisons'] = comparisons
    with (output / 'numerical-contract.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')
    return report
