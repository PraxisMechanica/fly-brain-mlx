import json
from collections.abc import Mapping
from dataclasses import asdict
from functools import partial
from pathlib import Path
from time import perf_counter

import mlx.core as mx
import torch

from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.ports import ConnectomeSilencer, ObservationAssembly
from fly_brain.qualification.spike_comparison_ports import (
    CaseScorer,
    CoordinateValidator,
    ReferenceClockConverter,
)
from fly_brain.qualification.stimulus_ports import (
    CaseStimulusPreparation,
    ExperimentReader,
)
from fly_brain.simulation.models import Connectome, InputPin

from .brian_jobs import build
from .case_execution import execute
from .case_report import require_first_replay, write
from .environment import write as write_environment
from .reference_identity import create as reference_identity
from .reference_identity import file_record
from .torch_setup import prepare as prepare_cpu


def run(
    connectome: Connectome,
    pin: InputPin,
    case: ParityCase,
    output: Path,
    precision: str,
    *,
    reference_parameters: Mapping[str, float],
    silence: ConnectomeSilencer,
    prepare_stimulus: CaseStimulusPreparation,
    read_experiment: ExperimentReader,
    assemble_observations: ObservationAssembly,
    score: CaseScorer,
    validate: CoordinateValidator,
    convert_clock: ReferenceClockConverter,
) -> dict[str, object]:
    if case not in required_cases():
        raise ValueError('Qualification requires a prescribed frozen case')
    if precision != '0' or not mx.metal.is_available() or torch.get_num_threads() != 1:
        raise RuntimeError(
            'Parity requires Metal precision zero and one CPU reference thread'
        )
    mx.disable_compile()
    started = perf_counter()

    def progress(phase: str) -> None:
        print(
            json.dumps({'phase': phase, 'elapsed_s': perf_counter() - started}),
            flush=True,
        )

    stimulus, silenced = prepare_stimulus(connectome, pin, case, output)
    write_environment(output, precision)
    progress('building-reference')
    job = build(
        connectome,
        stimulus.targets,
        silenced,
        stimulus.events[0],
        output / 'reference-build',
        bind_build=True,
    )
    if job.build_context is None:
        raise ValueError('Paired qualification requires bound reference build context')
    digest, identity = reference_identity(
        connectome,
        stimulus,
        silenced,
        job.shape,
        job.files,
        job.directory,
        job.build_context,
    )
    with (output / 'reference-job.json').open('x') as artifact:
        json.dump(
            {
                'directory': str(job.directory),
                'shape': asdict(job.shape),
                'observed': job.observed,
                'files': job.files,
                'producer_sha256': digest,
                'producer': identity,
                'executable': file_record(job.directory / 'main'),
            },
            artifact,
            indent=2,
        )
    progress('preparing-engines')
    factory, read_rows = assemble_observations(
        connectome, stimulus.targets, silenced, precision
    )
    cpu = prepare_cpu(
        connectome,
        stimulus.targets,
        silenced,
        1,
        reference_parameters=reference_parameters,
        silence=silence,
    )
    execute(
        job,
        factory,
        cpu,
        connectome,
        stimulus,
        output / 'observations',
        progress,
        read_rows=read_rows,
        check_first=partial(
            require_first_replay,
            connectome=connectome,
            steps=case.steps,
            score=score,
            validate=validate,
            convert_clock=convert_clock,
        ),
    )
    report = write(
        case,
        connectome,
        pin,
        stimulus,
        output / 'observations',
        output,
        score=score,
        validate=validate,
        convert_clock=convert_clock,
        read_experiment=read_experiment,
    )
    progress('case-recorded')
    return report
