from dataclasses import dataclass

from numpy.typing import ArrayLike


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
