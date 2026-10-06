from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.models import Connectome, InputPin
from fly_brain.simulation.observations import (
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationInitialState,
    ObservationOperands,
    PhysicalQueueObservation,
    ReductionEvidence,
)

from .models import ParityCase, QualificationRequest, QualificationResult


class ReductionReader(Protocol):
    def __call__(self, neurons: tuple[int, ...], /) -> ReductionEvidence: ...


class PinnedInputs(Protocol):
    def __call__(self, project: Path, /) -> tuple[Connectome, InputPin]: ...


class ProjectProbe(Protocol):
    def __call__(self, project: Path, output: Path, /) -> dict[str, object]: ...


class OutputProbe(Protocol):
    def __call__(self, output: Path, /) -> dict[str, object]: ...


class InputProbe(Protocol):
    def __call__(
        self, connectome: Connectome, pin: InputPin, output: Path, /
    ) -> dict[str, object]: ...


class ParityProbe(Protocol):
    def __call__(
        self, connectome: Connectome, pin: InputPin, case: ParityCase, output: Path, /
    ) -> dict[str, object]: ...


class QualificationUseCase(Protocol):
    def __call__(self, request: QualificationRequest, /) -> QualificationResult: ...


class DiagnosticUseCase(Protocol):
    def __call__(self, request: QualificationRequest, /) -> dict[str, object]: ...


class ParityUseCase(Protocol):
    def __call__(
        self, project: Path, output: Path, case: ParityCase, /
    ) -> dict[str, object]: ...


class QualificationCommand(Protocol):
    def __call__(self, request: QualificationRequest, /) -> int: ...


class DiagnosticCommand(Protocol):
    def __call__(self, request: QualificationRequest, /) -> int: ...


class ParityCommand(Protocol):
    def __call__(self, project: Path, output: Path, case: ParityCase, /) -> int: ...


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


class ObservationAssembly(Protocol):
    def __call__(
        self,
        connectome: Connectome,
        targets: tuple[int, ...],
        silenced: tuple[int, ...],
        precision: str,
        /,
    ) -> tuple[ObservationSessionFactory, ReductionReader]: ...
