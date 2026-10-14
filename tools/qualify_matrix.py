"""Run the frozen 52-case matrix and its prescribed sugar/P9 batch checks."""

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase, QualificationRequest
from fly_brain.simulation.models import Connectome, ExperimentName, InputPin
from fly_brain.simulation.ports import StimulusGenerator


def case_name(case: ParityCase) -> str:
    return f'{case.experiment}-{case.steps}-{case.trial}'


def canonical_inputs(
    connectome: Connectome,
    pin: InputPin,
    output: Path,
    generate: StimulusGenerator,
) -> dict[ParityCase, str]:
    from fly_brain.qualification.adapters.batch_stimulus import load
    from fly_brain.simulation.stimulus_service import read_experiment
    from fly_brain.simulation.storage import persist_stimulus

    if np.__version__ != '1.26.4':
        raise RuntimeError('Canonical qualification requires NumPy 1.26.4')
    output.mkdir(parents=True, exist_ok=False)
    cases = required_cases()
    hashes: dict[ParityCase, str] = {}
    names: dict[ExperimentName, None] = dict.fromkeys(case.experiment for case in cases)
    for name in names:
        selected = tuple(case for case in cases if case.experiment == name)
        steps = max(case.steps for case in selected)
        trials = tuple(sorted({case.trial for case in selected}))
        configuration = read_experiment(name)
        probabilities = np.asarray(configuration.rates_hz, dtype=np.float64) * 0.0001
        if not np.all((probabilities >= 0) & (probabilities <= 1)):
            raise ValueError('Canonical channel probabilities must be in [0, 1]')
        longest = generate(connectome, configuration, steps, trials, 20261004)
        for position, trial in enumerate(trials):
            random = np.random.Generator(
                np.random.PCG64(
                    np.random.SeedSequence(
                        [20261004, configuration.generator_code, trial]
                    )
                )
            )
            expected = (
                random.random((steps, len(configuration.activated_ids))) < probabilities
            ).astype(np.uint8)
            if not np.array_equal(longest.events[position], expected):
                raise ValueError(
                    'Canonical batch differs from independent PCG64 replay'
                )
        if name != 'silent' and len(
            {hashlib.sha256(row.tobytes()).hexdigest() for row in longest.events}
        ) != len(trials):
            raise ValueError('Prescribed nonempty trial streams are not distinct')
        for case in selected:
            actual = generate(
                connectome, configuration, case.steps, (case.trial,), 20261004
            )
            repeated = generate(
                connectome, configuration, case.steps, (case.trial,), 20261004
            )
            prefix = longest.events[trials.index(case.trial) :][:1, : case.steps]
            if not np.array_equal(actual.events, prefix):
                raise ValueError('Duration prefix or standalone trial input differs')
            if not np.array_equal(actual.events, repeated.events):
                raise ValueError('Canonical regeneration differs')
            destination = output / case_name(case)
            persist_stimulus(destination, configuration, pin, actual)
            restored = load(destination, configuration, pin)
            if not np.array_equal(restored.events, actual.events):
                raise ValueError('Canonical saved input differs')
            hashes[case] = restored.sha256
    for case in cases:
        if case.experiment == 'sugar-silenced':
            if hashes[case] != hashes[ParityCase('sugar', case.steps, case.trial)]:
                raise ValueError('Silencing changed the prescribed sugar events')
    with (output / 'preflight.json').open('x') as artifact:
        json.dump(
            {
                'accepted': True,
                'cases': [
                    {'case': asdict(case), 'sha256': hashes[case]} for case in cases
                ],
                'regeneration_reload_prefix_and_trial_checks': True,
                'independent_generator': 'NumPy 1.26.4 PCG64(SeedSequence)',
                'seed': 20261004,
                'scope': 'Canonical inputs only; no simulation or parity acceptance.',
            },
            artifact,
            indent=2,
            allow_nan=False,
        )
    return hashes


