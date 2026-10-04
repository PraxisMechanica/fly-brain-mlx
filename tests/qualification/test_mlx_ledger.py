from pathlib import Path
from typing import cast

import mlx.core as mx
import numpy as np
import pytest

from fly_brain.qualification.adapters.mlx_ledger import CHECK_NAMES, EventLedger
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import as_host, boolean_input, evaluate
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.models import Connectome

pytestmark = [pytest.mark.integration, pytest.mark.metal]


def connectome(empty: bool = False) -> Connectome:
    counts = np.array([] if empty else [360, 0, 1, -2, 3, 360, -1, -1], dtype=np.int32)
    return Connectome(
        np.arange(6, dtype=np.int64),
        np.array([] if empty else [0, 0, 0, 1, 2, 3, 4, 4], dtype=np.int32),
        np.array([] if empty else [1, 1, 0, 2, 3, 0, 5, 5], dtype=np.int32),
        counts,
        counts.astype(np.float64) * 0.275,
    )


@pytest.mark.parametrize('trials', [1, 4])
@pytest.mark.parametrize('empty', [False, True])
def test_actual_device_queues_and_gates_agree_with_bounded_spike_history(
    precision: str, trials: int, empty: bool, request: pytest.FixtureRequest
) -> None:
    original = connectome(empty)
    targets = () if empty else (0, 0, 1)
    execution = prepare(original, targets, (3,), precision)
    last = np.full((trials, 6), -100000000, dtype=np.int32)
    last[:, 5] = np.arange(trials) - 10
    state = core.initial_state(
        execution.network,
        trials,
        voltage_mv=(-52, -52, -44, -44, -44, -52),
        synaptic_mv=(0, 0, 100, 0, 0, 0),
        last_spike_step=last,
    )
    ledger = EventLedger(original, targets, trials, last)
    events = np.zeros((101, trials, len(targets)), dtype=np.bool_)
    if targets:
        for trial in range(trials):
            events[trial::3, trial, 0] = True
            events[trial::7, trial, 1] = True
            events[trial::4, trial, 2] = True
    with mx.stream(mx.gpu):
        inputs = boolean_input(events)
    rows: dict[str, list[mx.array]] = {name: [] for name in core.State._fields[:-1]}
    rows.update({name: [] for name in core.StepTrace._fields})
    flags: list[mx.array] = []
    for step in range(len(events)):
        state, trace = execution.advance(state, inputs[step])
        checks = ledger.check(state, trace, inputs[step])
        with mx.stream(mx.gpu):
            evaluate(*state[:-1], *trace, checks)
        flags.append(checks)
        for name, value in zip(core.State._fields[:-1], state[:-1], strict=True):
            rows[name].append(value)
        for name, value in zip(core.StepTrace._fields, trace, strict=True):
            rows[name].append(value)
    with mx.stream(mx.gpu):
        observed = np.asarray(mx.stack(flags), dtype=np.bool_)
        arrays = {name: as_host(mx.stack(values)) for name, values in rows.items()}
    assert observed.shape == (101, trials, 30) and observed.all()
    assert len(ledger.history) == 19
    assert all(value.shape == (trials, 6) for value in ledger.history)
    if not empty:
        assert arrays['due'][:, :, [1, 5]].any()
        assert arrays['accepted'].any() and arrays['discarded'].any()
        assert arrays['queue'][-1].any()
    destination = cast(str | None, request.config.getoption('--artifact-output'))
    if destination is not None:
        output = Path(destination)
        output.mkdir(parents=True, exist_ok=True)
        with (output / f'mlx-ledger-{trials}-{empty}.npz').open('xb') as artifact:
            np.savez_compressed(
                artifact,
                **arrays,
                checks=observed,
                events=events,
                original_sources=original.sources,
                original_destinations=original.destinations,
                original_counts=original.counts,
                initial_last=last,
            )


