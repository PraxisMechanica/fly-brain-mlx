from collections.abc import Callable
from pathlib import Path

from fly_brain.simulation.backend.engines import Execution
from fly_brain.simulation.models import Connectome, Stimulus

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
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for mode in ('first', 'repeat'):
        progress('paired-' + mode)
        collect_paired(job, mlx, connectome, stimulus, output / ('paired-' + mode))
    for mode in ('first', 'repeat'):
        progress('cpu-' + mode)
        collect_cpu(cpu, stimulus, output / ('cpu-' + mode))
    verify_paired(output / 'paired-first', output / 'paired-repeat')
    verify_cpu(output / 'cpu-first', output / 'cpu-repeat')
    progress('replay-verified')
