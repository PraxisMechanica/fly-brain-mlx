import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

import brian2 as b
import mlx.core as mx
import numpy as np
import pytest
from numpy.typing import ArrayLike

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
import mlx_core as core
import run_brian2_cuda as reference


@dataclass(frozen=True)
class Case:
    neurons: int
    sources: tuple[int, ...] = ()
    destinations: tuple[int, ...] = ()
    weights: tuple[float, ...] = ()
    targets: tuple[int, ...] = ()
    silenced: tuple[int, ...] = ()
    voltage: ArrayLike = -52
    synaptic: ArrayLike = 0
    last_spike: ArrayLike = core.INITIAL_LAST_SPIKE


MEASUREMENTS = {}


@pytest.fixture(scope='module', autouse=True)
def qualification_environment():
    assert os.environ.get('MLX_ENABLE_TF32') == '0'
    assert importlib.metadata.version('mlx') == '0.32.3'
    assert importlib.metadata.version('mlx-metal') == '0.32.3'
    assert np.__version__ == '1.26.4'
    assert mx.metal.is_available()
    yield
    destination = os.environ.get('MLX_QUALIFICATION_OUTPUT')
    if destination:
        report = {
            'execution': 'uncompiled, explicit Metal stream, ordered edge/channel additions',
            'mlx': importlib.metadata.version('mlx'),
            'mlx_metal': importlib.metadata.version('mlx-metal'),
            'brian2': b.__version__,
            'numpy': np.__version__,
            'python': platform.python_version(),
            'platform': platform.platform(),
            'device': mx.device_info(),
            'MLX_ENABLE_TF32': os.environ['MLX_ENABLE_TF32'],
            'coefficients_float32': dict(zip('abc', core.COEFFICIENTS)),
            'measurements': MEASUREMENTS,
        }
        with (Path(destination) / 'measurements.json').open('x') as output:
            json.dump(report, output, indent=2)
            output.write('\n')


def events_for(case, steps, impulses=(), trials=1):
    events = np.zeros((steps, trials, len(case.targets)), dtype=np.bool_)
    for step, channel in impulses:
        events[step, :, channel] = True
    return events


def record(name, arrays, measurements):
    MEASUREMENTS[name] = measurements
    destination = os.environ.get('MLX_QUALIFICATION_OUTPUT')
    if destination:
        with (Path(destination) / f'{name}.npz').open('xb') as output:
            np.savez_compressed(output, **arrays)


def run_reference(case, events):
    trials = events.shape[1]
    output = []
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
        params = dict(reference.default_params)
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
        objects = [group]
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
        for spike_step, neuron in zip(spike_steps, spikes.i[:]):
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


def network_for(case):
    return core.make_network(
        case.neurons,
        case.sources,
        case.destinations,
        case.weights,
        case.targets,
        case.silenced,
    )


def run_candidate(case, events, chunks=None):
    network = network_for(case)
    state = core.initial_state(
        network, events.shape[1], case.voltage, case.synaptic, case.last_spike
    )
    with mx.stream(mx.gpu):
        inputs = mx.array(events)
    rows = {name: [] for name in core.StepTrace._fields}
    rows.update({name: [] for name in core.State._fields[:-1]})
    for length in chunks or [len(events)]:
        end = state.step + length
        while state.step < end:
            with mx.stream(mx.gpu):
                state, trace = core.advance(network, state, inputs[state.step])
                mx.eval(*state[:-1], *trace)
            for name, value in zip(core.StepTrace._fields, trace):
                rows[name].append(value)
            for name, value in zip(core.State._fields[:-1], state[:-1]):
                rows[name].append(value)
    assert state.step == len(events)
    with mx.stream(mx.gpu):
        arrays = {name: mx.stack(values) for name, values in rows.items()}
        mx.eval(*arrays.values())
    result = {name: np.asarray(value) for name, value in arrays.items()}
    result['queue'] = np.swapaxes(result['queue'], 1, 2)
    return result


