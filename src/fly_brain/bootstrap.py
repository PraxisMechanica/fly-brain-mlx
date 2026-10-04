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


def input_audit(project: Path, output: Path) -> dict[str, object]:
    from fly_brain.qualification.adapters.connectome_probe import run
    from fly_brain.simulation.inputs import load_connectome
    from fly_brain.simulation.models import InputPin

    pin = InputPin(
        '52b0ac6094cd32c546f8d4c341e094376f48f4e791f8db9b166de5dff8199ea4',
        'efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347',
        138639,
        15091983,
    )
    connectome = load_connectome(
        project / 'data/2025_Completeness_783.csv',
        project / 'data/2025_Connectivity_783.parquet',
        pin,
    )
    return run(connectome, pin, output)
