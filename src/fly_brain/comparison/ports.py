from collections.abc import Callable
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .models import (
    ComparisonRequest,
    ComparisonResult,
    MetricAcceptance,
    ParityMetrics,
    SpikeSteps,
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


CaseScoring = Callable[[SpikeSteps, SpikeSteps, SpikeSteps, float], MetricAcceptance]
CoordinateValidation = Callable[[SpikeSteps, int, int], None]
ReferenceClockConversion = Callable[[NDArray[np.float64], int], NDArray[np.int64]]

TrialMeasurement = Callable[
    [tuple[tuple[SpikeSteps, SpikeSteps], ...], NDArray[np.int64], float], ParityMetrics
]
TimeBinCounting = Callable[[NDArray[np.int64], int], NDArray[np.int64]]