def qualify(name, case, events):
    expected = run_reference(case, events)
    observed = run_candidate(case, events)
    errors = {}
    for key, wanted in expected.items():
        actual = observed[key]
        if key.endswith('_mv'):
            assert np.all(np.isfinite(actual))
            error = np.abs(actual - wanted)
            budget = 1e-3 + 1e-5 * np.abs(wanted)
            assert np.all(error <= budget), (
                name,
                key,
                np.unravel_index(error.argmax(), error.shape),
            )
            errors[key] = float(error.max(initial=0))
        else:
            np.testing.assert_array_equal(actual, wanted, err_msg=f'{name}: {key}')
    margin = np.abs(expected['pre_voltage_mv'] + 45)
    budget = 1e-3 + 1e-5 * np.abs(expected['pre_voltage_mv'])
    assert np.all(margin[expected['available']] > budget[expected['available']])
    assert np.max(np.abs(expected['voltage_mv'])) <= 256
    assert np.max(np.abs(expected['synaptic_mv'])) <= 1024
    for neuron in range(case.neurons):
        assert sum(destination == neuron for destination in case.destinations) <= 32
    repeat = run_candidate(case, events)
    for key, value in observed.items():
        np.testing.assert_array_equal(
            value, repeat[key], err_msg=f'{name}: repeat {key}'
        )
    record(
        name,
        {
            **{f'reference_{key}': value for key, value in expected.items()},
            **{f'mlx_{key}': value for key, value in observed.items()},
            'events': events,
        },
        {
            'steps': len(events),
            'trials': events.shape[1],
            'spikes': int(observed['spikes'].sum()),
            'max_abs_error_mv': errors,
            'exact_discrete_parity': True,
            'repeat_bit_identical': True,
            'minimum_available_threshold_margin_mv': float(
                margin[expected['available']].min(initial=np.inf)
            ),
        },
    )
    return observed


@pytest.mark.parametrize(
    'voltage,synaptic',
    [(-52, 0), (-50, 0), (-100, -100), (-52, 100), (-52, 1024), (-52, -1024)],
)
def test_isolated_step_preserves_the_coupled_linear_solution(voltage, synaptic):
    a = np.exp(-0.1 / 20)
    decay = np.exp(-0.1 / 5)
    coupling = a * -np.expm1(-0.1 * (1 / 5 - 1 / 20)) / 3
    expected = np.array(
        [-52 + a * (voltage + 52) + coupling * synaptic, decay * synaptic]
    )
    with mx.stream(mx.gpu):
        v, g = core.integrate(
            mx.array([voltage], dtype=mx.float32),
            mx.array([synaptic], dtype=mx.float32),
            mx.array([True]),
        )
    observed = np.array([np.asarray(v)[0], np.asarray(g)[0]])
    assert np.all(np.abs(observed - expected) <= 2e-5 + 2e-6 * np.abs(expected))
    if synaptic == 100:
        euler = np.array(
            [voltage + 0.1 * (-52 - voltage + synaptic) / 20, synaptic * 0.98]
        )
        assert np.all(np.abs(euler - expected) > 2e-5 + 2e-6 * np.abs(expected))


def test_ten_thousand_linear_steps_stay_within_the_reviewed_budget():
    b.set_device('runtime')
    b.start_scope()
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'
    params = dict(reference.default_params)
    group = b.NeuronGroup(
        6, params['eqs'], method='linear', refractory='rfc', namespace=params
    )
    initial_v = np.array([-52, -50, -100, -52, -52, -52], dtype=np.float64)
    initial_g = np.array([0, 0, -100, 100, 1024, -1024], dtype=np.float64)
    group.v, group.g, group.rfc = initial_v * b.mV, initial_g * b.mV, 0 * b.ms
    monitor = b.StateMonitor(group, ('v', 'g'), record=True, when='end')
    b.Network(group, monitor).run(1000 * b.ms)
    expected = np.stack((monitor.v[:] / b.mV, monitor.g[:] / b.mV), axis=-1).transpose(
        1, 0, 2
    )
    runs = []
    for _ in range(2):
        trace = []
        with mx.stream(mx.gpu):
            v, g, available = (
                mx.array(initial_v.astype(np.float32)),
                mx.array(initial_g.astype(np.float32)),
                mx.ones((6,), dtype=mx.bool_),
            )
            for _ in range(10000):
                v, g = core.integrate(v, g, available)
                mx.eval(v, g)
                trace.append(mx.stack((v, g), axis=-1))
            actual = mx.stack(trace)
            mx.eval(actual)
        runs.append(np.asarray(actual))
    actual = runs[0]
    np.testing.assert_array_equal(actual, runs[1])
    error = np.abs(actual - expected)
    assert np.all(error <= 1e-3 + 1e-5 * np.abs(expected))
    assert tuple(core.COEFFICIENTS) == (
        0.9950124621391296,
        0.9801986813545227,
        0.004937935154885054,
    )
    record(
        'linear-10000',
        {'reference': expected, 'mlx': actual},
        {
            'steps': 10000,
            'max_abs_error_mv_v_g': error.max(axis=(0, 1)).tolist(),
            'repeat_bit_identical': True,
        },
    )


