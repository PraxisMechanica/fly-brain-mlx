import hashlib
import importlib.metadata
import json
import platform
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import mlx.core as mx
import torch

from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.simulation.backend.bucketed import prepare_observed
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.models import Connectome, InputPin
from fly_brain.simulation.stimuli import generate, neuron_indices
from fly_brain.simulation.storage import persist_stimulus

from .brian_jobs import build
from .case_execution import execute
from .case_report import write
from .torch_setup import prepare as prepare_cpu


def run(
    connectome: Connectome,
    pin: InputPin,
    case: ParityCase,
    output: Path,
    precision: str,
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

    experiment = EXPERIMENTS[case.experiment]
    stimulus = persist_stimulus(
        output,
        experiment,
        pin,
        generate(connectome, experiment, case.steps, (case.trial,)),
    )
    silenced = neuron_indices(connectome, experiment.silenced_ids)
    with (output / 'environment.json').open('x') as artifact:
        json.dump(
            {
                'python': sys.version,
                'platform': platform.platform(),
                'versions': {
                    name: importlib.metadata.version(name)
                    for name in ('mlx', 'mlx-metal', 'numpy', 'brian2', 'torch')
                },
                'MLX_ENABLE_TF32': precision,
                'compilation': 'disabled',
                'device': mx.device_info(),
                'cpu_threads': torch.get_num_threads(),
                'cpu_interop_threads': torch.get_num_interop_threads(),
                'cpu_default_dtype': str(torch.get_default_dtype()),
                'cpu_deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
                'source_sha256': {
                    name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                    for name, module in sys.modules.copy().items()
                    if name.startswith('fly_brain.') and module.__file__ is not None
                },
                'scope': 'Qualification execution; input load is outside elapsed timing. No benchmark or unified-memory claim.',
            },
            artifact,
            indent=2,
            allow_nan=False,
        )
    progress('building-reference')
    job = build(
        connectome,
        stimulus.targets,
        silenced,
        stimulus.events[0],
        output / 'reference-build',
    )
    with (output / 'reference-job.json').open('x') as artifact:
        json.dump(
            {
                'directory': str(job.directory),
                'shape': asdict(job.shape),
                'observed': job.observed,
                'files': job.files,
            },
            artifact,
            indent=2,
        )
    progress('preparing-engines')
    mlx, read_rows = prepare_observed(connectome, stimulus.targets, silenced, precision)
    cpu = prepare_cpu(connectome, stimulus.targets, silenced, 1)
    execute(
        job,
        mlx,
        cpu,
        connectome,
        stimulus,
        output / 'observations',
        progress,
        read_rows=read_rows,
    )
    report = write(case, connectome, pin, stimulus, output / 'observations', output)
    progress('case-recorded')
    return report
