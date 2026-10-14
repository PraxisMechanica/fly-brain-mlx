from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.simulation.identifiers import TrialId
from fly_brain.simulation.observations import (
    PHASE_DTYPES,
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    PhysicalQueueObservation,
)
from tests.unit.test_identifier_type_contracts import typed
from tools.architecture.compiler import object_value

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    'model,expression',
    (
        (
            'ObservationConfiguration',
            'ObservationConfiguration(base.neurons, base.queue_slots, base.initial_step, (value,), base.sources, base.destinations, base.targets, base.refractory_steps, base.initial_voltage_mv, base.initial_synaptic_mv, base.initial_last_spike_step)',
        ),
        (
            'NativeObservation',
            'NativeObservation(base.completed_steps, (value,), base.fields, base.due_edges, base.due_sha256)',
        ),
        (
            'NativeComparison',
            'NativeComparison(base.completed_steps, (value,), base.gates_equal, base.queue_equal)',
        ),
        (
            'PhysicalQueueObservation',
            'PhysicalQueueObservation(base.completed_steps, (value,), base.queue)',
        ),
        (
            'SessionBlock',
            'SessionBlock(base.begin, base.rows, (value,), base.fields, base.checks, base.queue_sha256, base.queue_slot_sha256, base.final_queue, base.due_edges, base.due_sha256)',
        ),
    ),
)
def test_actual_session_values_reject_neuron_rows_as_requested_trial_labels(
    tmp_path: Path, model: str, expression: str
) -> None:
    module = (
        'fly_brain.qualification.session_blocks'
        if model == 'SessionBlock'
        else 'fly_brain.simulation.observations'
    )
    source = (
        f'from {module} import {model}\n'
        'from fly_brain.simulation.identifiers import NeuronRow, TrialId\n'
        f'def consume(base: {model}) -> {model}:\n'
        '    value = NeuronRow(2)\n'
        + f'    return {expression}\n'
        + 'def preserve(row: NeuronRow, trial: TrialId) -> tuple[NeuronRow, TrialId]:\n    return row, trial\n'
    )
    found = typed(tmp_path, source)
    assert len(found) == 1
    diagnostic = object_value(found[0])
    assert diagnostic['rule'] == 'reportArgumentType'
    assert object_value(object_value(diagnostic['range'])['start'])['line'] == 4
    assert typed(tmp_path, source.replace('NeuronRow(2)', 'TrialId(2)')) == []


@pytest.mark.parametrize(
    'module',
    ('fly_brain.simulation.observation_ports', 'fly_brain.qualification.ports'),
)
def test_captured_session_factory_preserves_trial_boundary_through_reexport(
    tmp_path: Path, module: str
) -> None:
    (tmp_path / 'facade.py').write_text(
        f'from {module} import ObservationSessionFactory as Factory, ObservationSession as Session\n'
    )
    source = (
        'from facade import Factory, Session\n'
        'from fly_brain.simulation.identifiers import NeuronRow, TrialId\n'
        'def consume(factory: Factory, labels: tuple[NeuronRow, ...]) -> Session:\n'
        '    def invoke() -> Session:\n        return factory(labels, None)\n'
        '    return invoke()\n'
        'def preserve(row: NeuronRow, trial: TrialId) -> tuple[NeuronRow, TrialId]:\n    return row, trial\n'
    )
    found = typed(tmp_path, source)
    assert len(found) == 1
    assert object_value(found[0])['rule'] == 'reportArgumentType'
    assert (
        typed(
            tmp_path,
            source.replace(
                'labels: tuple[NeuronRow, ...]', 'labels: tuple[TrialId, ...]'
            ),
        )
        == []
    )


@pytest.mark.parametrize(
    'trials',
    ((TrialId(2), TrialId(4)), (TrialId(4), TrialId(2)), (TrialId(4), TrialId(4))),
)
def test_neutral_session_values_keep_requested_label_tuple_without_using_positions(
    trials: tuple[TrialId, ...],
) -> None:
    fields = {
        name: np.zeros((2, 0) if name == 'accepted_inputs' else (2, 2), dtype=dtype)
        for name, dtype in PHASE_DTYPES.items()
    }
    edges = (np.array([], dtype=np.int32), np.array([], dtype=np.int32))
    queue = PhysicalQueueObservation(1, trials, np.zeros((19, 2, 0), dtype=np.bool_))
    native = NativeObservation(1, trials, fields, edges, ('first', 'second'))
    configuration = ObservationConfiguration(
        2,
        19,
        0,
        trials,
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.full(2, 22, dtype=np.int32),
        np.full((2, 2), -52, dtype=np.float32),
        np.zeros((2, 2), dtype=np.float32),
        np.full((2, 2), -100000000, dtype=np.int32),
    )
    comparison = NativeComparison(
        1, trials, np.ones((2, 8), dtype=np.bool_), np.ones((2, 19), dtype=np.bool_)
    )
    block = SessionBlock(
        0,
        1,
        trials,
        {name: value[None] for name, value in fields.items()},
        np.ones((1, 2, 30), dtype=np.bool_),
        queue.sha256,
        queue.slot_sha256,
        queue.queue,
        (native.due_edges,),
        (native.due_sha256,),
    )
    for actual in (configuration, native, comparison, queue, block):
        assert actual.trial_indices is trials
    assert block.fields['pre_v'].shape == (1, 2, 2)
    assert block.due_sha256 == (('first', 'second'),)
    assert len(queue.sha256) == 2 and len(queue.slot_sha256[0]) == 19
    assert not block.fields['pre_v'].flags.writeable and not queue.queue.flags.writeable
