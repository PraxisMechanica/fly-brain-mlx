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

from .qualification_cases import case_name, read_index, verify_case


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


def run(
    request: QualificationRequest,
    *,
    resume_from: Path | None = None,
    reviews: Path | None = None,
    verify_only: bool = False,
) -> dict[str, object]:
    from fly_brain.bootstrap import pinned_inputs, stimulus
    from fly_brain.comparison.diagnostics import time_bin_counts
    from fly_brain.comparison.pooling import measure_trials
    from fly_brain.qualification.adapters.case_report import encode
    from fly_brain.qualification.matrix_diagnostics import CaseRasters
    from fly_brain.qualification.matrix_diagnostics import (
        summarize as group_diagnostics,
    )

    request.output.mkdir(parents=True, exist_ok=False)
    prior = read_index(resume_from / 'matrix.json') if resume_from is not None else {}
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
                'resume_from': str(resume_from) if resume_from is not None else None,
                'reviews': str(reviews) if reviews is not None else None,
                'verify_only': verify_only,
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
            'verify_only': verify_only,
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
        with (request.output / 'matrix.json').open('w') as artifact:
            json.dump(result, artifact, indent=2, default=encode, allow_nan=False)
        return result

    summary = summarize()
    for number, case in enumerate(cases, 1):
        name = case_name(case)
        previous = prior.get(case)
        reused = previous is not None and (previous.directory / 'case.json').is_file()
        if verify_only and not reused:
            return summarize()
        destination = (
            previous.directory
            if previous is not None and reused
            else request.output / 'cases' / name
        )
        review = (
            reviews / name
            if reviews is not None and (reviews / name).is_dir()
            else (previous.review if previous is not None else None)
        )
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
        print(
            json.dumps(
                {'case': number, 'of': len(cases), 'name': name, 'reused': reused}
            ),
            flush=True,
        )
        if reused and previous is not None:
            exit_code = previous.exit_code
        else:
            with (request.output / 'commands' / (name + '.log')).open('x') as log:
                process = subprocess.run(
                    command,
                    cwd=request.project,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
            exit_code = process.returncode
        path = destination / 'case.json'
        accepted = False
        record: dict[str, object] = {}
        if path.exists():
            verified = verify_case(
                request.project,
                destination,
                case,
                connectome,
                pin,
                canonical_sha256=hashes[case],
                review=review,
                bound_files=previous.artifact_sha256
                if previous is not None and reused
                else None,
            )
            if (
                previous is not None
                and previous.review_sha256
                and review == previous.review
                and verified.review_sha256 != previous.review_sha256
            ):
                raise ValueError('Previously bound causal decision changed')
            rasters.append(verified.rasters)
            accepted = verified.accepted and (
                exit_code == 0 or bool(verified.review_sha256)
            )
            record = verified.record()
            if not accepted:
                failed.append(case)
        else:
            invalid.append(case)
        completed.append(
            {
                **record,
                'case': asdict(case),
                'directory': str(destination),
                'exit_code': exit_code,
                'reused': reused,
                'accepted': accepted,
            }
        )
        summary = summarize()
        if not accepted:
            return summary
    if verify_only:
        return summary
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
                    str(request.output / 'matrix.json'),
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
    parser.add_argument('--resume-from', type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    arguments = parser.parse_args()
    request = QualificationOptions(
        project=arguments.project, output=arguments.output
    ).to_request()
    if arguments.verify_only and arguments.resume_from is None:
        parser.error('--verify-only requires --resume-from')
    report = run(
        request,
        resume_from=arguments.resume_from.resolve()
        if arguments.resume_from is not None
        else None,
        reviews=arguments.reviews.resolve() if arguments.reviews is not None else None,
        verify_only=arguments.verify_only,
    )
    exit_code = 0 if report['accepted'] else 1
    print(json.dumps(diagnostic_display(report, request.output, exit_code), indent=2))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
