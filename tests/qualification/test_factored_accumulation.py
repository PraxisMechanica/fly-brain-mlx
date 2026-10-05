from collections.abc import Sequence
from typing import cast

import mlx.core as mx
import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_replay import run_reference
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.accumulation import SCALE
from fly_brain.simulation.backend.arrays import as_host
from fly_brain.simulation.backend.engines import Factory, factored
from fly_brain.simulation.models import NetworkCase as Case
from tests.support.bucketed import bucketed_case, exact_bucketed_case
from tests.support.qualification import Harness, events_for, replay_events

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]
INITIAL = core.INITIAL_LAST_SPIKE


@pytest.fixture(
    scope='module',
    params=(factored, bucketed_case, exact_bucketed_case),
)
def compiler(request: pytest.FixtureRequest) -> Factory:
    return cast(Factory, request.param)


def weights(counts: Sequence[int]) -> tuple[float, ...]:
    return tuple(float(value) for value in np.asarray(counts, dtype=np.int64) * SCALE)


@pytest.mark.parametrize(
    'name,case,steps,impulses',
    [
        ('rest-empty', Case(2), 60, ()),
        (
            'reset-weights',
            Case(2, (0,), (1,), weights([4]), voltage=(-44, -52), synaptic=(1, 0)),
            60,
            (),
        ),
        (
            'positive-negative',
            Case(3, (0, 0), (1, 2), weights([15, -15]), voltage=(-44, -52, -52)),
            80,
            (),
        ),
        (
            'balanced-duplicates',
            Case(
                4,
                (0, 1, 0, 1),
                (2, 2, 3, 3),
                weights([4, -4, 1, 1]),
                voltage=(-44, -44, -52, -52),
            ),
            80,
            (),
        ),
        (
            'cast-drift-triplet',
            Case(
                2, (0, 0, 0), (1, 1, 1), weights([2405, -2404, -1]), voltage=(-44, -52)
            ),
            60,
            (),
        ),
        (
            'fanout-self-wrap',
            Case(3, (0, 0, 0), (0, 1, 2), weights([4, 7, -7]), (0,)),
            160,
            ((0, 0), (25, 0), (50, 0), (75, 0), (100, 0)),
        ),
        ('refractory-held', Case(1, voltage=-50, synaptic=1, last_spike=0), 40, ()),
        (
            'released-at-arrival',
            Case(
                2,
                (0,),
                (1,),
                weights([4]),
                voltage=(-44, -50),
                synaptic=(0, 1),
                last_spike=(INITIAL, -10),
            ),
            50,
            (),
        ),
        (
            'outgoing-silencing',
            Case(
                3,
                (0, 1, 2),
                (1, 2, 1),
                weights([364, 11, 7]),
                silenced=(1,),
                voltage=(-44, -52, -52),
            ),
            80,
            (),
        ),
        (
            'overlapping-inputs',
            Case(2, targets=(0, 0, 1)),
            80,
            ((0, 0), (0, 1), (5, 0), (12, 1), (24, 0), (24, 1)),
        ),
        (
            'zero-refractory-loss',
            Case(1, targets=(0,)),
            12,
            tuple((step, 0) for step in range(12)),
        ),
        (
            '32-edge-fanin',
            Case(
                2,
                (0,) * 32,
                (1,) * 32,
                weights([1, -1] * 15 + [2, 1]),
                voltage=(-44, -52),
            ),
            80,
            (),
        ),
    ],
)
def test_factored_network_matches_reference_phases(
    name: str,
    case: Case,
    steps: int,
    impulses: tuple[tuple[int, int], ...],
    harness: Harness,
) -> None:
    observed = harness.qualify(name, case, events_for(case, steps, impulses))
    if name == 'cast-drift-triplet':
        assert abs(observed['synaptic_mv'][18, 0, 1]) <= 2e-5
    if name == 'outgoing-silencing':
        assert observed['spikes'][:, 0, 1].any()
        assert not observed['spikes'][:, 0, 2].any()
    if name == 'released-at-arrival':
        assert observed['accepted'][18, 0, 0]