def threshold_reference(values, available):
    b.set_device('runtime')
    b.start_scope()
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'
    params = dict(reference.default_params)
    group = b.NeuronGroup(
        len(values),
        params['eqs'],
        method='linear',
        threshold=params['eq_th'],
        reset=params['eq_rst'],
        refractory='rfc',
        namespace=params,
    )
    group.v = np.asarray(values) * b.mV
    group.g = 0 * b.mV
    group.not_refractory = available
    group.rfc = 0 * b.ms
    group.state_updater.active = False
    spikes = b.SpikeMonitor(group)
    b.Network(group, spikes).run(0.1 * b.ms)
    output = np.zeros(len(values), dtype=np.bool_)
    output[spikes.i[:]] = True
    return output


def test_strict_threshold_and_neighboring_float32_values():
    values = np.array(
        [
            np.nextafter(np.float32(-45), np.float32(-np.inf)),
            -45,
            np.nextafter(np.float32(-45), np.float32(np.inf)),
            -44,
        ],
        dtype=np.float32,
    )
    available = np.array([True, True, True, False])
    with mx.stream(mx.gpu):
        observed = np.asarray(
            core.threshold_spikes(mx.array(values), mx.array(available))
        )
    expected = threshold_reference(values, available)
    np.testing.assert_array_equal(observed, expected)
    np.testing.assert_array_equal(observed, [False, False, True, False])


def test_quarter_ulp_rounding_is_an_asserted_precision_limitation():
    value = -45 + float(np.spacing(np.float32(45))) / 4
    expected = threshold_reference([value], [True])
    with mx.stream(mx.gpu):
        observed = np.asarray(
            core.threshold_spikes(mx.array([value], dtype=mx.float32), mx.array([True]))
        )
    np.testing.assert_array_equal(expected, [True])
    np.testing.assert_array_equal(observed, [False])
    record(
        'threshold-rounding-limitation',
        {'reference_spikes': expected, 'mlx_spikes': observed},
        {
            'input_mv': value,
            'expected_difference': True,
            'universal_float64_spike_equivalence': False,
        },
    )


