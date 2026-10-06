import json
from collections.abc import Callable
from pathlib import Path

from fly_brain.qualification.ports import ReductionReader
from fly_brain.simulation.backend.engines import Execution
from fly_brain.simulation.models import Connectome, Stimulus

from .active_cpu import step as active_cpu_step
from .brian_jobs import BrianJob
from .paired_collect import collect as collect_paired
from .replay_evidence import cpu as verify_cpu
from .replay_evidence import paired as verify_paired
from .torch_collect import collect as collect_cpu
from .torch_reference import TorchModel


def execute(
    job: BrianJob,
    mlx: Execution,
    cpu: TorchModel,
    connectome: Connectome,
    stimulus: Stimulus,
    output: Path,
    progress: Callable[[str], None],
    *,
    read_rows: ReductionReader,
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for mode in ('first', 'repeat'):
        progress('paired-' + mode)
        collect_paired(
            job,
            mlx,
            connectome,
            stimulus,
            output / ('paired-' + mode),
            read_rows=read_rows,
        )
    advance_cpu = active_cpu_step(cpu)
    with (output / 'cpu-evaluation.json').open('x') as artifact:
        json.dump(
            {
                'mode': 'active-source-exact-integer',
                'dynamics': 'Pinned original TorchModel components and scaling',
                'scope': 'Qualified singleton comparator evaluation',
                'qualification': 'docs/evidence/execution-time-investigation/active-cpu-qualification/full-native/parent-verification.json',
            },
            artifact,
            indent=2,
        )
    for mode in ('first', 'repeat'):
        progress('cpu-' + mode)
        collect_cpu(cpu, stimulus, output / ('cpu-' + mode), advance_cpu)
    verify_paired(output / 'paired-first', output / 'paired-repeat')
    verify_cpu(output / 'cpu-first', output / 'cpu-repeat')
    progress('replay-verified')
