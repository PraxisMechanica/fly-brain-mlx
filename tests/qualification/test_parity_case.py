import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from fly_brain.comparison.acceptance import (
    evaluate_case,
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.infrastructure.seeded_random import uniforms
from fly_brain.qualification.adapters.parity_case import run
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.module import build_case_stimulus
from fly_brain.qualification.reference_parameters import model_parameters
from fly_brain.simulation.experiments import P9_IDS
from fly_brain.simulation.identifiers import TrialId
from fly_brain.simulation.models import InputPin
from fly_brain.simulation.module import (
    build_connectome_silencer,
    build_experiment_reader,
    build_stimulus,
    build_stimulus_recorder,
)
from fly_brain.simulation.observation_module import build_observation_assembly
from fly_brain.simulation.storage import persist_stimulus
from tests.support.observation_fixtures import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


def test_driver_runs_prescribed_p9_protocol_without_accepting_a_small_connectome(
    precision: str, tmp_path: Path
) -> None:
    connectome = replace(
        fixture().connectome, neuron_ids=np.array((*P9_IDS, 2, 3, 4, 5), dtype=np.int64)
    )
    pin = InputPin('fixture', 'fixture', 6, 8)
    read_experiment = build_experiment_reader()
    prepare_stimulus = build_case_stimulus(
        read_experiment,
        build_stimulus(uniforms),
        build_stimulus_recorder(persist_stimulus),
    )
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        report = run(
            connectome,
            pin,
            ParityCase('p9', 1000, TrialId(0)),
            tmp_path / 'case',
            precision,
            prepare_stimulus=prepare_stimulus,
            read_experiment=read_experiment,
            assemble_observations=build_observation_assembly(),
            score=evaluate_case,
            validate=validate_coordinates,
            convert_clock=steps_from_reference_clock,
            reference_parameters=model_parameters(),
            silence=build_connectome_silencer(),
        )
        with pytest.raises(FileExistsError):
            run(
                connectome,
                pin,
                ParityCase('p9', 1000, TrialId(0)),
                tmp_path / 'case',
                precision,
                prepare_stimulus=prepare_stimulus,
                read_experiment=read_experiment,
                assemble_observations=build_observation_assembly(),
                score=evaluate_case,
                validate=validate_coordinates,
                convert_clock=steps_from_reference_clock,
                reference_parameters=model_parameters(),
                silence=build_connectome_silencer(),
            )
    finally:
        torch.set_num_threads(threads)
    saved = json.loads((tmp_path / 'case/case.json').read_text())
    assert saved['case_checks']['required_frozen_case'] is True
    assert saved['case_checks']['prescribed_seed_generator_targets_and_rates'] is True
    assert saved['case_checks']['full_connectome_geometry'] is False
    assert report['case_accepted'] is False and report['full_matrix_accepted'] is False
    assert saved['causal']['steps'] == 1000
    environment = json.loads((tmp_path / 'case/environment.json').read_text())
    assert environment['cpu_threads'] == 1 and environment['compilation'] == 'disabled'
    assert environment['versions']['brian2'] == '2.8.0'
    assert (
        bool(environment['source_sha256']['fly_brain.simulation.backend.core']),
        environment['source_sha256']['fly_brain.qualification.reference_parameters'],
    ) == (
        True,
        hashlib.sha256(
            Path(model_parameters.__code__.co_filename).read_bytes()
        ).hexdigest(),
    )
