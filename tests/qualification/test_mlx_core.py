import hashlib
from pathlib import Path

import brian2 as b
import mlx.core as mx
import numpy as np
import pytest
from numpy.typing import ArrayLike, NDArray

from fly_brain.qualification.adapters import brian_reference as reference
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import as_host, evaluate
from fly_brain.simulation.models import NetworkCase as Case
from tests.support.qualification import BoolArray, Harness, events_for, replay_events

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


@pytest.mark.parametrize(
    'voltage,synaptic',
    [(-52, 0), (-50, 0), (-100, -100), (-52, 100), (-52, 1024), (-52, -1024)],
)
def test_isolated_step_preserves_the_coupled_linear_solution(
    voltage: float, synaptic: float
) -> None:
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
    observed = np.array([as_host(v)[0], as_host(g)[0]])
    assert np.all(np.abs(observed - expected) <= 2e-5 + 2e-6 * np.abs(expected))
    if synaptic == 100:
        euler = np.array(
            [voltage + 0.1 * (-52 - voltage + synaptic) / 20, synaptic * 0.98]
        )
        assert np.all(np.abs(euler - expected) > 2e-5 + 2e-6 * np.abs(expected))


def test_ten_thousand_linear_steps_stay_within_the_reviewed_budget(
    harness: Harness,
) -> None:
    b.set_device('runtime')
    b.start_scope()
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'
    params = reference.default_parameters()
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
    runs: list[NDArray[np.float32 | np.float64 | np.int32 | np.int64 | np.bool_]] = []
    for _ in range(2):
        trace: list[mx.array] = []
        with mx.stream(mx.gpu):
            v, g, available = (
                mx.array(initial_v.astype(np.float32)),
                mx.array(initial_g.astype(np.float32)),
                mx.ones((6,), dtype=mx.bool_),
            )
            for _ in range(10000):
                v, g = core.integrate(v, g, available)
                evaluate(v, g)
                trace.append(mx.stack([v, g], axis=-1))
            actual = mx.stack(trace)
            evaluate(actual)
        runs.append(as_host(actual))
    actual = runs[0]
    np.testing.assert_array_equal(actual, runs[1])
    error = np.abs(actual - expected)
    assert np.all(error <= 1e-3 + 1e-5 * np.abs(expected))
    assert tuple(core.COEFFICIENTS) == (
        0.9950124621391296,
        0.9801986813545227,
        0.004937935154885054,
    )
    harness.recorder.record(
        'linear-10000',
        {'reference': expected, 'mlx': actual},
        {
            'steps': 10000,
            'max_abs_error_mv_v_g': error.max(axis=(0, 1)).tolist(),
            'repeat_bit_identical': True,
        },
    )


