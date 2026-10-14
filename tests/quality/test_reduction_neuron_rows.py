from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.causal_capture import CausalCapture
from fly_brain.qualification.adapters.causal_reduction import reduction_inputs
from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.observations import (
    COMPENSATED_ORDER,
    ReductionEvidence,
    ReductionRow,
)
from tests.quality.support import PROJECT
from tests.quality.test_reference_silencing_boundary import typed
from tests.unit.test_audit_transition import block

pytestmark = pytest.mark.unit
NATIVE = """import numpy as np
from fly_brain.simulation.identifiers import NeuronRow{foreign}
from fly_brain.simulation.observations import ReductionRow, ReductionReader as Provider
from fly_brain.simulation.backend.bucketed import Layout
from fly_brain.simulation.backend.reduction_evidence import read_rows
from fly_brain.qualification.ports import ReductionReader as Consumer
from fly_brain.qualification.causality import BudgetViolation, CausalAudit
from fly_brain.qualification.adapters.causal_capture import CausalCapture, CauseContext, ObservedStep
from fly_brain.qualification.adapters.paired_observer import PairedBlock
from fly_brain.qualification.adapters.causal_reduction import reduction_inputs
def use(layout: Layout, provider: Provider, consumer: Consumer, capture: CausalCapture, paired: PairedBlock, observed: ObservedStep, existing: tuple[NeuronRow, ...]) -> None:
    _ = ReductionRow({row}, np.zeros(0, dtype=np.int32), np.zeros(0, dtype=np.float32), np.zeros(0, dtype=np.bool_))
    _ = read_rows(layout, ({device},))
    _ = provider(({public},))
    _ = consumer(({consumed},))
    reduction_inputs(consumer, ({inputs},), np.zeros(0, dtype=np.float64))
    _ = capture.context(paired, 0, ({captured},))
    _ = CauseContext(({context},), observed, None)
    _ = BudgetViolation(0, 'pre', 'v', {budget}, 0.0, 0.0, 0.001)
    _ = CausalAudit(first_spike_neurons=({spike},))
    _ = consumer(existing)
def local_position(value: int) -> int:
    return value
"""
POINTS = (
    'row',
    'device',
    'public',
    'consumed',
    'inputs',
    'captured',
    'context',
    'budget',
    'spike',
)
SEAMS = (
    (
        'simulation.observations',
        '        neuron: NeuronRow,',
        POINTS[:1],
    ),
    (
        'simulation.observations',
        'tuple[NeuronRow, ...]',
        POINTS[2:3],
    ),
    (
        'simulation.backend.reduction_evidence',
        'tuple[NeuronRow, ...]',
        POINTS[1:2],
    ),
    ('qualification.ports', 'tuple[NeuronRow, ...]', POINTS[3:4]),
    (
        'qualification.adapters.causal_reduction',
        'tuple[NeuronRow, ...]',
        POINTS[4:5],
    ),
    (
        'qualification.adapters.causal_capture',
        'tuple[NeuronRow, ...]',
        POINTS[5:7],
    ),
    ('qualification.causality', 'neuron: NeuronRow', POINTS[7:8]),
    (
        'qualification.causality',
        'first_spike_neurons: tuple[NeuronRow, ...]',
        POINTS[8:],
    ),
)


@pytest.mark.parametrize(
    'identifier,foreign',
    (
        ('257', ''),
        ('TrialId(257)', ', TrialId'),
        ('FlyWireNeuronId(257)', ', FlyWireNeuronId'),
    ),
)
def test_native_constructor_provider_and_consumer_reject_wrong_identity_spaces(
    tmp_path: Path, identifier: str, foreign: str
) -> None:
    code = NATIVE.format(**dict.fromkeys(POINTS, identifier), foreign=foreign)
    result, output = typed(tmp_path, code)
    locations = (
        'ReductionRow(',
        'read_rows(layout, (',
        'provider((',
        'consumer((',
        'reduction_inputs(consumer,',
        'capture.context(',
        'CauseContext((',
        'BudgetViolation(',
        'CausalAudit(',
    )
    located = tuple(
        f'consumer.py:{code[: code.index(target)].count(chr(10)) + 1}:' in output
        for target in locations
    )
    assert (result, 'reportArgumentType' in output, located) == (
        1,
        True,
        (True,) * 9,
    ), output


