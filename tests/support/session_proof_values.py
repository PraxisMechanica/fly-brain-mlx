import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import numpy as np
import pytest
from numpy.typing import NDArray
from pydantic import BaseModel

from fly_brain.simulation.observations import HostArray

Scalar = TypeVar('Scalar', bound=np.generic)


class NativeValue(BaseModel, frozen=True):
    dtype: str
    shape: tuple[int, ...]
    sha256: str


class TrialProof(BaseModel, frozen=True):
    fields: dict[str, NativeValue]
    due_edges: tuple[NativeValue, ...]
    due_sha256: tuple[str, ...]
    queue: NativeValue
    queue_slot_sha256: tuple[str, ...]


class BlockProof(BaseModel, frozen=True):
    begin: int
    rows: int
    trials: tuple[int, ...]
    units: dict[str, str]
    by_trial: dict[str, TrialProof]
    measured_checks: bool
    checks_all: bool
    artifact_sha256: str
    queue_artifact_sha256: str


class MemorySample(BaseModel, frozen=True):
    stage: str
    step: int
    elapsed_s: float
    resident_bytes: int
    process_peak_resident_bytes: int
    mlx_active_bytes: int
    mlx_cache_bytes: int
    mlx_peak_bytes: int
    traced_host_current_bytes: int
    traced_host_peak_bytes: int


@dataclass(frozen=True)
class Frame:
    begin: int
    rows: int
    fields: Mapping[str, HostArray]
    checks: NDArray[np.bool_] | None
    due_edges: tuple[tuple[NDArray[np.int32], ...], ...]
    due_sha256: tuple[tuple[str, ...], ...]


def value_signature(value: NDArray[Scalar]) -> NativeValue:
    contiguous = np.ascontiguousarray(value)
    return NativeValue(
        dtype=value.dtype.str,
        shape=value.shape,
        sha256=hashlib.sha256(contiguous.data).hexdigest(),
    )


def require_same_trial(before: BlockProof, after: BlockProof, trial: int) -> None:
    if (before.begin, before.rows, before.units) != (
        after.begin,
        after.rows,
        after.units,
    ):
        raise ValueError('Native block order, shape or phase units differ')
    if str(trial) not in before.by_trial or str(trial) not in after.by_trial:
        raise ValueError('Native trial identity is missing')
    if before.by_trial[str(trial)] != after.by_trial[str(trial)]:
        raise ValueError(
            'Actual native dtype, shape, bytes, due or physical queue differ'
        )
    if after.measured_checks and not after.checks_all:
        raise ValueError('Actual independent checks failed')


def proof_root(request: pytest.FixtureRequest) -> Path:
    value = request.config.getoption('--artifact-output')
    if not isinstance(value, str):
        raise ValueError('Pinned proof requires its fresh --artifact-output root')
    return Path(value)
