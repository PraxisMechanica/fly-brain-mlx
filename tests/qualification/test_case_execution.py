import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import build
from fly_brain.qualification.adapters.case_execution import execute
from fly_brain.qualification.adapters.torch_setup import prepare as prepare_cpu
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.models import Stimulus
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


@pytest.mark.parametrize('empty', (False, True))
def test_each_engine_replays_fresh_state_with_complete_retained_evidence(
    precision: str, tmp_path: Path, empty: bool
) -> None:
    case = fixture(empty)
    events = case.events[:1]
    stimulus = Stimulus(
        events,
        case.targets,
        (200.0,) * len(case.targets),
        (0,),
        0,
        0,
        hashlib.sha256(events.tobytes()).hexdigest(),
    )
    job = build(case.connectome, case.targets, (3,), events[0], tmp_path / 'build')
    mlx = prepare(case.connectome, case.targets, (3,), precision)
    cpu = prepare_cpu(case.connectome, case.targets, (3,), 1)
    progress: list[str] = []
    output = tmp_path / 'evidence'
    execute(job, mlx, cpu, case.connectome, stimulus, output, progress.append)
    assert progress == [
        'paired-first',
        'paired-repeat',
        'cpu-first',
        'cpu-repeat',
        'replay-verified',
    ]
    for mode in ('first', 'repeat'):
        paired = output / ('paired-' + mode)
        causal = json.loads((paired / 'causal.json').read_text())
        assert causal['steps'] == 101 and causal['first_spike_step'] is None
        with (
            np.load(paired / 'reference-native.npz') as reference,
            np.load(paired / 'mlx-native.npz') as actual,
        ):
            assert reference['clock_step'].tolist() == [101]
            assert reference['spike_i'].tolist() == actual['spike_neurons'].tolist()
        rows = (
            (output / ('cpu-' + mode) / 'native-digests.jsonl').read_text().splitlines()
        )
        assert len(rows) == 102 and json.loads(rows[-1])['step'] == 100
    with pytest.raises(FileExistsError):
        execute(job, mlx, cpu, case.connectome, stimulus, output, progress.append)