@pytest.mark.parametrize(
    'field,check',
    [
        ('available', 'available'),
        ('spikes', 'threshold'),
        ('receiving', 'receiving'),
        ('due', 'due'),
        ('accepted', 'accepted'),
        ('discarded', 'discarded'),
        ('accepted_inputs', 'accepted_inputs'),
        ('last_spike_step', 'last_spike_step'),
    ],
)
def test_ledger_detects_changed_discrete_state_and_delivery_bits(
    precision: str, field: str, check: str
) -> None:
    original = connectome()
    targets = (0, 0, 1)
    execution = prepare(original, targets, (), precision)
    state = core.initial_state(execution.network, voltage_mv=-44)
    with mx.stream(mx.gpu):
        events = mx.ones((1, 3), dtype=mx.bool_)
    state, trace = execution.advance(state, events)
    ledger = EventLedger(original, targets, 1)
    with mx.stream(mx.gpu):
        if field == 'last_spike_step':
            positions = mx.arange(6)[None, :] == 0
            state = state._replace(
                last_spike_step=state.last_spike_step + positions.astype(mx.int32)
            )
        else:
            value = cast(mx.array, getattr(trace, field))
            changed = mx.where(mx.arange(value.shape[1])[None, :] == 0, ~value, value)
            trace = trace._replace(**{field: changed})
        flags = np.asarray(ledger.check(state, trace, events), dtype=np.bool_)
    assert not flags[0, CHECK_NAMES.index(check)]


@pytest.mark.parametrize('slot', [0, 18])
def test_ledger_detects_changed_pending_and_consumed_queue_slots(
    precision: str, slot: int
) -> None:
    original = connectome()
    execution = prepare(original, (), (), precision)
    state = core.initial_state(execution.network, voltage_mv=-44)
    with mx.stream(mx.gpu):
        events = mx.zeros((1, 0), dtype=mx.bool_)
    state, trace = execution.advance(state, events)
    with mx.stream(mx.gpu):
        changed = (mx.arange(19)[:, None, None] == slot) & (
            mx.arange(state.queue.shape[2])[None, None, :] == 0
        )
        queue = mx.where(changed, ~state.queue, state.queue)
        flags = np.asarray(
            EventLedger(original, (), 1).check(
                state._replace(queue=queue), trace, events
            ),
            dtype=np.bool_,
        )
    assert not flags[0, CHECK_NAMES.index(f'queue-slot-{slot}')]


@pytest.mark.parametrize('phase', ['pre', 'before', 'end'])
def test_ledger_rejects_nonfinite_state_in_every_observed_phase(
    precision: str, phase: str
) -> None:
    original = connectome()
    execution = prepare(original, (), (), precision)
    state = core.initial_state(execution.network)
    with mx.stream(mx.gpu):
        events = mx.zeros((1, 0), dtype=mx.bool_)
    state, trace = execution.advance(state, events)
    with mx.stream(mx.gpu):
        invalid = mx.full((1, 6), float('nan'))
        if phase == 'pre':
            trace = trace._replace(pre_voltage_mv=invalid)
        elif phase == 'before':
            trace = trace._replace(before_reset_synaptic_mv=invalid)
        else:
            state = state._replace(voltage_mv=invalid)
        flags = np.asarray(
            EventLedger(original, (), 1).check(state, trace, events), dtype=np.bool_
        )
    assert not flags[0, CHECK_NAMES.index('finite_' + phase)]


def test_ledger_rejects_an_omitted_or_reordered_step(precision: str) -> None:
    original = connectome()
    execution = prepare(original, (), (), precision)
    state = core.initial_state(execution.network)
    with mx.stream(mx.gpu):
        events = mx.zeros((1, 0), dtype=mx.bool_)
    state, trace = execution.advance(state, events)
    with pytest.raises(ValueError, match='step or clock'):
        EventLedger(original, (), 1).check(state._replace(step=2), trace, events)
