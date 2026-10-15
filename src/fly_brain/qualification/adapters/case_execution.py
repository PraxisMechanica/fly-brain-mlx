import hashlib
import json
import multiprocessing
import os
from collections.abc import Callable
from pathlib import Path

import torch

from fly_brain.qualification.ports import ObservationSessionFactory, ReductionReader
from fly_brain.simulation.models import Connectome, Stimulus

from .active_cpu import step as active_cpu_step
from .brian_jobs import BrianJob
from .paired_collect import collect as collect_paired
from .replay_evidence import cpu as verify_cpu
from .replay_evidence import paired as verify_paired
from .torch_collect import collect as collect_cpu
from .torch_reference import TorchModel


def cpu_replays(
    model: TorchModel,
    stimulus: Stimulus,
    output: Path,
    interop_threads: int,
    deterministic: bool,
) -> None:
    torch.set_num_threads(1)
    if torch.get_num_interop_threads() != interop_threads:
        torch.set_num_interop_threads(interop_threads)
    torch.use_deterministic_algorithms(deterministic)
    if torch.get_default_dtype() != torch.float32 or (
        hashlib.sha256(stimulus.events.tobytes()).hexdigest() != stimulus.sha256
    ):
        raise ValueError('CPU worker input or default dtype differs from its launch')
    advance_cpu = active_cpu_step(model)
    with (output / 'cpu-evaluation.json').open('x') as artifact:
        json.dump(
            {
                'mode': 'active-source-exact-integer',
                'dynamics': 'Pinned original TorchModel components and scaling',
                'scope': 'Qualified singleton comparator evaluation',
                'qualification': 'docs/agent/numerical-contract.md',
                'pid': os.getpid(),
                'start_method': 'spawn',
                'cpu_threads': torch.get_num_threads(),
                'cpu_interop_threads': torch.get_num_interop_threads(),
                'cpu_default_dtype': str(torch.get_default_dtype()),
                'cpu_deterministic_algorithms': torch.are_deterministic_algorithms_enabled(),
                'stimulus_sha256': stimulus.sha256,
            },
            artifact,
            indent=2,
        )
    for mode in ('first', 'repeat'):
        print(json.dumps({'phase': 'cpu-' + mode, 'pid': os.getpid()}), flush=True)
        collect_cpu(model, stimulus, output / ('cpu-' + mode), advance_cpu)


def execute(
    job: BrianJob,
    factory: ObservationSessionFactory,
    cpu: TorchModel,
    connectome: Connectome,
    stimulus: Stimulus,
    output: Path,
    progress: Callable[[str], None],
    *,
    read_rows: ReductionReader,
    check_first: Callable[[Path], None],
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    worker = multiprocessing.get_context('spawn').Process(
        target=cpu_replays,
        args=(
            cpu,
            stimulus,
            output,
            torch.get_num_interop_threads(),
            torch.are_deterministic_algorithms_enabled(),
        ),
    )
    try:
        worker.start()
        progress('cpu-replays-started')
        progress('paired-first')
        collect_paired(
            job,
            factory,
            connectome,
            stimulus,
            output / 'paired-first',
            read_rows=read_rows,
        )
        worker.join()
        if worker.exitcode != 0:
            raise RuntimeError(f'CPU replay worker failed with exit {worker.exitcode}')
    finally:
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)
            if worker.is_alive():
                worker.kill()
                worker.join(timeout=5)
                if worker.is_alive():
                    raise RuntimeError('The owned CPU replay worker could not stop')
        worker.close()
    verify_cpu(output / 'cpu-first', output / 'cpu-repeat')
    progress('cpu-replays-verified')
    check_first(output)
    progress('first-replay-scored')
    progress('paired-repeat')
    collect_paired(
        job,
        factory,
        connectome,
        stimulus,
        output / 'paired-repeat',
        read_rows=read_rows,
    )
    verify_paired(output / 'paired-first', output / 'paired-repeat')
    progress('replay-verified')
