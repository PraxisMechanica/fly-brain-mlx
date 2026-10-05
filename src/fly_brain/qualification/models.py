from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from fly_brain.simulation.models import ExperimentName


@dataclass(frozen=True)
class ParityCase:
    experiment: ExperimentName
    steps: int
    trial: int


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
