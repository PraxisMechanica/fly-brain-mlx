from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from fly_brain.comparison.models import (
    FlyWireSpikeSteps,
    MetricAcceptance,
    ParityMetrics,
    RowSpikeSteps,
)
from fly_brain.simulation.identifiers import FlyWireIds64


class CaseScorer(Protocol):
    def __call__(
        self,
        reference: FlyWireSpikeSteps,
        mlx: FlyWireSpikeSteps,
        torch: FlyWireSpikeSteps,
        duration_s: float,
        /,
    ) -> MetricAcceptance: ...


class CoordinateValidator(Protocol):
    def __call__(self, spikes: RowSpikeSteps, neurons: int, steps: int, /) -> None: ...


class ReferenceClockConverter(Protocol):
    def __call__(
        self, time_s: NDArray[np.float64], horizon: int, /
    ) -> NDArray[np.int64]: ...


class TrialMeasurer(Protocol):
    def __call__(
        self,
        trials: tuple[tuple[FlyWireSpikeSteps, FlyWireSpikeSteps], ...],
        support: FlyWireIds64,
        duration_s: float,
        /,
    ) -> ParityMetrics: ...


class TimeBinCounter(Protocol):
    def __call__(
        self, spike_steps: NDArray[np.int64], horizon: int, /
    ) -> NDArray[np.int64]: ...