@pytest.mark.parametrize(
    'name,case,steps,impulses',
    [
        ('rest-empty', Case(2), 60, ()),
        (
            'reset-weights',
            Case(2, (0,), (1,), (1,), voltage=(-44, -52), synaptic=(1, 0)),
            60,
            (),
        ),
        (
            'positive-negative',
            Case(3, (0, 0), (1, 2), (4, -4), voltage=(-44, -52, -52)),
            80,
            (),
        ),
        (
            'balanced-duplicates',
            Case(
                4,
                (0, 1, 0, 1),
                (2, 2, 3, 3),
                (1.1, -1.1, 0.275, 0.275),
                voltage=(-44, -44, -52, -52),
            ),
            80,
            (),
        ),
        (
            'fanout-self-wrap',
            Case(3, (0, 0, 0), (0, 1, 2), (1, 2, -2), (0,)),
            160,
            ((0, 0), (25, 0), (50, 0), (75, 0), (100, 0)),
        ),
        ('refractory-held', Case(1, voltage=-50, synaptic=1, last_spike=0), 40, ()),
        (
            'target-released-at-arrival',
            Case(
                2,
                (0,),
                (1,),
                (1,),
                voltage=(-44, -50),
                synaptic=(0, 1),
                last_spike=(core.INITIAL_LAST_SPIKE, -10),
            ),
            50,
            (),
        ),
        (
            'zero-refractory-loss',
            Case(1, targets=(0,)),
            12,
            tuple((step, 0) for step in range(12)),
        ),
        (
            'outgoing-silencing',
            Case(
                3,
                (0, 1, 2),
                (1, 2, 1),
                (100, 3, 2),
                silenced=(1,),
                voltage=(-44, -52, -52),
            ),
            80,
            (),
        ),
        (
            'classes-overlap-zero-rate',
            Case(2, targets=(0, 0, 1)),
            80,
            ((0, 0), (0, 1), (5, 0), (12, 1), (24, 0), (24, 1)),
        ),
        (
            'thirty-two-event-fanin',
            Case(
                2,
                (0,) * 32,
                (1,) * 32,
                (0.275, -0.275) * 15 + (0.55, 0.275),
                voltage=(-44, -52),
            ),
            80,
            (),
        ),
    ],
)
def test_ordinary_network_matches_every_reference_phase(name, case, steps, impulses):
    observed = qualify(name, case, events_for(case, steps, impulses))
    if name == 'rest-empty':
        assert not observed['spikes'].any()
    if name == 'refractory-held':
        np.testing.assert_array_equal(
            observed['voltage_mv'][:22], np.full((22, 1, 1), -50)
        )
        np.testing.assert_array_equal(observed['synaptic_mv'][:22], np.ones((22, 1, 1)))
    if name == 'target-released-at-arrival':
        assert observed['accepted'][18, 0, 0]
    if name == 'zero-refractory-loss':
        np.testing.assert_array_equal(
            np.flatnonzero(observed['spikes'][:, 0, 0]), [1, 3, 5, 7, 9, 11]
        )
    if name == 'outgoing-silencing':
        assert observed['spikes'][:, 0, 1].any()
        assert np.max(observed['synaptic_mv'][:, 0, 1]) > 0
        assert not observed['spikes'][:, 0, 2].any()
        np.testing.assert_array_equal(observed['synaptic_mv'][:, 0, 2], 0)


def test_refractory_boundary_discards_due_at_21_but_accepts_due_at_22():
    case = Case(
        3,
        (0, 1),
        (2, 2),
        (1, 2),
        (0, 1),
        voltage=(-52, -52, -50),
        synaptic=(0, 0, 1),
        last_spike=(core.INITIAL_LAST_SPIKE, core.INITIAL_LAST_SPIKE, 0),
    )
    events = events_for(case, 50, ((2, 0), (3, 1)))
    observed = qualify('refractory-boundary', case, events)
    assert observed['discarded'][21, 0, 0]
    assert observed['accepted'][22, 0, 1]
    assert not observed['due'][22, 0, 0]


def replay_events(steps=1000, trials=1):
    return np.stack(
        [
            (
                np.random.Generator(
                    np.random.PCG64(np.random.SeedSequence([20261004, 2, trial]))
                ).random((steps, 3), dtype=np.float64)
                < np.array([200, 100, 0]) * 1e-4
            )
            for trial in range(trials)
        ],
        axis=1,
    )


REPLAY_CASE = Case(3, (0, 0, 1, 2), (1, 2, 2, 1), (0.275, 100, -0.55, 0.825), (0, 0, 1))


def test_retained_reference_replay_qualifies_exact_events_and_integer_times():
    retained = np.load(
        Path(__file__).resolve().parents[1]
        / 'docs/evidence/milestone-0/numerical-contract-replay.npz',
        allow_pickle=False,
    )
    events = replay_events()
    stored_key = next(
        key for key in retained.files if 'stimulus' in key or 'events' in key
    )
    np.testing.assert_array_equal(events[:, 0].astype(np.uint8), retained[stored_key])
    assert (
        hashlib.sha256(events[:, 0].astype(np.uint8).tobytes()).hexdigest()
        == 'f1da12a8a7f3a44198fe04a385f897f991eadea36f680bf5d668ed19343fa09d'
    )
    np.testing.assert_array_equal(events[:100], replay_events(100))
    observed = qualify('retained-replay', REPLAY_CASE, events)
    assert observed['spikes'].sum() == 43
    for name in ('voltage_mv', 'synaptic_mv'):
        wanted = retained[name].T
        error = np.abs(observed[name][:, 0] - wanted)
        assert np.all(error <= 1e-3 + 1e-5 * np.abs(wanted))
    np.testing.assert_array_equal(
        observed['receiving'][:, 0], retained['not_refractory'].T
    )
    np.testing.assert_array_equal(
        observed['last_spike_step'][:, 0],
        np.rint(retained['lastspike_ms'].T / 0.1).astype(np.int32),
    )
    retained_steps, _, retained_neurons = np.nonzero(observed['spikes'])
    np.testing.assert_array_equal(retained_steps, retained['spike_steps'])
    np.testing.assert_array_equal(retained_neurons, retained['spike_neurons'])
    MEASUREMENTS['retained-replay']['retained_complete_state_and_events_checked'] = True
    steps = np.nonzero(observed['spikes'])[0]
    milliseconds = steps.astype(np.float64) * core.DT_MS
    np.testing.assert_allclose(
        milliseconds / core.DT_MS, steps, rtol=0, atol=1e-9 / core.DT_MS
    )


