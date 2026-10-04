import os
import platform
from pathlib import Path

from fly_brain.comparison.models import ComparisonRequest, ComparisonResult
from fly_brain.comparison.service import compare
from fly_brain.qualification.models import QualificationRequest, QualificationResult
from fly_brain.qualification.service import qualify


def configure_mlx() -> str:
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise RuntimeError('The application requires Apple silicon and macOS')
    precision = os.environ.setdefault('MLX_ENABLE_TF32', '0')
    if precision != '0':
        raise RuntimeError('Launch with MLX_ENABLE_TF32=0')
    return precision


def qualification(request: QualificationRequest) -> QualificationResult:
    from fly_brain.qualification.adapters.pytest_runner import run_tests
    from fly_brain.qualification.adapters.results import write_result

    configure_mlx()
    return qualify(request, run_tests, write_result)


def comparison(request: ComparisonRequest, output: Path) -> ComparisonResult:
    from fly_brain.comparison.storage import read_spikes, write_comparison

    result = compare(request, read_spikes)
    write_comparison(output, result)
    return result


def accumulation(project: Path, output: Path) -> dict[str, object]:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.accumulation_probe import run

    return run(project, output, precision)


def factored(project: Path, output: Path) -> dict[str, object]:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.factored_probe import run

    return run(project, output, precision)


def replay(output: Path) -> dict[str, object]:
    from fly_brain.qualification.adapters.replay_probe import run

    return run(output)


def schedule(output: Path) -> dict[str, object]:
    from fly_brain.qualification.adapters.schedule_probe import run

    return run(output)
