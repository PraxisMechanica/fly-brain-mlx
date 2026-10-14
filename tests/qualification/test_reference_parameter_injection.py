import importlib
from functools import partial
from pathlib import Path
from types import MappingProxyType, ModuleType

import pytest
import torch

from fly_brain import bootstrap
from fly_brain.qualification import reference_parameters
from fly_brain.qualification.adapters import schedule_probe, torch_setup
from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.module import build_connectome_silencer
from tests.support.observation_fixtures import fixture
from tests.support.reference_baseline import ORIGINAL_COMMIT
from tests.support.reference_baseline import original as original

pytestmark = [pytest.mark.integration, pytest.mark.reference]


def test_setup_copies_values_after_silencing_and_keeps_original_error_precedence() -> (
    None
):
    case = fixture()
    values = reference_parameters.model_parameters()
    model = torch_setup.prepare(
        case.connectome,
        case.targets,
        (),
        1,
        reference_parameters=MappingProxyType(values),
        silence=build_connectome_silencer(),
    )
    values['wScale'] = 0
    assert model.scale == 0.275
    with pytest.raises(ValueError, match='Silenced source index'):
        torch_setup.prepare(
            case.connectome,
            (),
            (NeuronRow(99),),
            1,
            reference_parameters=MappingProxyType({}),
            silence=build_connectome_silencer(),
        )
    with pytest.raises(KeyError):
        torch_setup.prepare(
            case.connectome,
            (),
            (),
            1,
            reference_parameters=MappingProxyType({}),
            silence=build_connectome_silencer(),
        )


def test_both_actual_bootstrap_paths_supply_fresh_immutable_values() -> None:
    threads = torch.get_num_threads()
    try:
        commands = (bootstrap.schedule(), bootstrap.parity_case(), bootstrap.schedule())
    finally:
        torch.set_num_threads(threads)
    supplied: list[object] = []
    for command in commands:
        assert isinstance(command, partial)
        use_case = command.keywords['use_case']
        assert isinstance(use_case, partial)
        execute = use_case.keywords['execute']
        assert isinstance(execute, partial)
        values: object = execute.keywords['reference_parameters']
        supplied.append(values)
        assert type(values) is MappingProxyType
        assert values == reference_parameters.model_parameters()
        with pytest.raises(TypeError):
            exec("values['wScale'] = 0", {'values': values})
    assert supplied[0] is not supplied[1] and supplied[0] is not supplied[2]


def test_actual_schedule_diagnostic_uses_injected_values_at_original_model_position(
    tmp_path: Path,
    original: tuple[ModuleType, ModuleType],
) -> None:
    original_schedule = importlib.import_module(
        'preserved_torch_reference.schedule_probe'
    )
    assert original_schedule.__file__ == (
        ORIGINAL_COMMIT + ':src/fly_brain/qualification/adapters/schedule_probe.py'
    )
    expected = original_schedule.run(tmp_path / 'original-schedule')
    actual = schedule_probe.run(
        tmp_path / 'schedule',
        reference_parameters=MappingProxyType(reference_parameters.model_parameters()),
    )
    assert actual == expected
    assert (tmp_path / 'schedule/reference-schedule.json').read_bytes() == (
        tmp_path / 'original-schedule/reference-schedule.json'
    ).read_bytes()
