from dataclasses import replace
from typing import cast

import mlx.core as mx
import numpy as np
import pytest

from fly_brain.qualification.ports import ObservationSession, ObservationSessionFactory
from fly_brain.qualification.session_expectations import (
    CHECK_NAMES,
    expect_step,
    initial_ledger,
    observation_checks,
)
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.backend.engines import Execution
from fly_brain.simulation.backend.observation_session import NativeObservationSession
from fly_brain.simulation.observation_module import build_observation_sessions
from fly_brain.simulation.observations import (
    ObservationInitialState,
    ObservationOperands,
)
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.metal]


def firing_initial(trials: int = 1) -> ObservationInitialState:
    return ObservationInitialState(
        np.full((trials, 6), -44, dtype=np.float64),
        np.zeros((trials, 6), dtype=np.float64),
        np.full((trials, 6), -100000000, dtype=np.int32),
    )


def fault_factory(execution: Execution) -> ObservationSessionFactory:
    def create(
        trial_indices: tuple[int, ...], initial: ObservationInitialState | None
    ) -> ObservationSession:
        if initial is None:
            state = core.initial_state(execution.network, len(trial_indices))
        else:
            state = core.initial_state(
                execution.network,
                len(trial_indices),
                initial.voltage_mv,
                initial.synaptic_mv,
                initial.last_spike_step,
            )
        return NativeObservationSession(
            execution.advance, execution.network, state, trial_indices
        )

    return create


def corrupt_operands(operands: ObservationOperands, field: str) -> ObservationOperands:
    return ObservationOperands(
        operands.sources,
        operands.destinations,
        ~operands.available if field == 'available' else operands.available,
        ~operands.spikes if field == 'spikes' else operands.spikes,
        ~operands.receiving if field == 'receiving' else operands.receiving,
        ~operands.due_sources if field == 'due_sources' else operands.due_sources,
        ~operands.accepted_destinations
        if field == 'accepted_destinations'
        else operands.accepted_destinations,
        ~operands.discarded_destinations
        if field == 'discarded_destinations'
        else operands.discarded_destinations,
        operands.accepted_inputs,
        operands.last_spike_step + np.int32(1)
        if field == 'last_spike_step'
        else operands.last_spike_step,
        ~operands.pending_sources
        if field == 'pending_sources'
        else operands.pending_sources,
    )


@pytest.mark.parametrize(
    'field,check',
    (
        ('available', 'available'),
        ('spikes', 'threshold'),
        ('receiving', 'receiving'),
        ('due', 'due'),
        ('accepted', 'accepted'),
        ('discarded', 'discarded'),
        ('accepted_inputs', 'accepted_inputs'),
        ('last_spike_step', 'last_spike_step'),
    ),
)
def test_neutral_comparator_detects_each_actual_discrete_fault(
    precision: str,
    field: str,
    check: str,
) -> None:
    case = fixture()
    execution = prepare(case.connectome, case.targets, (), precision)

    def changed(
        state: core.State, inputs: mx.array
    ) -> tuple[core.State, core.StepTrace]:
        state, trace = execution.advance(state, inputs)
        with mx.stream(mx.gpu):
            if field == 'last_spike_step':
                state = state._replace(
                    last_spike_step=state.last_spike_step
                    + (mx.arange(6)[None, :] == 0).astype(mx.int32)
                )
            else:
                value = cast(mx.array, getattr(trace, field))
                trace = trace._replace(
                    **{
                        field: mx.where(
                            mx.arange(value.shape[1])[None, :] == 0, ~value, value
                        )
                    }
                )
        return state, trace

    factory = fault_factory(Execution(execution.network, changed))
    session = factory((0,), firing_initial())
    inputs = np.ones((1, len(case.targets)), dtype=np.bool_)
    actual = session.advance(inputs)
    _, operands = expect_step(
        initial_ledger(case.connectome, case.targets, 1, firing_initial()),
        actual,
        inputs,
        case.connectome,
        case.targets,
    )
    flags = observation_checks(actual, session.compare(operands), operands)
    assert not flags[0, CHECK_NAMES.index(check)]


@pytest.mark.parametrize('slot', range(19))
def test_neutral_comparator_reads_every_actual_physical_slot(
    precision: str, slot: int
) -> None:
    case = fixture()
    execution = prepare(case.connectome, case.targets, (), precision)

    def changed(
        state: core.State, inputs: mx.array
    ) -> tuple[core.State, core.StepTrace]:
        state, trace = execution.advance(state, inputs)
        with mx.stream(mx.gpu):
            mask = (mx.arange(19)[:, None, None] == slot) & (
                mx.arange(state.queue.shape[2])[None, None, :] == 0
            )
            state = state._replace(queue=mx.where(mask, ~state.queue, state.queue))
        return state, trace

    session = fault_factory(Execution(execution.network, changed))(
        (0,), firing_initial()
    )
    inputs = np.zeros((1, len(case.targets)), dtype=np.bool_)
    actual = session.advance(inputs)
    _, operands = expect_step(
        initial_ledger(case.connectome, case.targets, 1, firing_initial()),
        actual,
        inputs,
        case.connectome,
        case.targets,
    )
    flags = observation_checks(actual, session.compare(operands), operands)
    assert not flags[0, CHECK_NAMES.index(f'queue-slot-{slot}')]
    with pytest.raises(ValueError, match='complete matching comparison'):
        session.advance(inputs)