def test_shared_owner_type_repair_closes_actual_provider_and_preserves_local_ints(
    tmp_path: Path,
) -> None:
    code = NATIVE.format(**dict.fromkeys(POINTS, 'NeuronRow(257)'), foreign='')
    code += 'from fly_brain.simulation.observations import ReductionEvidence\ndef binding(layout: Layout) -> Consumer:\n    def supplied(neurons: tuple[NeuronRow, ...]) -> ReductionEvidence:\n        return read_rows(layout, neurons)\n    provider: Provider = supplied\n    consumer: Consumer = provider\n    return consumer\n'
    code += 'def identities(row: ReductionRow, audit: CausalAudit, context: CauseContext, violation: BudgetViolation) -> tuple[NeuronRow, ...]:\n    return (row.neuron, violation.neuron, *audit.first_spike_neurons, *context.neurons)\n'
    repair = typed(tmp_path, code)
    result, output = typed(tmp_path, code + 'def broken(\n')
    assert (repair[0], result, 'consumer.py:' in output, 'error:' in output) == (
        0,
        1,
        True,
        True,
    ), (repair[1], output)


@pytest.mark.parametrize('module,annotation,points', SEAMS)
def test_each_actual_annotation_independently_rejects_then_weakens(
    tmp_path: Path, module: str, annotation: str, points: tuple[str, ...]
) -> None:
    source = (
        PROJECT / 'src/fly_brain' / Path(*module.split('.')).with_suffix('.py')
    ).read_text()
    package = 'fly_brain.' + module.rpartition('.')[0]
    source = source.replace('from .', 'from ' + package + '.')
    identifiers: dict[str, str] = dict.fromkeys(POINTS, 'NeuronRow(257)')
    identifiers.update(dict.fromkeys(points, '257'))
    code = NATIVE.format(**identifiers, foreign='')
    code = code.replace('from fly_brain.' + module + ' import', 'from api import')
    api = tmp_path / 'api.py'
    api.write_text(source)
    result, output = typed(tmp_path, code)
    assert (
        result,
        'consumer.py:' in output,
        'reportArgumentType' in output,
        annotation in source,
    ) == (
        1,
        True,
        True,
        True,
    )
    api.write_text(source.replace(annotation, annotation.replace('NeuronRow', 'int')))
    result, output = typed(tmp_path, code)
    assert result == 0, output


def test_selector_scalar_tuple_forwarding_and_reader_failure_are_preserved() -> None:
    scalar = int('257')
    neuron = NeuronRow(scalar)
    row = ReductionRow(
        neuron,
        np.zeros(0, dtype=np.int32),
        np.zeros(0, dtype=np.float32),
        np.zeros(0, dtype=np.bool_),
    )
    selectors = (neuron, neuron)
    received: list[tuple[NeuronRow, ...]] = []

    def reader(neurons: tuple[NeuronRow, ...]) -> ReductionEvidence:
        received.append(neurons)
        return ReductionEvidence((row,) * len(neurons), COMPENSATED_ORDER)

    identities = neuron is scalar, row.neuron is scalar
    arrays = reduction_inputs(reader, selectors, np.zeros(0, dtype=np.float64))
    assert (*identities, bool(arrays), received, received[0] is selectors) == (
        True,
        True,
        True,
        [selectors],
        True,
    )
    assert reduction_inputs(reader, (), np.zeros(0, dtype=np.float64)) == {}
    failure = ValueError('actual reader failed')

    def failing(neurons: tuple[NeuronRow, ...]) -> ReductionEvidence:
        received.append(neurons)
        raise failure

    with pytest.raises(ValueError) as caught:
        reduction_inputs(failing, selectors, np.zeros(0, dtype=np.float64))
    assert (caught.value is failure, received[-1] is selectors) == (True, True)


def test_causal_origin_and_capture_keep_existing_values_and_direct_tuple_identity() -> (
    None
):
    capture = CausalCapture()
    actual = block(0, 2, fork=1, violation=1)
    capture.check(actual)
    spike, budget = capture.spike, capture.budget
    assert spike is not None and budget is not None
    violation = capture.audit.first_budget_violation
    assert violation is not None
    assert (
        spike.neurons,
        budget.neurons,
        spike.neurons is capture.audit.first_spike_neurons,
        budget.neurons[0] is violation.neuron,
        type(violation.neuron),
        spike.current.snapshot.step,
        budget.current.snapshot.step,
    ) == ((1, 3), (2,), True, True, int, 1, 1)
