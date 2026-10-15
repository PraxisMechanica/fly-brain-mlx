import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import get_args

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.comparison.acceptance import (
    evaluate_case,
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.comparison.models import FlyWireSpikeSteps, SpikeSteps
from fly_brain.infrastructure.seeded_random import uniforms
from fly_brain.qualification.adapters import case_report
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.module import build_case_stimulus
from fly_brain.qualification.spike_comparison_ports import (
    CoordinateValidator,
    ReferenceClockConverter,
)
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.identifiers import (
    FlyWireIds64,
    NeuronRow,
    NeuronRows32,
    TrialId,
)
from fly_brain.simulation.models import (
    Connectome,
    Experiment,
    ExperimentName,
    InputPin,
    Stimulus,
)
from fly_brain.simulation.module import (
    build_experiment_reader,
    build_stimulus,
    build_stimulus_recorder,
)
from fly_brain.simulation.stimuli import neuron_indices
from fly_brain.simulation.storage import persist_stimulus

pytestmark = pytest.mark.integration


def network() -> Connectome:
    ids = tuple(
        dict.fromkeys(
            identifier
            for experiment in EXPERIMENTS.values()
            for identifier in (*experiment.activated_ids, *experiment.silenced_ids)
        )
    )
    return Connectome(
        FlyWireIds64(np.array(ids, dtype=np.int64)),
        NeuronRows32(np.array([], dtype=np.int32)),
        NeuronRows32(np.array([], dtype=np.int32)),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )


@pytest.mark.parametrize('name', get_args(ExperimentName))
@pytest.mark.parametrize('trial', range(5))
def test_owned_preparation_matches_original_stimulus_and_saved_bytes(
    tmp_path: Path, name: ExperimentName, trial: int
) -> None:
    connectome = network()
    pin = InputPin('fixture-csv', 'fixture-parquet', len(connectome.neuron_ids), 0)
    case = ParityCase(name, 17, TrialId(trial))
    experiment = EXPERIMENTS[name]
    generate = build_stimulus(uniforms)
    expected = persist_stimulus(
        tmp_path / 'original',
        experiment,
        pin,
        generate(connectome, experiment, case.steps, (case.trial,), 20261004),
    )
    expected_silenced = neuron_indices(connectome, experiment.silenced_ids)
    prepare = build_case_stimulus(
        build_experiment_reader(), generate, build_stimulus_recorder(persist_stimulus)
    )
    actual, silenced = prepare(connectome, pin, case, tmp_path / 'owned')
    assert (actual.events.dtype, actual.events.shape, actual.events.tobytes()) == (
        expected.events.dtype,
        expected.events.shape,
        expected.events.tobytes(),
    )
    assert not actual.events.flags.writeable and not expected.events.flags.writeable
    fields = (
        'targets',
        'rates_hz',
        'trial_indices',
        'seed',
        'generator_code',
        'sha256',
    )
    assert tuple(getattr(actual, field) for field in fields) == tuple(
        getattr(expected, field) for field in fields
    )
    assert silenced == expected_silenced
    assert (tmp_path / 'owned/stimulus.npz').read_bytes() == (
        tmp_path / 'original/stimulus.npz'
    ).read_bytes()
    assert (tmp_path / 'owned/stimulus.json').read_bytes() == (
        tmp_path / 'original/stimulus.json'
    ).read_bytes()
    print(
        json.dumps(
            {
                'experiment': name,
                'trial': trial,
                'events': actual.sha256,
                'artifact': hashlib.sha256(
                    (tmp_path / 'owned/stimulus.npz').read_bytes()
                ).hexdigest(),
            }
        )
    )
    with pytest.raises(FileExistsError):
        prepare(connectome, pin, case, tmp_path / 'owned')


def test_report_reads_catalog_again_after_native_evidence_and_pending_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    connectome = network()
    pin = InputPin('csv', 'parquet', len(connectome.neuron_ids), 0)
    case = ParityCase('p9', 1000, TrialId(2))
    experiment = EXPERIMENTS[case.experiment]
    current = experiment
    calls: list[str] = []

    def read(name: ExperimentName) -> Experiment:
        assert name == case.experiment
        calls.append('catalog')
        return current

    recorder = build_stimulus_recorder(persist_stimulus)

    def record(
        output: Path,
        value: Connectome,
        definition: Experiment,
        inputs: InputPin,
        stimulus: Stimulus,
    ) -> tuple[Stimulus, tuple[NeuronRow, ...]]:
        calls.append('record')
        return recorder(output, value, definition, inputs, stimulus)

    output = tmp_path / 'case'
    stimulus, _ = build_case_stimulus(read, build_stimulus(uniforms), record)(
        connectome, pin, case, output
    )
    current = replace(experiment, generator_code=experiment.generator_code + 1)
    observations = output / 'observations'
    paired = observations / 'paired-first'
    paired.mkdir(parents=True)
    (paired / 'causal.json').write_text(
        json.dumps(
            {
                'steps': case.steps,
                'first_spike_step': None,
                'first_budget_violation': None,
            }
        )
    )

    def paired_check(first: Path, repeat: Path) -> None:
        calls.append('paired')

    def cpu_check(first: Path, repeat: Path) -> None:
        calls.append('cpu')

    def load(
        value: Connectome,
        steps: int,
        first: Path,
        cpu: Path,
        *,
        validate: CoordinateValidator,
        convert_clock: ReferenceClockConverter,
    ) -> tuple[dict[str, FlyWireSpikeSteps], dict[str, object]]:
        calls.append('load')
        empty = SpikeSteps(
            FlyWireIds64(np.array([], dtype=np.int64)), np.array([], dtype=np.int64)
        )
        return {engine: empty for engine in ('brian', 'mlx', 'torch')}, {}

    def pending(
        first: Path, steps: int, sources: NDArray[np.int32], neurons: int
    ) -> tuple[int, ...]:
        np.testing.assert_array_equal(sources, connectome.sources)
        assert neurons == len(connectome.neuron_ids)
        calls.append('pending')
        return (0,) * 18

    monkeypatch.setattr(case_report, 'verify_paired', paired_check)
    monkeypatch.setattr(case_report, 'verify_cpu', cpu_check)
    monkeypatch.setattr(case_report, 'load', load)
    monkeypatch.setattr(case_report, 'verify_pending', pending)
    report = case_report.write(
        case,
        connectome,
        pin,
        stimulus,
        observations,
        output,
        score=evaluate_case,
        validate=validate_coordinates,
        convert_clock=steps_from_reference_clock,
        read_experiment=read,
    )
    assert calls == ['catalog', 'record', 'paired', 'cpu', 'load', 'pending', 'catalog']
    saved = json.loads((output / 'case.json').read_text())
    assert saved['case_checks']['prescribed_seed_generator_targets_and_rates'] is False
    assert report['case_accepted'] is False and report['full_matrix_accepted'] is False
