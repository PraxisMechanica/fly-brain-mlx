import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch

from fly_brain.qualification.adapters.parity_case import run
from fly_brain.qualification.models import ParityCase
from fly_brain.simulation.experiments import P9_IDS
from fly_brain.simulation.models import InputPin
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


def test_driver_runs_prescribed_p9_protocol_without_accepting_a_small_connectome(
    precision: str, tmp_path: Path
) -> None:
    connectome = replace(
        fixture().connectome, neuron_ids=np.array((*P9_IDS, 2, 3, 4, 5), dtype=np.int64)
    )
    pin = InputPin('fixture', 'fixture', 6, 8)
    threads = torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        report = run(
            connectome, pin, ParityCase('p9', 1000, 0), tmp_path / 'case', precision
        )
        with pytest.raises(FileExistsError):
            run(
                connectome, pin, ParityCase('p9', 1000, 0), tmp_path / 'case', precision
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
    assert environment['source_sha256']['fly_brain.simulation.backend.core']
