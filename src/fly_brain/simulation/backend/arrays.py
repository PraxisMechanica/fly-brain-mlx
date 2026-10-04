from typing import cast

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

HostArray = NDArray[np.float32 | np.float64 | np.int32 | np.int64 | np.bool_]


def evaluate(*arrays: mx.array) -> None:
    mx.eval(*arrays)  # pyright: ignore[reportUnknownMemberType]


def boolean_input(events: NDArray[np.bool_]) -> mx.array:
    return mx.array(events)  # pyright: ignore[reportArgumentType]


def as_host(value: mx.array) -> HostArray:
    return cast(HostArray, np.asarray(value))
