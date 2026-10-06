from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

import numpy as np
from numpy.typing import NDArray

HostArray = NDArray[np.float32 | np.float64 | np.int32 | np.int64 | np.bool_]
Scalar = TypeVar('Scalar', bound=np.generic)
COMPENSATED_ORDER = 'Actual padded leaf order; adjacent-pair compensated integer-count tree; four high/low scale products; 16-leaf compensated final tree.'
EXACT_ORDER = 'Actual padded leaf order; leaf-axis float32 exact integer-count sum; four high/low scale products; 16-leaf compensated final tree.'


def _immutable(values: NDArray[Scalar]) -> NDArray[Scalar]:
    return np.frombuffer(values.tobytes(order='C'), dtype=values.dtype).reshape(
        values.shape
    )


@dataclass(frozen=True)
class ReductionRow:
    neuron: int
    edges: NDArray[np.int32]
    counts: NDArray[np.float32]
    occupied: NDArray[np.bool_]

    def __post_init__(self) -> None:
        if (
            self.edges.dtype != np.int32
            or self.counts.dtype != np.float32
            or self.occupied.dtype != np.bool_
            or self.edges.ndim != 1
            or self.edges.shape != self.counts.shape
            or self.edges.shape != self.occupied.shape
        ):
            raise ValueError(
                'Reduction rows require equal native one-dimensional fields'
            )
        object.__setattr__(self, 'edges', _immutable(self.edges))
        object.__setattr__(self, 'counts', _immutable(self.counts))
        object.__setattr__(self, 'occupied', _immutable(self.occupied))


@dataclass(frozen=True)
class ReductionEvidence:
    rows: tuple[ReductionRow, ...]
    order: str


ReductionReader = Callable[[tuple[int, ...]], ReductionEvidence]