@pytest.mark.parametrize(
    'field', ('available', 'spikes', 'receiving', 'last_spike_step', 'pending_sources')
)
def test_wrong_supplied_operands_block_further_native_advance(
    precision: str, field: str
) -> None:
    case = fixture()
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (), precision
    )
    session = factory((0,), firing_initial())
    inputs = np.zeros((1, len(case.targets)), dtype=np.bool_)
    actual = session.advance(inputs)
    _, operands = expect_step(
        initial_ledger(case.connectome, case.targets, 1, firing_initial()),
        actual,
        inputs,
        case.connectome,
        case.targets,
    )
    changed = corrupt_operands(operands, field)
    comparison = session.compare(changed)
    assert not (comparison.gates_equal.all() and comparison.queue_equal.all())
    with pytest.raises(ValueError, match='complete matching comparison'):
        session.advance(inputs)


@pytest.mark.parametrize(
    'factor', ('due_sources', 'accepted_destinations', 'discarded_destinations')
)
def test_supplied_source_and_destination_factors_are_used_without_policy_reconstruction(
    precision: str,
    factor: str,
) -> None:
    case = fixture()
    targets = tuple(range(6))
    factory, _ = build_observation_sessions(case.connectome, targets, (), precision)
    session = factory((0,), firing_initial())
    state = initial_ledger(case.connectome, targets, 1, firing_initial())
    inputs = np.zeros((1, 6), dtype=np.bool_)
    operands: ObservationOperands | None = None
    for step in range(19):
        actual = session.advance(inputs)
        state, operands = expect_step(state, actual, inputs, case.connectome, targets)
        if step < 18:
            assert observation_checks(actual, session.compare(operands), operands).all()
    assert operands is not None
    changed = corrupt_operands(operands, factor)
    comparison = session.compare(changed)
    assert not comparison.gates_equal.all()
    with pytest.raises(ValueError, match='complete matching comparison'):
        session.advance(inputs)


def test_missing_comparison_blocks_advance_and_complete_data_can_release_it(
    precision: str,
) -> None:
    case = fixture()
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (), precision
    )
    session = factory((0,), firing_initial())
    inputs = np.zeros((1, len(case.targets)), dtype=np.bool_)
    actual = session.advance(inputs)
    with pytest.raises(ValueError, match='complete matching comparison'):
        session.advance(inputs)
    _, operands = expect_step(
        initial_ledger(case.connectome, case.targets, 1, firing_initial()),
        actual,
        inputs,
        case.connectome,
        case.targets,
    )
    assert observation_checks(actual, session.compare(operands), operands).all()
    assert session.advance(inputs).completed_steps == 2


@pytest.mark.parametrize('phase', ('pre', 'before', 'end'))
def test_actual_nonfinite_phase_data_remains_visible_to_qualification(
    precision: str, phase: str
) -> None:
    case = fixture()
    execution = prepare(case.connectome, case.targets, (), precision)

    def changed(
        state: core.State, inputs: mx.array
    ) -> tuple[core.State, core.StepTrace]:
        state, trace = execution.advance(state, inputs)
        with mx.stream(mx.gpu):
            invalid = mx.full((1, 6), float('nan'))
            if phase == 'pre':
                trace = trace._replace(pre_synaptic_mv=invalid)
            elif phase == 'before':
                trace = trace._replace(before_reset_synaptic_mv=invalid)
            else:
                state = state._replace(synaptic_mv=invalid)
        return state, trace

    with pytest.raises(ValueError, match='independent qualification checks'):
        list(
            observe_session(
                fault_factory(Execution(execution.network, changed)),
                case.connectome,
                case.targets,
                (0,),
                case.events[:1, :1],
                firing_initial(),
            )
        )


@pytest.mark.parametrize(
    'field', ('sources', 'destinations', 'targets', 'refractory_steps')
)
def test_independently_pinned_configuration_rejects_changed_actual_maps(
    precision: str, field: str
) -> None:
    case = fixture()
    execution = prepare(case.connectome, case.targets, (), precision)
    with mx.stream(mx.gpu):
        actual = cast(
            mx.array,
            getattr(
                execution.network, 'input_targets' if field == 'targets' else field
            ),
        )
        changed = (
            mx.zeros_like(actual) if field == 'refractory_steps' else (actual + 1) % 6
        )
    network = replace(
        execution.network, **{'input_targets' if field == 'targets' else field: changed}
    )
    factory = fault_factory(Execution(network, execution.advance))
    with pytest.raises(ValueError, match='independent pinned inputs'):
        list(
            observe_session(
                factory,
                case.connectome,
                case.targets,
                (0,),
                case.events[:1, :1],
                firing_initial(),
            )
        )