def threshold_reference(values: ArrayLike, available: ArrayLike) -> BoolArray:
    b.set_device('runtime')
    b.start_scope()
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'
    params = reference.default_parameters()
    group = b.NeuronGroup(
        len(np.asarray(values)),
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
    output = np.zeros(len(np.asarray(values)), dtype=np.bool_)
    output[spikes.i[:]] = True
    return output


def test_strict_threshold_and_neighboring_float32_values() -> None:
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
        observed = as_host(core.threshold_spikes(mx.array(values), mx.array(available)))
    expected = threshold_reference(values, available)
    np.testing.assert_array_equal(observed, expected)
    np.testing.assert_array_equal(observed, [False, False, True, False])


def test_quarter_ulp_rounding_is_an_asserted_precision_limitation(
    harness: Harness,
) -> None:
    value = -45 + float(np.spacing(np.float32(45))) / 4
    expected = threshold_reference([value], [True])
    with mx.stream(mx.gpu):
        observed = as_host(
            core.threshold_spikes(mx.array([value], dtype=mx.float32), mx.array([True]))
        )
    np.testing.assert_array_equal(expected, [True])
    np.testing.assert_array_equal(observed, [False])
    harness.recorder.record(
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
def test_ordinary_network_matches_every_reference_phase(
    name: str,
    case: Case,
    steps: int,
    impulses: tuple[tuple[int, int], ...],
    harness: Harness,
) -> None:
    observed = harness.qualify(name, case, events_for(case, steps, impulses))
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


def test_refractory_boundary_discards_due_at_21_but_accepts_due_at_22(
    harness: Harness,
) -> None:
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
    observed = harness.qualify('refractory-boundary', case, events)
    assert observed['discarded'][21, 0, 0]
    assert observed['accepted'][22, 0, 1]
    assert not observed['due'][22, 0, 0]


REPLAY_CASE = Case(3, (0, 0, 1, 2), (1, 2, 2, 1), (0.275, 100, -0.55, 0.825), (0, 0, 1))


def test_retained_reference_replay_qualifies_exact_events_and_integer_times(
    harness: Harness, project: Path
) -> None:
    retained = np.load(
        project / 'docs/evidence/milestone-0/numerical-contract-replay.npz',
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
    observed = harness.qualify('retained-replay', REPLAY_CASE, events)
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
    harness.recorder.annotate(
        'retained-replay', 'retained_complete_state_and_events_checked', True
    )
    steps = np.nonzero(observed['spikes'])[0]
    milliseconds = steps.astype(np.float64) * core.DT_MS
    np.testing.assert_allclose(
        milliseconds / core.DT_MS, steps, rtol=0, atol=1e-9 / core.DT_MS
    )


def test_chunked_continuation_preserves_pending_edges_and_exact_state(
    harness: Harness,
) -> None:
    events = replay_events(180)
    whole = harness.run_candidate(REPLAY_CASE, events)
    chunked = harness.run_candidate(REPLAY_CASE, events, [1, 17, 1, 18, 40, 103])
    for key, value in whole.items():
        np.testing.assert_array_equal(value, chunked[key])
    harness.recorder.record(
        'chunked-continuation',
        {f'whole_{key}': value for key, value in whole.items()},
        {
            'chunks': [1, 17, 1, 18, 40, 103],
            'all_state_and_discrete_bit_identical': True,
        },
    )


def test_fresh_trials_and_batched_trials_preserve_their_independent_streams(
    harness: Harness,
) -> None:
    events = replay_events(300, trials=3)
    assert not np.array_equal(events[:, 0], events[:, 1])
    assert not np.array_equal(events[:, 1], events[:, 2])
    batch = harness.qualify('batched-trials', REPLAY_CASE, events)
    for trial in range(3):
        standalone = harness.run_candidate(REPLAY_CASE, events[:, trial : trial + 1])
        for key, value in standalone.items():
            np.testing.assert_array_equal(value[:, 0], batch[key][:, trial])


def test_reset_and_frozen_state_are_exact_within_the_engine(harness: Harness) -> None:
    case = Case(
        2, voltage=(-44, -50), synaptic=(1, 1), last_spike=(core.INITIAL_LAST_SPIKE, 0)
    )
    network = harness.network_for(case)
    state = core.initial_state(
        network,
        voltage_mv=case.voltage,
        synaptic_mv=case.synaptic,
        last_spike_step=case.last_spike,
    )
    with mx.stream(mx.gpu):
        updated, trace = core.advance(network, state, mx.zeros((1, 0), dtype=mx.bool_))
        evaluate(*updated[:-1], *trace)
    np.testing.assert_array_equal(as_host(updated.voltage_mv), [[-52, -50]])
    np.testing.assert_array_equal(as_host(updated.synaptic_mv), [[0, 1]])
    np.testing.assert_array_equal(as_host(trace.receiving), [[False, False]])


def test_zero_rate_channel_still_disables_the_target_refractory_duration(
    precision: str,
) -> None:
    network = core.make_network(1, input_targets=[0], precision=precision)
    state = core.initial_state(
        network, voltage_mv=-50, synaptic_mv=1, last_spike_step=0
    )
    with mx.stream(mx.gpu):
        state, first = core.advance(network, state, mx.array([[False]]))
        state, second = core.advance(network, state, mx.array([[False]]))
    np.testing.assert_array_equal(as_host(first.available), [[True]])
    np.testing.assert_array_equal(as_host(second.available), [[True]])


def test_core_keeps_explicit_metal_execution_under_a_cpu_default_stream(
    precision: str,
) -> None:
    with mx.stream(mx.cpu):
        network = core.make_network(
            2, [0], [1], [1], input_targets=[0], precision=precision
        )
        state = core.initial_state(network, voltage_mv=[-44, -52])
        event = mx.array([[False]])
        state, trace = core.advance(network, state, event)
        evaluate(*state[:-1], *trace)
    assert state.voltage_mv.dtype == mx.float32
    assert state.synaptic_mv.dtype == mx.float32
    assert state.last_spike_step.dtype == mx.int32
    assert state.queue.dtype == mx.bool_
    np.testing.assert_array_equal(as_host(trace.spikes), [[True, False]])


def test_unsafe_precision_setting_is_rejected_at_the_network_boundary() -> None:
    with pytest.raises(RuntimeError, match='MLX_ENABLE_TF32=0'):
        core.make_network(1, precision='1')


def test_firing_discards_same_step_recurrent_events_at_both_refractory_durations(
    harness: Harness,
) -> None:
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
    observed = harness.qualify(
        'same-step-recurrent-loss', case, events_for(case, 50, ((3, 0), (21, 1)))
    )
    np.testing.assert_array_equal(observed['spikes'][22, 0, 1:], [True, True])
    np.testing.assert_array_equal(observed['discarded'][22, 0], [True, True])
    np.testing.assert_array_equal(
        observed['before_reset_synaptic_mv'][22, 0, 1:],
        observed['pre_synaptic_mv'][22, 0, 1:],
    )


def test_fresh_state_clears_previous_trial_pending_edges_without_mutating_weights(
    precision: str,
) -> None:
    network = core.make_network(2, [0], [1], [0.275], precision=precision)
    previous = core.initial_state(network, voltage_mv=[-44, -52])
    with mx.stream(mx.gpu):
        previous, _ = core.advance(network, previous, mx.zeros((1, 0), dtype=mx.bool_))
        assert as_host(previous.queue).any()
        fresh = core.initial_state(network)
        assert fresh.step == 0
        assert not as_host(fresh.queue).any()
        np.testing.assert_array_equal(
            as_host(fresh.last_spike_step), core.INITIAL_LAST_SPIKE
        )
        np.testing.assert_array_equal(
            as_host(network.weights_mv), np.array([0.275], dtype=np.float32)
        )
        for _ in range(40):
            fresh, trace = core.advance(
                network, fresh, mx.zeros((1, 0), dtype=mx.bool_)
            )
            evaluate(*fresh[:-1], *trace)
            assert not as_host(trace.due).any()
        np.testing.assert_array_equal(as_host(fresh.voltage_mv), -52)
        np.testing.assert_array_equal(as_host(fresh.synaptic_mv), 0)


def test_large_cancellation_is_an_asserted_accumulation_limit_not_a_parity_pass(
    harness: Harness,
) -> None:
    ordered = np.concatenate((np.full(2048, 2405), [1], np.full(2048, -2405))) * 0.275
    interleaved = np.concatenate((np.tile([2405, -2405], 2048), [1])) * 0.275

    def serial_sum(weights: NDArray[np.float64]) -> float:
        with mx.stream(mx.gpu):
            values = mx.array(weights.astype(np.float32))
            total = mx.array(0, dtype=mx.float32)
            for index in range(len(weights)):
                total = total + values[index]
                if index % 64 == 0:
                    evaluate(total)
            evaluate(total)
        return float(as_host(total))

    serial = serial_sum(ordered)
    assert serial == serial_sum(ordered)
    alternate = serial_sum(interleaved)
    with mx.stream(mx.gpu):
        library = float(as_host(mx.sum(mx.array(ordered.astype(np.float32)))))
    expected = 0.275
    budget = 1e-3 + 1e-5 * abs(expected)
    assert abs(serial - expected) > budget
    assert abs(alternate - expected) <= budget
    u = 2**-24
    gamma = len(ordered) * u / (1 - len(ordered) * u)
    harness.recorder.record(
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
