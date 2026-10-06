from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .observations import (
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationInitialState,
    ObservationOperands,
    PhysicalQueueObservation,
)


class ObservationSession(Protocol):
    @property
    def configuration(self) -> ObservationConfiguration: ...

    def advance(self, events: NDArray[np.bool_], /) -> NativeObservation: ...

    def compare(self, operands: ObservationOperands, /) -> NativeComparison: ...

    def physical_queue(self) -> PhysicalQueueObservation: ...


class ObservationSessionFactory(Protocol):
    def __call__(
        self, trial_indices: tuple[int, ...], initial: ObservationInitialState | None, /
    ) -> ObservationSession: ...
