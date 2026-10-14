from pathlib import Path

import pytest

from tests.unit.test_identifier_type_contracts import typed
from tools.code_quality.json_values import object_value

pytestmark = [pytest.mark.unit, pytest.mark.checker]


@pytest.mark.parametrize(
    'model,field,owned,other',
    (
        ('Connectome', 'neuron_ids', 'FlyWireIds64', 'NeuronRows64'),
        ('Connectome', 'neuron_ids', 'FlyWireIds64', 'TrialIds64'),
        ('Connectome', 'sources', 'NeuronRows32', 'EdgeRows32'),
        ('Connectome', 'sources', 'NeuronRows32', 'PaddedEdgeRows32'),
        ('Connectome', 'destinations', 'NeuronRows32', 'EdgeRows32'),
        ('DestinationGrouping', 'edge_ids', 'EdgeRows32', 'NeuronRows32'),
        ('DestinationGrouping', 'edge_ids', 'EdgeRows32', 'PaddedEdgeRows32'),
        ('DestinationBucket', 'targets', 'NeuronRows32', 'EdgeRows32'),
        ('DestinationBucket', 'edge_ids', 'PaddedEdgeRows32', 'EdgeRows32'),
        ('DestinationBucket', 'edge_ids', 'PaddedEdgeRows32', 'NeuronRows32'),
    ),
)
def test_real_model_constructors_reject_wrong_array_spaces_and_accept_repair(
    tmp_path: Path, model: str, field: str, owned: str, other: str
) -> None:
    arguments = {
        'Connectome': (
            ('neuron_ids', 'FlyWireIds64'),
            ('sources', 'NeuronRows32'),
            ('destinations', 'NeuronRows32'),
            ('counts', 'NDArray[np.int32]'),
            ('weights_mv', 'NDArray[np.float64]'),
        ),
        'DestinationGrouping': (
            ('edge_ids', 'EdgeRows32'),
            ('inverse', 'NDArray[np.int32]'),
            ('offsets', 'NDArray[np.int64]'),
        ),
        'DestinationBucket': (
            ('targets', 'NeuronRows32'),
            ('edge_ids', 'PaddedEdgeRows32'),
            ('counts', 'NDArray[np.float32]'),
            ('occupied', 'NDArray[np.bool_]'),
        ),
    }[model]
    brands = sorted(
        {
            annotation
            for _, annotation in arguments
            if not annotation.startswith('NDArray')
        }
        | {other}
    )
    parameters = ', '.join(f'{name}: {annotation}' for name, annotation in arguments)
    operands = ', '.join('value' if name == field else name for name, _ in arguments)
    source = (
        'import numpy as np\nfrom numpy.typing import NDArray\n'
        + 'from fly_brain.simulation.identifiers import '
        + ', '.join(brands)
        + '\n'
        + f'from fly_brain.simulation.models import {model}\n'
        + f'def execute(value: {other}, {parameters}) -> {model}:\n'
        + f'    return {model}({operands})\n'
        + f'def preserve(value: {other}) -> {other}:\n    return value\n'
    )
    found = typed(tmp_path, source)
    assert len(found) == 1
    diagnostic = object_value(found[0])
    assert diagnostic['rule'] == 'reportArgumentType'
    assert diagnostic['file'] == str(tmp_path / 'consumer.py')
    assert (
        typed(
            tmp_path,
            source.replace(f'execute(value: {other}', f'execute(value: {owned}'),
        )
        == []
    )
