import hashlib
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

LaunchReader = Callable[[str, str], bytes]
ExecutionEvidence = tuple[Path, str]

_SOURCES = frozenset(
    (
        'fly_brain.simulation.backend.core',
        'fly_brain.simulation.backend.arrays',
        'fly_brain.simulation.backend.engines',
        'fly_brain.simulation.backend.bucketed',
        'fly_brain.simulation.backend.accumulation',
        'fly_brain.simulation.mapping',
        'fly_brain.simulation.stimuli',
        'fly_brain.simulation.experiments',
        'fly_brain.qualification.adapters.mlx_observer',
        'fly_brain.qualification.adapters.mlx_ledger',
        'fly_brain.qualification.adapters.torch_reference',
        'fly_brain.qualification.adapters.torch_setup',
        'fly_brain.qualification.adapters.torch_observer',
        'fly_brain.qualification.adapters.torch_collect',
    )
)


class _Device(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra='forbid')
    device_name: str
    max_recommended_working_set_size: int
    memory_size: int
    architecture: str
    max_buffer_length: int
    resource_limit: int


class _Environment(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra='forbid')
    python: str
    platform: str
    versions: dict[str, str]
    MLX_ENABLE_TF32: Literal['0']
    compilation: Literal['disabled']
    device: _Device
    cpu_threads: int
    cpu_interop_threads: int
    cpu_default_dtype: Literal['torch.float32']
    cpu_deterministic_algorithms: bool
    source_sha256: dict[str, str]
    scope: str


def _read(
    project: Path, evidence: ExecutionEvidence, read_launch: LaunchReader
) -> _Environment:
    directory, launch = evidence
    environment = _Environment.model_validate_json(
        (directory / 'environment.json').read_text()
    )
    if environment.cpu_threads != 1 or environment.versions != {
        'mlx': '0.32.3',
        'mlx-metal': '0.32.3',
        'numpy': '1.26.4',
        'brian2': '2.8.0',
        'torch': '2.11.0',
    }:
        raise ValueError(
            'Batch evidence requires the frozen versions and CPU thread count'
        )
    if not _SOURCES <= environment.source_sha256.keys():
        raise ValueError('Batch evidence requires every numerical and observer source')
    for name, digest in environment.source_sha256.items():
        if not name.startswith('fly_brain.') or not all(
            part.isidentifier() for part in name.split('.')
        ):
            raise ValueError('Recorded executed source must identify a project module')
        base = project / 'src' / Path(*name.split('.'))
        path = (
            base.with_suffix('.py')
            if base.with_suffix('.py').is_file()
            else base / '__init__.py'
        )
        relative = str(path.relative_to(project))
        if (
            hashlib.sha256(path.read_bytes()).hexdigest() != digest
            or hashlib.sha256(read_launch(launch, relative)).hexdigest() != digest
        ):
            raise ValueError(
                f'Executed source differs from its launch or current source: {name}'
            )
    return environment


def require_environments(
    project: Path,
    batch: ExecutionEvidence,
    singletons: Mapping[int, ExecutionEvidence],
    read_launch: LaunchReader,
) -> dict[str, str]:
    if set(singletons) != {0, 1, 2, 3}:
        raise ValueError('Batch environment requires all four independent identities')
    actual = _read(project, batch, read_launch)
    settings = actual.model_dump(exclude={'source_sha256', 'scope'})
    common = dict(actual.source_sha256)
    for trial in range(4):
        expected = _read(project, singletons[trial], read_launch)
        if expected.model_dump(exclude={'source_sha256', 'scope'}) != settings:
            raise ValueError(f'Batch execution settings differ from singleton {trial}')
        common = {
            name: digest
            for name, digest in common.items()
            if name in expected.source_sha256
        }
        if any(
            expected.source_sha256[name] != digest for name, digest in common.items()
        ):
            raise ValueError(f'Shared executed sources differ for singleton {trial}')
    return common
