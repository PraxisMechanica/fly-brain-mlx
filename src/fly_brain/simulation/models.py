from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .identifiers import (
    EdgeRows32,
    FlyWireIds64,
    FlyWireNeuronId,
    NeuronRow,
    NeuronRows32,
    NeuronRows64,
    PaddedEdgeRows32,
    TrialId,
    TrialIds64,
)


@dataclass(frozen=True)
class NetworkCase:
    neurons: int
    sources: tuple[NeuronRow, ...] = ()
    destinations: tuple[NeuronRow, ...] = ()
    weights: tuple[float, ...] = ()
    targets: tuple[NeuronRow, ...] = ()
    silenced: tuple[NeuronRow, ...] = ()
    voltage: ArrayLike = -52
    synaptic: ArrayLike = 0
    last_spike: ArrayLike = -100000000


@dataclass(frozen=True)
class InputPin:
    completeness_sha256: str
    connectivity_sha256: str
    neurons: int
    edges: int
    scale_mv: float = 0.275


@dataclass(frozen=True)
class Connectome:
    neuron_ids: FlyWireIds64
    sources: NeuronRows32
    destinations: NeuronRows32
    counts: NDArray[np.int32]
    weights_mv: NDArray[np.float64]


@dataclass(frozen=True)
class DestinationGrouping:
    edge_ids: EdgeRows32
    inverse: NDArray[np.int32]
    offsets: NDArray[np.int64]


@dataclass(frozen=True)
class DestinationBucket:
    targets: NeuronRows32
    edge_ids: PaddedEdgeRows32
    counts: NDArray[np.float32]
    occupied: NDArray[np.bool_]


ExperimentName = Literal['sugar', 'p9', 'sugar-silenced', 'two-class', 'silent']


@dataclass(frozen=True)
class Experiment:
    name: ExperimentName
    code: int
    generator_code: int
    activated_ids: tuple[FlyWireNeuronId, ...]
    rates_hz: tuple[float, ...]
    silenced_ids: tuple[FlyWireNeuronId, ...] = ()


@dataclass(frozen=True)
class Stimulus:
    events: NDArray[np.uint8]
    targets: tuple[NeuronRow, ...]
    rates_hz: tuple[float, ...]
    trial_indices: tuple[TrialId, ...]
    seed: int
    generator_code: int
    sha256: str


@dataclass(frozen=True)
class SimulationRequest:
    project: Path
    output: Path
    experiment: ExperimentName
    duration_s: float
    trials: int
    seed: int


@dataclass(frozen=True)
class SpikeEvents:
    trials: TrialIds64
    neurons: NeuronRows64
    steps: NDArray[np.int64]


@dataclass(frozen=True)
class SimulationRun:
    spikes: SpikeEvents
    timings: dict[str, float]
    peak_device_bytes: int
    device_name: str


@dataclass(frozen=True)
class SimulationResult:
    spike_file: Path
    spikes: int
    active_neurons: int
    elapsed_s: float
