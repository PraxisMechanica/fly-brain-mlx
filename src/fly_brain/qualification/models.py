from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.identifiers import TrialId
from fly_brain.simulation.models import ExperimentName

MappedArray = NDArray[np.int32] | NDArray[np.int64] | NDArray[np.float64]


@dataclass(frozen=True)
class InputAuditPreparation:
    arrays: dict[str, MappedArray]
    degree: NDArray[np.int64]
    duplicate: NDArray[np.bool_]
    checksums: dict[str, dict[str, str | list[int]]]


@dataclass(frozen=True)
class InputAuditArtifact:
    path: str
    sha256: str


@dataclass(frozen=True)
class ParityCase:
    experiment: ExperimentName
    steps: int
    trial: TrialId


@dataclass(frozen=True)
class QualificationRequest:
    project: Path
    output: Path


@dataclass(frozen=True)
class TestCounts:
    tests: int
    failures: int
    errors: int
    skipped: int


@dataclass(frozen=True)
class QualificationResult:
    command: tuple[str, ...]
    exit_code: int
    counts: TestCounts | None

    @property
    def accepted(self) -> bool:
        return (
            self.exit_code == 0
            and self.counts is not None
            and self.counts.tests > 0
            and self.counts.failures == 0
            and self.counts.errors == 0
            and self.counts.skipped == 0
        )


class TestRunner(Protocol):
    def __call__(self, request: QualificationRequest, /) -> QualificationResult: ...


class ResultWriter(Protocol):
    def __call__(
        self, request: QualificationRequest, result: QualificationResult, /
    ) -> None: ...