def run(request: QualificationRequest) -> dict[str, object]:
    from fly_brain.bootstrap import pinned_inputs, stimulus
    from fly_brain.comparison.acceptance import (
        evaluate_case,
        steps_from_reference_clock,
        validate_coordinates,
    )
    from fly_brain.comparison.diagnostics import time_bin_counts
    from fly_brain.comparison.pooling import measure_trials
    from fly_brain.qualification.adapters.batch_environment import (
        read_environment,
    )
    from fly_brain.qualification.adapters.case_replay import require_complete_replay
    from fly_brain.qualification.adapters.case_report import encode
    from fly_brain.qualification.adapters.case_spikes import load as load_spikes
    from fly_brain.qualification.matrix_diagnostics import CaseRasters
    from fly_brain.qualification.matrix_diagnostics import (
        summarize as group_diagnostics,
    )

    request.output.mkdir(parents=True, exist_ok=False)
    checkpoint = subprocess.check_output(
        ['git', '-C', str(request.project), 'rev-parse', 'HEAD'], text=True
    ).strip()
    script = Path(__file__).resolve()
    relative = str(script.relative_to(request.project))
    if script.read_bytes() != subprocess.check_output(
        ['git', '-C', str(request.project), 'show', checkpoint + ':' + relative]
    ):
        raise ValueError('Commit the matrix controller before full qualification')
    with (request.output / 'matrix-launch.json').open('x') as artifact:
        json.dump(
            {
                'commit': checkpoint,
                'controller': relative,
                'controller_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
                'python_executable': sys.executable,
                'scope': 'Controller launch; individual cases record their own environment and source inventories.',
            },
            artifact,
            indent=2,
        )
    (request.output / 'cases').mkdir()
    (request.output / 'batches').mkdir()
    (request.output / 'commands').mkdir()
    connectome, pin = pinned_inputs()(request.project)
    hashes = canonical_inputs(connectome, pin, request.output / 'canonical', stimulus())
    cases = required_cases()
    completed: list[dict[str, object]] = []
    batches: dict[str, bool] = {}
    rasters: list[CaseRasters] = []
    invalid: list[ParityCase] = []
    failed: list[ParityCase] = []

    def read_launch(commit: str, path: str) -> bytes:
        return subprocess.check_output(
            ['git', '-C', str(request.project), 'show', commit + ':' + path]
        )

    def summarize() -> dict[str, object]:
        complete = len(completed) == len(cases) and set(batches) == {'sugar', 'p9'}
        accepted = (
            complete
            and all(row['accepted'] for row in completed)
            and all(batches.values())
        )
        result: dict[str, object] = {
            'accepted': accepted,
            'complete': complete,
            'required_cases': len(cases),
            'visited_cases': len(completed),
            'valid_cases': len(rasters),
            'cases': completed,
            'missing': [asdict(case) for case in cases[len(completed) :]],
            'batches': batches,
            'groups': [
                asdict(group)
                for group in group_diagnostics(
                    tuple(rasters),
                    tuple(invalid),
                    tuple(failed),
                    measure=measure_trials,
                    count_bins=time_bin_counts,
                )
            ],
            'scope': 'Frozen paired matrix with fresh engine repeats and prescribed batches. Stops on an unaccepted or invalid case; incomplete coverage never grants acceptance.',
        }
        with (request.output / 'matrix.json').open('x') as artifact:
            json.dump(result, artifact, indent=2, default=encode, allow_nan=False)
        return result

    for number, case in enumerate(cases, 1):
        name = case_name(case)
        destination = request.output / 'cases' / name
        command = [
            sys.executable,
            '-m',
            'fly_brain',
            'qualify-parity',
            '--project',
            str(request.project),
            '--output',
            str(destination),
            '--experiment',
            case.experiment,
            '--duration-s',
            str(case.steps * 0.0001),
            '--trial',
            str(case.trial),
        ]
        print(json.dumps({'case': number, 'of': len(cases), 'name': name}), flush=True)
        with (request.output / 'commands' / (name + '.log')).open('x') as log:
            process = subprocess.run(
                command,
                cwd=request.project,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        path = destination / 'case.json'
        accepted = False
        if path.exists():
            report = json.loads(path.read_text())
            if report['case'] != asdict(case):
                raise ValueError('Recorded case identity differs from its invocation')
            if report['stimulus_sha256'] != hashes[case]:
                raise ValueError('Engine case input differs from canonical preflight')
            require_complete_replay(destination, case.steps)
            launch = json.loads((destination / 'launch.json').read_text())
            read_environment(
                request.project, (destination, launch['commit']), read_launch
            )
            spikes, _ = load_spikes(
                connectome,
                case.steps,
                destination / 'observations/paired-first',
                destination / 'observations/cpu-first',
                validate=validate_coordinates,
                convert_clock=steps_from_reference_clock,
            )
            measured = evaluate_case(
                spikes['brian'], spikes['mlx'], spikes['torch'], case.steps * 0.0001
            )
            if measured.checks != report['metric_acceptance']['checks']:
                raise ValueError('Recorded metric gates differ from native rescoring')
            rasters.append(
                CaseRasters(case, spikes['brian'], spikes['mlx'], spikes['torch'])
            )
            accepted = (
                process.returncode == 0
                and report['case_accepted'] is True
                and measured.accepted
            )
            if not accepted:
                failed.append(case)
        else:
            invalid.append(case)
        completed.append(
            {
                'case': asdict(case),
                'exit_code': process.returncode,
                'accepted': accepted,
            }
        )
        if not accepted:
            return summarize()
    for experiment in ('sugar', 'p9'):
        destination = request.output / 'batches' / experiment
        with (request.output / 'commands' / (experiment + '-batch.log')).open(
            'x'
        ) as log:
            process = subprocess.run(
                [
                    sys.executable,
                    '-m',
                    'tools.qualify_batch',
                    '--project',
                    str(request.project),
                    '--output',
                    str(destination),
                    '--experiment',
                    experiment,
                    '--singletons',
                    str(request.output / 'cases'),
                ],
                cwd=request.project,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        path = destination / 'batch.json'
        batches[experiment] = (
            process.returncode == 0
            and path.exists()
            and json.loads(path.read_text())['accepted'] is True
        )
        if not batches[experiment]:
            return summarize()
    return summarize()


def main() -> int:
    from fly_brain.qualification.presentation import diagnostic_display
    from fly_brain.qualification.schemas import QualificationOptions

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    request = QualificationOptions(
        project=arguments.project, output=arguments.output
    ).to_request()
    report = run(request)
    exit_code = 0 if report['accepted'] else 1
    print(json.dumps(diagnostic_display(report, request.output, exit_code), indent=2))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
