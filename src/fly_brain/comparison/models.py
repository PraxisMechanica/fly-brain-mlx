from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.identifiers import (
    FlyWireIds64,
    FlyWireNeuronId,
    TrialId,
    TrialIds16,
)

MetricValue = str | int | float | None


@dataclass(frozen=True)
class Spikes:
    trials: TrialIds16
    neuron_ids: FlyWireIds64
    time_s: NDArray[np.float64]


@dataclass(frozen=True)
class SpikeSteps:
    neurons: NDArray[np.int64]
    steps: NDArray[np.int64]


@dataclass(frozen=True)
class ParityMetrics:
    reference_spikes: int
    candidate_spikes: int
    active_jaccard: Fraction
    count_error: Fraction | None
    signed_count_ratio: Fraction | None
    neuron_count_error: Fraction | None
    rate_correlation: float | None
    counts_equal: bool
    timing_matches: int
    timing_f1: Fraction
    timing_precision: Fraction
    timing_recall: Fraction
    exact_step_f1: Fraction
    one_step_f1: Fraction
    mean_timing_error_ms: float | None
    median_timing_error_ms: float | None
    shared_rate_correlation: float | None
    common_rate_mae_hz: float | None
    common_rate_rmse_hz: float | None


@dataclass(frozen=True)
class MetricAcceptance:
    mlx: ParityMetrics
    torch: ParityMetrics
    checks: dict[str, bool]

    @property
    def accepted(self) -> bool:
        return all(self.checks.values())


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
    rates: dict[FlyWireNeuronId, float]
    active: set[FlyWireNeuronId]
    groups: dict[tuple[TrialId, FlyWireNeuronId], NDArray[np.float64]]
    spikes: int


class SpikeReader(Protocol):
    def __call__(self, path: Path, duration_s: float, /) -> Spikes: ...
