from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from fly_brain.comparison.models import MetricAcceptance, ParityMetrics, SpikeSteps


class CaseScorer(Protocol):
    def __call__(
        self,
        reference: SpikeSteps,
        mlx: SpikeSteps,
        torch: SpikeSteps,
        duration_s: float,
        /,
    ) -> MetricAcceptance: ...


class CoordinateValidator(Protocol):
    def __call__(self, spikes: SpikeSteps, neurons: int, steps: int, /) -> None: ...


class ReferenceClockConverter(Protocol):
    def __call__(
        self, time_s: NDArray[np.float64], horizon: int, /
    ) -> NDArray[np.int64]: ...


class TrialMeasurer(Protocol):
    def __call__(
        self,
        trials: tuple[tuple[SpikeSteps, SpikeSteps], ...],
        support: NDArray[np.int64],
        duration_s: float,
        /,
    ) -> ParityMetrics: ...


class TimeBinCounter(Protocol):
    def __call__(
        self, spike_steps: NDArray[np.int64], horizon: int, /
    ) -> NDArray[np.int64]: ...
