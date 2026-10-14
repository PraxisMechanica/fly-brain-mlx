from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.module import build_case_stimulus
from fly_brain.simulation.identifiers import (
    FlyWireIds64,
    FlyWireNeuronId,
    NeuronRow,
    NeuronRows32,
    TrialId,
)
from fly_brain.simulation.models import Connectome, Experiment, InputPin, Stimulus
from fly_brain.simulation.module import build_stimulus_recorder

pytestmark = pytest.mark.unit


def network() -> Connectome:
    return Connectome(
        FlyWireIds64(np.array([10, 20], dtype=np.int64)),
        NeuronRows32(np.array([], dtype=np.int32)),
        NeuronRows32(np.array([], dtype=np.int32)),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )


def stimulus(case: ParityCase) -> Stimulus:
    return Stimulus(
        np.zeros((1, case.steps, 1), dtype=np.uint8),
        (NeuronRow(0),),
        (100.0,),
        (case.trial,),
        20261004,
        1,
        'fixture',
    )


def test_owned_preparation_is_lazy_and_preserves_exact_case_arguments() -> None:
    connectome = network()
    case = ParityCase('p9', 7, TrialId(4))
    pin, output = InputPin('csv', 'parquet', 2, 0), Path('/fresh')
    experiment = Experiment('p9', 1, 1, (FlyWireNeuronId(10),), (100.0,))
    generated = stimulus(case)
    stored = replace(generated, events=generated.events.copy())
    calls: list[object] = []

    def read(name: str) -> Experiment:
        calls.append(('read', name))
        return experiment

    def generate(
        value: Connectome,
        definition: Experiment,
        steps: int,
        trials: tuple[TrialId, ...],
        seed: int,
    ) -> Stimulus:
        assert value is connectome and definition is experiment
        calls.append(('generate', steps, trials, seed))
        return generated

    def record(
        destination: Path,
        value: Connectome,
        definition: Experiment,
        inputs: InputPin,
        events: Stimulus,
    ) -> tuple[Stimulus, tuple[NeuronRow, ...]]:
        assert value is connectome and definition is experiment and inputs is pin
        assert events is generated
        calls.append(('record', destination))
        return stored, (NeuronRow(1),)

    prepare = build_case_stimulus(read, generate, record)
    assert calls == []
    actual, silenced = prepare(connectome, pin, case, output)
    assert actual is stored and actual.events is not generated.events
    assert silenced == (NeuronRow(1),)
    assert calls == [
        ('read', 'p9'),
        ('generate', 7, (case.trial,), 20261004),
        ('record', output),
    ]


def test_missing_silenced_identity_fails_only_after_persistence() -> None:
    case = ParityCase('p9', 7, TrialId(4))
    generated = stimulus(case)
    experiment = Experiment(
        'p9', 1, 1, (FlyWireNeuronId(10),), (100.0,), (FlyWireNeuronId(999),)
    )
    calls: list[str] = []

    def persist(
        output: Path, definition: Experiment, pin: InputPin, value: Stimulus
    ) -> Stimulus:
        calls.append('persist')
        assert definition is experiment and value is generated
        return value

    record = build_stimulus_recorder(persist)
    assert calls == []
    with pytest.raises(ValueError, match='Experiment neurons absent.*999'):
        record(
            Path('/fresh'),
            network(),
            experiment,
            InputPin('csv', 'parquet', 2, 0),
            generated,
        )
    assert calls == ['persist']


def test_writer_failure_precedes_mapping_and_is_propagated() -> None:
    case = ParityCase('p9', 7, TrialId(4))
    experiment = Experiment(
        'p9', 1, 1, (FlyWireNeuronId(10),), (100.0,), (FlyWireNeuronId(999),)
    )
    calls: list[str] = []

    def persist(
        output: Path, definition: Experiment, pin: InputPin, value: Stimulus
    ) -> Stimulus:
        calls.append('persist')
        raise FileExistsError('occupied')

    record = build_stimulus_recorder(persist)
    with pytest.raises(FileExistsError, match='occupied'):
        record(
            Path('/fresh'),
            network(),
            experiment,
            InputPin('csv', 'parquet', 2, 0),
            stimulus(case),
        )
    assert calls == ['persist']


def test_recording_keeps_reloaded_object_and_duplicate_silenced_row_order() -> None:
    case = ParityCase('p9', 7, TrialId(4))
    generated = stimulus(case)
    stored = replace(generated, events=generated.events.copy())
    stored.events.setflags(write=False)
    experiment = Experiment(
        'p9',
        1,
        1,
        (FlyWireNeuronId(10),),
        (100.0,),
        (FlyWireNeuronId(20), FlyWireNeuronId(10), FlyWireNeuronId(20)),
    )

    def persist(
        output: Path, definition: Experiment, pin: InputPin, value: Stimulus
    ) -> Stimulus:
        assert value is generated and definition is experiment
        return stored

    actual, silenced = build_stimulus_recorder(persist)(
        Path('/fresh'),
        network(),
        experiment,
        InputPin('csv', 'parquet', 2, 0),
        generated,
    )
    assert actual is stored and not actual.events.flags.writeable
    assert silenced == (NeuronRow(1), NeuronRow(0), NeuronRow(1))
