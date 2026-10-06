from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .fan_in import FanInCases


class UniformDraws(Protocol):
    def __call__(
        self, seed: tuple[int, int, int, int, int], size: int, /
    ) -> NDArray[np.float64]: ...


class PermutationDraws(Protocol):
    def __call__(
        self, seed: tuple[int, int, int], size: int, /
    ) -> NDArray[np.int64]: ...


class FanInCaseBuilder(Protocol):
    def __call__(
        self,
        target: int,
        sources: NDArray[np.int32],
        counts: NDArray[np.int32],
        weights: NDArray[np.float64],
        /,
    ) -> FanInCases: ...