def test_factored_refractory_boundary_and_firing_step_discard_events(
    harness: Harness,
) -> None:
    case = Case(
        3,
        (0, 1),
        (2, 2),
        weights([4, 7]),
        (0, 1),
        voltage=(-52, -52, -50),
        synaptic=(0, 0, 1),
        last_spike=(INITIAL, INITIAL, 0),
    )
    observed = harness.qualify('boundary', case, events_for(case, 50, ((2, 0), (3, 1))))
    assert observed['discarded'][21, 0, 0]
    assert observed['accepted'][22, 0, 1]
    assert not observed['due'][22, 0, 0]
    case = Case(
        3,
        (0, 0),
        (1, 2),
        weights([11, 11]),
        (0, 1),
        voltage=(-52, -52, -44),
        synaptic=(0, 0, 1),
        last_spike=(INITIAL, INITIAL, 0),
    )
    observed = harness.qualify(
        'same-step-loss', case, events_for(case, 50, ((3, 0), (21, 1)))
    )
    np.testing.assert_array_equal(observed['spikes'][22, 0, 1:], [True, True])
    np.testing.assert_array_equal(observed['discarded'][22, 0], [True, True])


REPLAY = Case(3, (0, 0, 1, 2), (1, 2, 2, 1), weights([1, 364, -2, 3]), (0, 0, 1))


def test_factored_replay_preserves_reference_states_and_events(
    harness: Harness,
) -> None:
    harness.qualify('replay-1000', REPLAY, replay_events())


def test_factored_batch_and_chunked_runs_preserve_complete_state(
    harness: Harness,
) -> None:
    events = replay_events(180, trials=3)
    batch = harness.qualify('batch-chunks', REPLAY, events)
    chunked = harness.run_candidate(REPLAY, events, [1, 17, 1, 18, 40, 103])
    for key, value in batch.items():
        np.testing.assert_array_equal(value, chunked[key])
    for trial in range(3):
        standalone = harness.run_candidate(REPLAY, events[:, trial : trial + 1])
        for key, value in standalone.items():
            np.testing.assert_array_equal(value[:, 0], batch[key][:, trial])


@pytest.mark.parametrize(
    'name,counts',
    [
        ('retained-large', [2405] * 2048 + [1] + [-2405] * 2048),
        ('cast-drift-large', [2405, -2404, -1] * 128),
    ],
)
def test_factored_large_fanin_meets_delayed_reference_trace(
    name: str, counts: list[int], harness: Harness
) -> None:
    case = Case(
        2, (0,) * len(counts), (1,) * len(counts), weights(counts), voltage=(-44, -52)
    )
    events = events_for(case, 40)
    expected = run_reference(case, events)
    observed = harness.run_candidate(case, events)
    repeated = harness.run_candidate(case, events)
    errors = {}
    for key, wanted in expected.items():
        if key.endswith('_mv'):
            error = np.abs(
                np.asarray(observed[key], dtype=np.float64)
                - np.asarray(wanted, dtype=np.float64)
            )
            assert np.all(error <= 1e-3 + 1e-5 * np.abs(wanted))
            errors[key] = float(error.max(initial=0))
        else:
            np.testing.assert_array_equal(observed[key], wanted)
    for key in observed:
        np.testing.assert_array_equal(observed[key], repeated[key])
    assert observed['accepted'][18, 0].all()
    assert not observed['due'][:18].any()
    state = expected['before_reset_synaptic_mv'][18]
    assert np.all(
        np.abs(observed['before_reset_synaptic_mv'][18] - state)
        <= 2e-5 + 2e-6 * np.abs(state)
    )
    harness.recorder.record(
        name,
        {
            **{f'reference_{key}': value for key, value in expected.items()},
            **{f'mlx_{key}': value for key, value in observed.items()},
            'events': events,
        },
        {
            'steps': 40,
            'edges': len(counts),
            'max_abs_error_mv': errors,
            'exact_discrete_parity': True,
            'repeat_bit_identical': True,
        },
    )


def test_factored_adapter_uses_metal_with_cpu_default_and_resets_pending_trials(
    harness: Harness,
) -> None:
    with mx.stream(mx.cpu):
        execution = harness.compile(Case(2, (0,), (1,), weights([1])))
        network = execution.network
        state = core.initial_state(network, voltage_mv=[-44, -52])
        state, trace = execution.advance(state, mx.zeros((1, 0), dtype=mx.bool_))
        assert as_host(state.queue).any()
        fresh = core.initial_state(network)
        assert not as_host(fresh.queue).any()
        fresh, _ = execution.advance(fresh, mx.zeros((1, 0), dtype=mx.bool_))
        np.testing.assert_array_equal(as_host(fresh.synaptic_mv), 0)
        np.testing.assert_array_equal(as_host(trace.spikes), [[True, False]])
