from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

MetricValue = str | int | float | None


@dataclass(frozen=True)
class Spikes:
    trials: NDArray[np.int16]
    neuron_ids: NDArray[np.int64]
    time_s: NDArray[np.float64]


@dataclass(frozen=True)
class ComparisonRequest:
    first: Path
    second: Path
    duration_s: float
    trials: int
    tolerance_ms: float
    first_label: str
    second_label: str


@dataclass(frozen=True)
class ComparisonResult:
    summary: dict[str, MetricValue]
    rates: tuple[dict[str, MetricValue], ...]


@dataclass(frozen=True)
class Metrics:
    rates: dict[int, float]
    active: set[int]
    groups: dict[tuple[int, int], NDArray[np.float64]]
    spikes: int


class SpikeReader(Protocol):
    def __call__(self, path: Path, duration_s: float, /) -> Spikes: ...
