from typing import cast

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.observations import HostArray


def evaluate(*arrays: mx.array) -> None:
    mx.eval(*arrays)  # pyright: ignore[reportUnknownMemberType]


def boolean_input(events: NDArray[np.bool_]) -> mx.array:
    return mx.array(events)  # pyright: ignore[reportArgumentType]


def as_host(value: mx.array) -> HostArray:
    return cast(HostArray, np.asarray(value))
