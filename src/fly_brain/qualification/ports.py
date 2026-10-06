from typing import Protocol

from fly_brain.simulation.observations import ReductionEvidence


class ReductionReader(Protocol):
    def __call__(self, neurons: tuple[int, ...], /) -> ReductionEvidence: ...
