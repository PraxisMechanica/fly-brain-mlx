import hashlib
import json
from collections.abc import Generator
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters import mlx_batch_collect
from fly_brain.qualification.adapters.paired_observer import phase_hash
from fly_brain.qualification.adapters.replay_evidence import verify
from fly_brain.qualification.ports import ObservationSessionFactory
from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.models import Connectome, Stimulus
from fly_brain.simulation.observation_module import build_observation_sessions
from fly_brain.simulation.observations import HostFieldSnapshots
from tests.qualification.test_mlx_observer import fixture
from tests.support.legacy_mlx_ledger import EventLedger
from tests.support.legacy_mlx_observer import MLXBlock, observe
from tests.support.session_block_values import replace_block, trial_fields

pytestmark = [pytest.mark.integration, pytest.mark.metal]


def trial_block(block: MLXBlock, trial: int) -> HostFieldSnapshots:
    return trial_fields(block.fields, trial)


@pytest.mark.parametrize('empty', (False, True))
def test_batch_collection_preserves_every_trial_native_phase_queue_and_spike(
    precision: str, tmp_path: Path, empty: bool
) -> None:
    case = fixture(empty)
    stimulus = Stimulus(
        case.events,
        case.targets,
        (),
        (0, 1, 2, 3),
        0,
        0,
        hashlib.sha256(case.events.tobytes()).hexdigest(),
    )
    execution = prepare(case.connectome, case.targets, (3,), precision)
    expected = list(
        observe(
            execution,
            core.initial_state(execution.network, 4),
            case.events,
            EventLedger(case.connectome, case.targets, 4),
        )
    )
    outputs = (tmp_path / 'first', tmp_path / 'repeat')
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (3,), precision
    )
    for output in outputs:
        mlx_batch_collect.collect(factory, case.connectome, stimulus, output)
        rows = [
            json.loads(line)
            for line in (output / 'phase-digests.jsonl').read_text().splitlines()
        ]
        assert [(row['begin'], row['rows']) for row in rows] == [
            (0, 32),
            (32, 32),
            (64, 32),
            (96, 5),
        ]
        for saved, actual in zip(rows, expected, strict=True):
            assert saved['native_phase_sha256'] == [
                phase_hash(trial_block(actual, trial).fields) for trial in range(4)
            ]
            assert saved['mlx_queue_sha256'] == list(actual.queue_sha256)
            assert saved['mlx_due_sha256'] == [list(row) for row in actual.due_sha256]
        with np.load(output / 'native.npz') as native:
            assert set(native.files) == set(expected[-1].fields) | {
                'queue',
                'spike_trials',
                'spike_neurons',
                'spike_steps',
            }
            for name, value in expected[-1].fields.items():
                assert (
                    native[name].dtype,
                    native[name].shape,
                    native[name].tobytes(),
                ) == (value.dtype, value[-1].shape, value[-1].tobytes())
            assert expected[-1].final_queue is not None
            assert native['queue'].tobytes() == expected[-1].final_queue.tobytes()
            raster = [
                (trial, neuron, block.begin + row)
                for block in expected
                for row, trial, neuron in zip(
                    *np.nonzero(block.fields['spikes']), strict=True
                )
            ]
            assert (
                list(
                    zip(
                        native['spike_trials'],
                        native['spike_neurons'],
                        native['spike_steps'],
                        strict=True,
                    )
                )
                == raster
            )
    verify(*outputs, ('phase-digests.jsonl',), ('native.npz',))
    with pytest.raises(FileExistsError):
        mlx_batch_collect.collect(factory, case.connectome, stimulus, outputs[0])


def test_failed_actual_ledger_check_cannot_be_recorded_as_success(
    precision: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = fixture()
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (), precision
    )
    stimulus = Stimulus(case.events, case.targets, (), (0, 1, 2, 3), 0, 0, 'fixture')

    def fault(
        factory: ObservationSessionFactory,
        connectome: Connectome,
        targets: tuple[int, ...],
        trials: tuple[int, ...],
        events: NDArray[np.uint8],
    ) -> Generator[SessionBlock, None, None]:
        for block in observe_session(factory, connectome, targets, trials, events):
            checks = block.checks.copy()
            checks[-1, 3, -1] = False
            yield replace_block(block, checks=checks)

    monkeypatch.setattr(mlx_batch_collect, 'observe_session', fault)
    with pytest.raises(ValueError, match='incomplete or invalid'):
        mlx_batch_collect.collect(
            factory, case.connectome, stimulus, tmp_path / 'invalid'
        )
    assert not (tmp_path / 'invalid/native.npz').exists()
