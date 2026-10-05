import hashlib
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
import torch

from fly_brain.qualification.adapters.batch_verify import compare
from fly_brain.qualification.adapters.brian_jobs import build
from fly_brain.qualification.adapters.mlx_batch_collect import collect as collect_mlx
from fly_brain.qualification.adapters.paired_collect import collect as collect_paired
from fly_brain.qualification.adapters.replay_evidence import verify
from fly_brain.qualification.adapters.torch_collect import collect as collect_cpu
from fly_brain.qualification.adapters.torch_setup import prepare as prepare_cpu
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.models import Stimulus
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


@pytest.fixture(scope='module', autouse=True)
def cpu_threads() -> Iterator[None]:
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    yield
    torch.set_num_threads(previous)


@pytest.mark.parametrize('empty', (False, True))
def test_actual_batch_native_evidence_matches_fresh_independent_trial_collection(
    precision: str,
    tmp_path: Path,
    request: pytest.FixtureRequest,
    empty: bool,
) -> None:
    case = fixture(empty)
    destination = cast(str | None, request.config.getoption('--artifact-output'))
    output = (
        Path(destination) / f'fixture-{empty}' if destination else tmp_path / 'fixture'
    )
    output.mkdir(parents=True, exist_ok=False)
    execution = prepare(case.connectome, case.targets, (3,), precision)
    stimulus = Stimulus(
        case.events,
        case.targets,
        (200.0,) * len(case.targets),
        (0, 1, 2, 3),
        0,
        0,
        hashlib.sha256(case.events.tobytes()).hexdigest(),
    )
    cpu = prepare_cpu(case.connectome, case.targets, (3,), 4)
    for mode in ('first', 'repeat'):
        collect_mlx(execution, case.connectome, stimulus, output / f'mlx-{mode}')
        collect_cpu(cpu, stimulus, output / f'cpu-{mode}')
    verify(
        output / 'mlx-first',
        output / 'mlx-repeat',
        ('phase-digests.jsonl',),
        ('native.npz',),
    )
    verify(
        output / 'cpu-first',
        output / 'cpu-repeat',
        ('native-digests.jsonl',),
        ('native.npz',),
    )
    singles: dict[int, Path] = {}
    for trial in range(4):
        events = case.events[trial : trial + 1]
        one = Stimulus(
            events,
            case.targets,
            stimulus.rates_hz,
            (trial,),
            0,
            0,
            hashlib.sha256(events.tobytes()).hexdigest(),
        )
        path = output / f'single-{trial}'
        job = build(
            case.connectome, case.targets, (3,), events[0], output / f'build-{trial}'
        )
        capture = collect_paired(job, execution, case.connectome, one, path / 'paired')
        assert (
            capture.audit.step == 101
            and capture.spike is None
            and capture.budget is None
        )
        collect_cpu(
            prepare_cpu(case.connectome, case.targets, (3,), 1), one, path / 'cpu'
        )
        singles[trial] = path
    for engine in ('mlx', 'cpu'):
        corresponding = {
            trial: path / ('paired' if engine == 'mlx' else 'cpu')
            for trial, path in singles.items()
        }
        for mode in ('first', 'repeat'):
            assert compare(
                output / f'{engine}-{mode}',
                corresponding,
                engine,
                101,
                6,
                len(case.connectome.sources),
                len(case.targets),
            ) == (None, {trial: () for trial in range(4)})
