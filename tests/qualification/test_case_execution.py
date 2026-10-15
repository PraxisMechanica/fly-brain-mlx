import hashlib
import json
import multiprocessing
import os
from dataclasses import replace
from functools import partial
from pathlib import Path

import numpy as np
import pytest

from fly_brain.comparison.acceptance import (
    evaluate_case,
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.comparison.models import FlyWireSpikeSteps, MetricAcceptance
from fly_brain.qualification.adapters import case_execution
from fly_brain.qualification.adapters.active_cpu import step as active_cpu_step
from fly_brain.qualification.adapters.brian_jobs import build
from fly_brain.qualification.adapters.case_execution import execute
from fly_brain.qualification.adapters.case_report import require_first_replay, write
from fly_brain.qualification.adapters.replay_evidence import cpu as verify_cpu
from fly_brain.qualification.adapters.torch_collect import collect as collect_cpu
from fly_brain.qualification.adapters.torch_setup import prepare as prepare_cpu
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.reference_parameters import model_parameters
from fly_brain.simulation.identifiers import NeuronRow, TrialId
from fly_brain.simulation.models import InputPin
from fly_brain.simulation.module import (
    build_connectome_silencer,
    build_experiment_reader,
)
from fly_brain.simulation.observation_module import build_observation_sessions
from tests.support.observation_fixtures import fixture, stimulus_for

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


@pytest.mark.parametrize('empty', (False, True))
def test_each_engine_replays_fresh_state_with_complete_retained_evidence(
    precision: str, tmp_path: Path, empty: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = fixture(empty)
    events = case.events[:1]
    stimulus = stimulus_for(
        events, case.targets, (200.0,) * len(case.targets), (TrialId(0),)
    )
    job = build(case.connectome, case.targets, (3,), events[0], tmp_path / 'build')
    mlx, read_rows = build_observation_sessions(
        case.connectome, case.targets, (NeuronRow(3),), precision
    )
    cpu = prepare_cpu(
        case.connectome,
        case.targets,
        (NeuronRow(3),),
        1,
        reference_parameters=model_parameters(),
        silence=build_connectome_silencer(),
    )
    progress: list[str] = []
    output = tmp_path / 'evidence'
    check_first = partial(
        require_first_replay,
        connectome=case.connectome,
        steps=101,
        score=evaluate_case,
        validate=validate_coordinates,
        convert_clock=steps_from_reference_clock,
    )
    execute(
        job,
        mlx,
        cpu,
        case.connectome,
        stimulus,
        output,
        progress.append,
        read_rows=read_rows,
        check_first=check_first,
    )
    assert progress == [
        'cpu-replays-started',
        'paired-first',
        'cpu-replays-verified',
        'first-replay-scored',
        'paired-repeat',
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
        execute(
            job,
            mlx,
            cpu,
            case.connectome,
            stimulus,
            output,
            progress.append,
            read_rows=read_rows,
            check_first=check_first,
        )
    metadata = json.loads((output / 'cpu-evaluation.json').read_text())
    assert metadata['pid'] != os.getpid() and metadata['cpu_threads'] == 1
    assert metadata['start_method'] == 'spawn'
    assert (
        metadata['stimulus_sha256']
        == hashlib.sha256(stimulus.events.tobytes()).hexdigest()
    )
    collect_cpu(cpu, stimulus, tmp_path / 'serial-cpu', active_cpu_step(cpu))
    verify_cpu(output / 'cpu-first', tmp_path / 'serial-cpu')
    if not empty:
        active_before = {process.pid for process in multiprocessing.active_children()}

        def rejected_score(
            reference: FlyWireSpikeSteps,
            actual: FlyWireSpikeSteps,
            baseline: FlyWireSpikeSteps,
            duration_s: float,
        ) -> MetricAcceptance:
            measured = evaluate_case(reference, actual, baseline, duration_s)
            return replace(
                measured,
                checks={**measured.checks, 'qualification_test_rejected': False},
            )

        rejected = tmp_path / 'rejected'
        with pytest.raises(ValueError, match='First replay failed fixed gates'):
            execute(
                job,
                mlx,
                cpu,
                case.connectome,
                stimulus,
                rejected,
                progress.append,
                read_rows=read_rows,
                check_first=partial(check_first, score=rejected_score),
            )
        first_report = json.loads((rejected / 'first-replay.json').read_text())
        assert (
            first_report['first_replay_gates']['qualification_test_rejected'] is False
        )
        assert first_report['case_accepted'] is False
        assert not (rejected / 'paired-repeat').exists()

        failed_cpu = tmp_path / 'failed-cpu'
        with pytest.raises(RuntimeError, match='CPU replay worker failed'):
            execute(
                job,
                mlx,
                cpu,
                case.connectome,
                replace(stimulus, sha256='changed'),
                failed_cpu,
                progress.append,
                read_rows=read_rows,
                check_first=check_first,
            )
        assert not (failed_cpu / 'paired-repeat').exists()

        def broken_pair(*arguments: object, **options: object) -> None:
            raise RuntimeError('Owned pair failed')

        monkeypatch.setattr(case_execution, 'collect_paired', broken_pair)
        with pytest.raises(RuntimeError, match='Owned pair failed'):
            execute(
                job,
                mlx,
                cpu,
                case.connectome,
                stimulus,
                tmp_path / 'broken-pair',
                progress.append,
                read_rows=read_rows,
                check_first=check_first,
            )
        assert {
            process.pid for process in multiprocessing.active_children()
        } == active_before
    pin = InputPin('fixture', 'fixture', 6, len(case.connectome.sources))
    report = write(
        ParityCase('sugar', 101, TrialId(0)),
        case.connectome,
        pin,
        stimulus,
        output,
        tmp_path,
        score=evaluate_case,
        validate=validate_coordinates,
        convert_clock=steps_from_reference_clock,
        read_experiment=build_experiment_reader(),
    )
    assert (
        report['case_accepted'] is False
        and report['scientific_review_required'] is False
    )
    saved = json.loads((tmp_path / 'case.json').read_text())
    assert saved['case_checks']['required_frozen_case'] is False
    assert (
        saved['case_checks']['actual_final_pending_events_equal_when_history_is_common']
        is True
    )
    assert (
        saved['metric_acceptance']['mlx']['active_jaccard']['numerator']
        == saved['metric_acceptance']['mlx']['active_jaccard']['denominator']
    )
    with np.load(tmp_path / 'normalized-spikes.npz') as raster:
        assert raster['brian_neurons'].tobytes() == raster['mlx_neurons'].tobytes()
        assert raster['brian_steps'].tobytes() == raster['mlx_steps'].tobytes()
    with pytest.raises(FileExistsError):
        write(
            ParityCase('sugar', 101, TrialId(0)),
            case.connectome,
            pin,
            stimulus,
            output,
            tmp_path,
            score=evaluate_case,
            validate=validate_coordinates,
            convert_clock=steps_from_reference_clock,
            read_experiment=build_experiment_reader(),
        )