def test_chunked_continuation_preserves_pending_edges_and_exact_state():
    events = replay_events(180)
    whole = run_candidate(REPLAY_CASE, events)
    chunked = run_candidate(REPLAY_CASE, events, [1, 17, 1, 18, 40, 103])
    for key, value in whole.items():
        np.testing.assert_array_equal(value, chunked[key])
    record(
        'chunked-continuation',
        {f'whole_{key}': value for key, value in whole.items()},
        {
            'chunks': [1, 17, 1, 18, 40, 103],
            'all_state_and_discrete_bit_identical': True,
        },
    )


def test_fresh_trials_and_batched_trials_preserve_their_independent_streams():
    events = replay_events(300, trials=3)
    assert not np.array_equal(events[:, 0], events[:, 1])
    assert not np.array_equal(events[:, 1], events[:, 2])
    batch = qualify('batched-trials', REPLAY_CASE, events)
    for trial in range(3):
        standalone = run_candidate(REPLAY_CASE, events[:, trial : trial + 1])
        for key, value in standalone.items():
            np.testing.assert_array_equal(value[:, 0], batch[key][:, trial])


def test_reset_and_frozen_state_are_exact_within_the_engine():
    case = Case(
        2, voltage=(-44, -50), synaptic=(1, 1), last_spike=(core.INITIAL_LAST_SPIKE, 0)
    )
    network = network_for(case)
    state = core.initial_state(
        network,
        voltage_mv=case.voltage,
        synaptic_mv=case.synaptic,
        last_spike_step=case.last_spike,
    )
    with mx.stream(mx.gpu):
        updated, trace = core.advance(network, state, mx.zeros((1, 0), dtype=mx.bool_))
        mx.eval(*updated[:-1], *trace)
    np.testing.assert_array_equal(np.asarray(updated.voltage_mv), [[-52, -50]])
    np.testing.assert_array_equal(np.asarray(updated.synaptic_mv), [[0, 1]])
    np.testing.assert_array_equal(np.asarray(trace.receiving), [[False, False]])


def test_zero_rate_channel_still_disables_the_target_refractory_duration():
    network = core.make_network(1, input_targets=[0])
    state = core.initial_state(
        network, voltage_mv=-50, synaptic_mv=1, last_spike_step=0
    )
    with mx.stream(mx.gpu):
        state, first = core.advance(network, state, mx.array([[False]]))
        state, second = core.advance(network, state, mx.array([[False]]))
    np.testing.assert_array_equal(np.asarray(first.available), [[True]])
    np.testing.assert_array_equal(np.asarray(second.available), [[True]])


def test_core_keeps_explicit_metal_execution_under_a_cpu_default_stream():
    with mx.stream(mx.cpu):
        network = core.make_network(2, [0], [1], [1], input_targets=[0])
        state = core.initial_state(network, voltage_mv=[-44, -52])
        event = mx.array([[False]])
        state, trace = core.advance(network, state, event)
        mx.eval(*state[:-1], *trace)
    assert state.voltage_mv.dtype == mx.float32
    assert state.synaptic_mv.dtype == mx.float32
    assert state.last_spike_step.dtype == mx.int32
    assert state.queue.dtype == mx.bool_
    np.testing.assert_array_equal(np.asarray(trace.spikes), [[True, False]])


