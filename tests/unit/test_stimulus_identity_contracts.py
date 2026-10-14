import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from fly_brain.simulation.identifiers import FlyWireNeuronId, NeuronRow, TrialId
from fly_brain.simulation.models import Experiment, Stimulus
from fly_brain.simulation.stimuli import neuron_indices
from tests.quality.support import PROJECT
from tests.unit.test_identifier_type_contracts import typed
from tests.unit.test_stimuli import connectome
from tools.code_quality.json_values import object_value

pytestmark = pytest.mark.unit


@pytest.mark.checker
@pytest.mark.parametrize(
    'extra_import,parameter,expression,wrong,owned',
    (
        (
            '',
            '',
            "models.Experiment('p9', 1, 1, (value,), (100.0,))",
            'NeuronRow',
            'FlyWireNeuronId',
        ),
        (
            '',
            '',
            "models.Experiment('p9', 1, 1, (), (), (value,))",
            'TrialId',
            'FlyWireNeuronId',
        ),
        (
            '',
            '',
            "models.Stimulus(events, (value,), (), (), 0, 0, '')",
            'FlyWireNeuronId',
            'NeuronRow',
        ),
        (
            '',
            '',
            "models.Stimulus(events, (), (), (value,), 0, 0, '')",
            'NeuronRow',
            'TrialId',
        ),
        (
            'from fly_brain.simulation.stimuli import neuron_indices\n',
            '',
            'neuron_indices(network, (value,))',
            'NeuronRow',
            'FlyWireNeuronId',
        ),
        (
            'from fly_brain.simulation.ports import StimulusGenerator\n',
            ', operation: StimulusGenerator',
            "operation(network, models.Experiment('silent', 0, 0, (), ()), 1, (value,), 0)",
            'NeuronRow',
            'TrialId',
        ),
        (
            'from fly_brain.qualification.stimulus_ports import StimulusGenerator\n',
            ', operation: StimulusGenerator',
            "operation(network, models.Experiment('silent', 0, 0, (), ()), 1, (value,), 0)",
            'FlyWireNeuronId',
            'TrialId',
        ),
        (
            'from fly_brain.simulation.ports import UniformDraws\n',
            ', operation: UniformDraws',
            'operation((0, 0, value), (1, 0))',
            'NeuronRow',
            'TrialId',
        ),
        (
            'from fly_brain.simulation.ports import SimulationExecutor\n',
            ', operation: SimulationExecutor',
            "operation(network, models.Stimulus(events, (), (), (), 0, 0, ''), (value,))",
            'TrialId',
            'NeuronRow',
        ),
    ),
)
def test_actual_stimulus_contract_rejects_equal_values_in_wrong_identity_space(
    tmp_path: Path,
    extra_import: str,
    parameter: str,
    expression: str,
    wrong: str,
    owned: str,
) -> None:
    source = (
        'import numpy as np\nfrom numpy.typing import NDArray\n'
        'from fly_brain.simulation import models\n'
        f'from fly_brain.simulation.identifiers import {wrong}, {owned}\n'
        + extra_import
        + f'def consume(network: models.Connectome, events: NDArray[np.uint8]{parameter}) -> None:\n'
        + f'    value = {wrong}(2)\n    {expression}\n'
        + f'def preserve(left: {wrong}, right: {owned}) -> tuple[{wrong}, {owned}]:\n    return left, right\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    start = object_value(object_value(diagnostic['range'])['start'])
    assert (len(found), diagnostic['rule'], diagnostic['file'], start['line']) == (
        1,
        'reportArgumentType',
        str(tmp_path / 'consumer.py'),
        source.splitlines().index('    ' + expression),
    )
    assert typed(tmp_path, source.replace(f'{wrong}(2)', f'{owned}(2)')) == []


@pytest.mark.checker
def test_aliased_reexported_lookup_keeps_flywire_input_and_neuron_row_output(
    tmp_path: Path,
) -> None:
    (tmp_path / 'facade.py').write_text(
        'from fly_brain.simulation.stimuli import neuron_indices as locate\n'
    )
    source = (
        'from facade import locate as map_rows\n'
        'from fly_brain.simulation.identifiers import NeuronRow, FlyWireNeuronId\n'
        'from fly_brain.simulation.models import Connectome\n'
        'def consume(network: Connectome, value: NeuronRow) -> tuple[NeuronRow, ...]:\n'
        '    return map_rows(network, (value,))\n'
        'def preserve(value: FlyWireNeuronId) -> FlyWireNeuronId:\n    return value\n'
    )
    found = typed(tmp_path, source)
    assert (len(found), object_value(found[0])['rule']) == (1, 'reportArgumentType')
    assert (
        typed(tmp_path, source.replace('value: NeuronRow)', 'value: FlyWireNeuronId)'))
        == []
    )


@pytest.mark.checker
def test_erasing_actual_stimulus_target_contract_loses_wrong_space_rejection(
    tmp_path: Path,
) -> None:
    original = (
        (PROJECT / 'src/fly_brain/simulation/models.py')
        .read_text()
        .replace(
            'from .identifiers import', 'from fly_brain.simulation.identifiers import'
        )
    )
    local = tmp_path / 'local_models.py'
    local.write_text(original)
    source = (
        'import numpy as np\nfrom numpy.typing import NDArray\n'
        'from local_models import Stimulus\n'
        'from fly_brain.simulation.identifiers import FlyWireNeuronId\n'
        'def consume(events: NDArray[np.uint8]) -> Stimulus:\n'
        "    return Stimulus(events, (FlyWireNeuronId(2),), (), (), 0, 0, '')\n"
    )
    assert len(typed(tmp_path, source)) == 1
    local.write_text(
        original.replace('targets: tuple[NeuronRow, ...]', 'targets: tuple[int, ...]')
    )
    assert typed(tmp_path, source) == []


def test_experiment_and_stimulus_keep_supplied_objects_and_serialized_identities() -> (
    None
):
    ids = (FlyWireNeuronId(720575940627652358), FlyWireNeuronId(720575940635872101))
    silenced = (ids[0],)
    experiment = Experiment('p9', 1, 1, ids, (100.0, 100.0), silenced)
    targets = neuron_indices(connectome(), ids)
    trials = (TrialId(2), TrialId(4))
    events = np.zeros((2, 3, 2), dtype=np.uint8)
    events.setflags(write=False)
    before = events.tobytes()
    stimulus = Stimulus(events, targets, experiment.rates_hz, trials, 0, 1, 'digest')
    assert experiment.activated_ids is ids and experiment.silenced_ids is silenced
    assert stimulus.targets is targets and stimulus.trial_indices is trials
    assert stimulus.events is events and stimulus.rates_hz is experiment.rates_hz
    assert (
        targets,
        events.dtype,
        events.shape,
        events.tobytes(),
        events.flags.writeable,
    ) == (
        (NeuronRow(0), NeuronRow(1)),
        np.dtype(np.uint8),
        (2, 3, 2),
        before,
        False,
    )
    assert json.dumps(asdict(experiment)) == (
        '{"name": "p9", "code": 1, "generator_code": 1, '
        '"activated_ids": [720575940627652358, 720575940635872101], '
        '"rates_hz": [100.0, 100.0], "silenced_ids": [720575940627652358], '
        '"first_class_channels": null}'
    )
    assert experiment.activation_classes == (1, 1)
