import json
from functools import partial
from pathlib import Path
from types import MappingProxyType

import pytest
import torch

from fly_brain import bootstrap
from fly_brain.qualification import reference_parameters
from fly_brain.qualification.adapters import schedule_probe, torch_setup
from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.module import build_connectome_silencer
from tests.support.observation_fixtures import fixture

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


def test_schedule_diagnostic_records_pinned_stimulation_and_delay(
    tmp_path: Path,
) -> None:
    actual = schedule_probe.run(
        tmp_path / 'schedule',
        reference_parameters=MappingProxyType(reference_parameters.model_parameters()),
    )
    assert actual['brian2_version'] == '2.8.0'
    assert actual['timestep_ms'] == 0.1
    assert actual['voltage_dtype'] == "<class 'numpy.float64'>"
    assert actual['synaptic_delay_ms'] == 1.8
    assert actual['guaranteed_stimulation'] == {
        'rate_hz': 10000,
        'end_voltage_mv': [16.75, -52.0, 16.75, -52.0, 16.75],
        'spike_times_ms': [step * 0.1 for step in (1, 3)],
    }
    delay = actual['pytorch_single_spike_delay']
    assert isinstance(delay, dict)
    assert (delay['first_destination_g_step'], delay['first_destination_v_step']) == (
        20,
        21,
    )
    assert (
        json.loads((tmp_path / 'schedule/reference-schedule.json').read_text())
        == actual
    )
