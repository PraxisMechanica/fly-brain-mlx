"""Compare one prescribed four-trial batch with its qualified singleton cases."""

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Literal

from fly_brain.qualification.models import ParityCase, QualificationRequest
from fly_brain.simulation.identifiers import TrialId


def run(
    request: QualificationRequest,
    experiment: Literal['sugar', 'p9'],
    singletons: Path,
) -> dict[str, object]:
    from fly_brain.bootstrap import configure_mlx

    precision = configure_mlx()
    import mlx.core as mx
    import torch

    from fly_brain.bootstrap import pinned_inputs, stimulus
    from fly_brain.comparison.acceptance import validate_coordinates
    from fly_brain.qualification.adapters.active_cpu import step as active_cpu_step
    from fly_brain.qualification.adapters.batch_environment import require_environments
    from fly_brain.qualification.adapters.batch_stimulus import load
    from fly_brain.qualification.adapters.batch_verify import compare
    from fly_brain.qualification.adapters.case_replay import require_complete_replay
    from fly_brain.qualification.adapters.environment import write as write_environment
    from fly_brain.qualification.adapters.mlx_batch_collect import (
        collect as collect_mlx,
    )
    from fly_brain.qualification.adapters.replay_evidence import verify
    from fly_brain.qualification.adapters.torch_collect import collect as collect_cpu
    from fly_brain.qualification.adapters.torch_setup import prepare as prepare_cpu
    from fly_brain.qualification.batch_identity import require_stimuli
    from fly_brain.qualification.reference_parameters import model_parameters
    from fly_brain.simulation.module import build_connectome_silencer
    from fly_brain.simulation.observation_module import build_observation_assembly
    from fly_brain.simulation.stimulus_service import read_experiment
    from fly_brain.simulation.storage import persist_stimulus

    torch.set_num_threads(1)
    mx.disable_compile()
    started = perf_counter()
    paths: dict[TrialId, Path] = {}
    launches: dict[TrialId, tuple[Path, str]] = {}
    for trial in map(TrialId, range(4)):
        directory = singletons / f'{experiment}-10000-{trial}'
        record = json.loads((directory / 'case.json').read_text())
        if (
            record['case'] != asdict(ParityCase(experiment, 10000, trial))
            or record['case_accepted'] is not True
        ):
            raise ValueError(f'Batch requires its accepted singleton case: {directory}')
        require_complete_replay(directory, 10000)
        paths[trial] = directory
        launch = json.loads((directory / 'launch.json').read_text())
        launches[trial] = directory, launch['commit']

    connectome, pin = pinned_inputs()(request.project)
    configuration = read_experiment(experiment)
    canonical = stimulus()(
        connectome, configuration, 10000, tuple(map(TrialId, range(4))), 20261004
    )
    persist_stimulus(request.output, configuration, pin, canonical)
    batch = load(request.output, configuration, pin)
    hashes = require_stimuli(
        canonical,
        batch,
        {trial: load(path, configuration, pin) for trial, path in paths.items()},
    )
    write_environment(request.output, precision)

    def read_launch(commit: str, path: str) -> bytes:
        return subprocess.check_output(
            ['git', '-C', str(request.project), 'show', commit + ':' + path]
        )

    launch = json.loads((request.output / 'launch.json').read_text())
    script = Path(__file__).resolve()
    if (
        hashlib.sha256(
            read_launch(launch['commit'], str(script.relative_to(request.project)))
        ).hexdigest()
        != hashlib.sha256(script.read_bytes()).hexdigest()
    ):
        raise ValueError('Commit the batch controller before qualification')
    common_sources = require_environments(
        request.project,
        (request.output, launch['commit']),
        launches,
        read_launch,
    )
    factory, _ = build_observation_assembly()(connectome, batch.targets, (), precision)
    cpu = prepare_cpu(
        connectome,
        batch.targets,
        (),
        4,
        reference_parameters=model_parameters(),
        silence=build_connectome_silencer(),
    )
    advance_cpu = active_cpu_step(cpu)
    for mode in ('first', 'repeat'):
        print(json.dumps({'phase': 'mlx-' + mode}), flush=True)
        collect_mlx(factory, connectome, batch, request.output / ('mlx-' + mode))
        print(json.dumps({'phase': 'cpu-' + mode}), flush=True)
        collect_cpu(cpu, batch, request.output / ('cpu-' + mode), advance_cpu)

    for engine, text_file in (
        ('mlx', 'phase-digests.jsonl'),
        ('cpu', 'native-digests.jsonl'),
    ):
        verify(
            request.output / (engine + '-first'),
            request.output / (engine + '-repeat'),
            (text_file,),
            ('native.npz',),
        )
    comparisons: dict[str, object] = {}
    gates: dict[str, bool] = {}
    for engine in ('mlx', 'cpu'):
        corresponding = {
            trial: path
            / 'observations'
            / ('paired-first' if engine == 'mlx' else 'cpu-first')
            for trial, path in paths.items()
        }
        for mode in ('first', 'repeat'):
            difference, finals = compare(
                request.output / (engine + '-' + mode),
                corresponding,
                engine,
                10000,
                len(connectome.neuron_ids),
                len(connectome.sources),
                len(batch.targets),
                validate=validate_coordinates,
            )
            name = engine + '-' + mode
            comparisons[name] = {
                'first_phase_difference': asdict(difference)
                if difference is not None
                else None,
                'final_floating_fields_different': finals,
            }
            gates[name + '-complete-native-equality'] = difference is None and not any(
                finals.values()
            )
    report: dict[str, object] = {
        'accepted': all(gates.values()),
        'experiment': experiment,
        'steps': 10000,
        'trial_indices': [0, 1, 2, 3],
        'fresh_repeats_bit_identical': True,
        'canonical_singleton_event_sha256': list(hashes),
        'common_source_sha256': common_sources,
        'comparisons': comparisons,
        'gates': gates,
        'elapsed_s': perf_counter() - started,
        'scope': 'Prescribed one-second four-trial batch. Exact native phase, event and queue equality is sufficient for the existing state budgets. A difference requires diagnosis before acceptance; no floating tolerance is enlarged.',
    }
    with (request.output / 'batch.json').open('x') as artifact:
        json.dump(report, artifact, indent=2, allow_nan=False)
    return report


def main() -> int:
    from fly_brain.qualification.presentation import diagnostic_display
    from fly_brain.qualification.schemas import QualificationOptions

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--experiment', choices=('sugar', 'p9'), required=True)
    parser.add_argument('--singletons', type=Path, required=True)
    arguments = parser.parse_args()
    request = QualificationOptions(
        project=arguments.project, output=arguments.output
    ).to_request()
    report = run(request, arguments.experiment, arguments.singletons.resolve())
    exit_code = 0 if report['accepted'] else 1
    print(json.dumps(diagnostic_display(report, request.output, exit_code), indent=2))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