def test_unsafe_precision_setting_is_rejected_at_the_network_boundary(monkeypatch):
    monkeypatch.setenv('MLX_ENABLE_TF32', '1')
    with pytest.raises(RuntimeError, match='MLX_ENABLE_TF32=0'):
        core.make_network(1)


def test_firing_discards_same_step_recurrent_events_at_both_refractory_durations():
    case = Case(
        3,
        (0, 0),
        (1, 2),
        (3, 3),
        (0, 1),
        voltage=(-52, -52, -44),
        synaptic=(0, 0, 1),
        last_spike=(core.INITIAL_LAST_SPIKE, core.INITIAL_LAST_SPIKE, 0),
    )
    observed = qualify(
        'same-step-recurrent-loss', case, events_for(case, 50, ((3, 0), (21, 1)))
    )
    np.testing.assert_array_equal(observed['spikes'][22, 0, 1:], [True, True])
    np.testing.assert_array_equal(observed['discarded'][22, 0], [True, True])
    np.testing.assert_array_equal(
        observed['before_reset_synaptic_mv'][22, 0, 1:],
        observed['pre_synaptic_mv'][22, 0, 1:],
    )


def test_fresh_state_clears_previous_trial_pending_edges_without_mutating_weights():
    network = core.make_network(2, [0], [1], [0.275])
    previous = core.initial_state(network, voltage_mv=[-44, -52])
    with mx.stream(mx.gpu):
        previous, _ = core.advance(network, previous, mx.zeros((1, 0), dtype=mx.bool_))
        assert np.asarray(previous.queue).any()
        fresh = core.initial_state(network)
        assert fresh.step == 0
        assert not np.asarray(fresh.queue).any()
        np.testing.assert_array_equal(
            np.asarray(fresh.last_spike_step), core.INITIAL_LAST_SPIKE
        )
        np.testing.assert_array_equal(
            np.asarray(network.weights_mv), np.array([0.275], dtype=np.float32)
        )
        for _ in range(40):
            fresh, trace = core.advance(
                network, fresh, mx.zeros((1, 0), dtype=mx.bool_)
            )
            mx.eval(*fresh[:-1], *trace)
            assert not np.asarray(trace.due).any()
        np.testing.assert_array_equal(np.asarray(fresh.voltage_mv), -52)
        np.testing.assert_array_equal(np.asarray(fresh.synaptic_mv), 0)


def test_large_cancellation_is_an_asserted_accumulation_limit_not_a_parity_pass():
    ordered = np.concatenate((np.full(2048, 2405), [1], np.full(2048, -2405))) * 0.275
    interleaved = np.concatenate((np.tile([2405, -2405], 2048), [1])) * 0.275

    def serial_sum(weights):
        with mx.stream(mx.gpu):
            values = mx.array(weights.astype(np.float32))
            total = mx.array(0, dtype=mx.float32)
            for index in range(len(weights)):
                total = total + values[index]
                if index % 64 == 0:
                    mx.eval(total)
            mx.eval(total)
        return float(total.item())

    serial = serial_sum(ordered)
    assert serial == serial_sum(ordered)
    alternate = serial_sum(interleaved)
    with mx.stream(mx.gpu):
        library = float(mx.sum(mx.array(ordered.astype(np.float32))).item())
    expected = 0.275
    budget = 1e-3 + 1e-5 * abs(expected)
    assert abs(serial - expected) > budget
    assert abs(alternate - expected) <= budget
    u = 2**-24
    gamma = len(ordered) * u / (1 - len(ordered) * u)
    record(
        'accumulation-limit',
        {'ordered_weights_mv': ordered, 'interleaved_weights_mv': interleaved},
        {
            'events': len(ordered),
            'expected_real_sum_mv': expected,
            'serial_mlx_mv': serial,
            'interleaved_serial_mlx_mv': alternate,
            'mlx_sum_mv': library,
            'trajectory_budget_mv': budget,
            'serial_qualifies': False,
            'serial_repeat_bit_identical': True,
            'sum_abs_weights_mv': float(np.abs(ordered).sum()),
            'gamma_m_sum_abs_mv': float(gamma * np.abs(ordered).sum()),
            'connectome_accumulation_approved': False,
        },
    )
