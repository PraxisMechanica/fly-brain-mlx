from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.identifiers import FlyWireIds64

from .models import (
    ComparisonRequest,
    ComparisonResult,
    FlyWireSpikeSteps,
    MetricAcceptance,
    ParityMetrics,
    RowSpikeSteps,
)


class ComparisonUseCase(Protocol):
    def __call__(self, request: ComparisonRequest, /) -> ComparisonResult: ...


class ComparisonWriter(Protocol):
    def __call__(self, output: Path, result: ComparisonResult, /) -> None: ...


class ComparisonReport(Protocol):
    def __call__(
        self, request: ComparisonRequest, output: Path, /
    ) -> ComparisonResult: ...


class ComparisonCommand(Protocol):
    def __call__(self, request: ComparisonRequest, output: Path, /) -> int: ...


CaseScoring = Callable[
    [FlyWireSpikeSteps, FlyWireSpikeSteps, FlyWireSpikeSteps, float], MetricAcceptance
]
CoordinateValidation = Callable[[RowSpikeSteps, int, int], None]
ReferenceClockConversion = Callable[[NDArray[np.float64], int], NDArray[np.int64]]

TrialMeasurement = Callable[
    [tuple[tuple[FlyWireSpikeSteps, FlyWireSpikeSteps], ...], FlyWireIds64, float],
    ParityMetrics,
]
TimeBinCounting = Callable[[NDArray[np.int64], int], NDArray[np.int64]]
