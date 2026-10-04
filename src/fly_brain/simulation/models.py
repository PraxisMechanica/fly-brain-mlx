from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray


@dataclass(frozen=True)
class NetworkCase:
    neurons: int
    sources: tuple[int, ...] = ()
    destinations: tuple[int, ...] = ()
    weights: tuple[float, ...] = ()
    targets: tuple[int, ...] = ()
    silenced: tuple[int, ...] = ()
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
    neuron_ids: NDArray[np.int64]
    sources: NDArray[np.int32]
    destinations: NDArray[np.int32]
    counts: NDArray[np.int32]
    weights_mv: NDArray[np.float64]


@dataclass(frozen=True)
class DestinationGrouping:
    edge_ids: NDArray[np.int32]
    inverse: NDArray[np.int32]
    offsets: NDArray[np.int64]


@dataclass(frozen=True)
class DestinationBucket:
    targets: NDArray[np.int32]
    edge_ids: NDArray[np.int32]
    counts: NDArray[np.float32]
    occupied: NDArray[np.bool_]
