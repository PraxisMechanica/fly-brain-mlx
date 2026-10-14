from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.identifiers import NeuronRow, TrialId
from fly_brain.simulation.models import (
    Connectome,
    DestinationBucket,
    DestinationGrouping,
    InputPin,
)
from fly_brain.simulation.observations import (
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationInitialState,
    ObservationOperands,
    PhysicalQueueObservation,
    ReductionEvidence,
)

from .models import (
    InputAuditArtifact,
    MappedArray,
    ParityCase,
    QualificationRequest,
    QualificationResult,
)


class InputAuditFiles(Protocol):
    def create_output(self, output: Path, /) -> None: ...

    def write_arrays(
        self, output: Path, arrays: Mapping[str, MappedArray], /
    ) -> Path: ...

    def read_artifact_identity(self, artifact: Path, /) -> InputAuditArtifact: ...

    def write_report(self, output: Path, report: dict[str, object], /) -> None: ...


class ReductionReader(Protocol):
    def __call__(self, neurons: tuple[NeuronRow, ...], /) -> ReductionEvidence: ...


class ConnectomeSilencer(Protocol):
    def __call__(
        self, connectome: Connectome, silenced: tuple[NeuronRow, ...], /
    ) -> Connectome: ...


class AbsoluteCountReader(Protocol):
    def __call__(self, connectome: Connectome, /) -> NDArray[np.int64]: ...


class DestinationGroupingReader(Protocol):
    def __call__(self, connectome: Connectome, /) -> DestinationGrouping: ...


class DestinationBucketsReader(Protocol):
    def __call__(self, connectome: Connectome, /) -> tuple[DestinationBucket, ...]: ...


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
        self,
        trial_indices: tuple[TrialId, ...],
        initial: ObservationInitialState | None,
        /,
    ) -> ObservationSession: ...


class ObservationAssembly(Protocol):
    def __call__(
        self,
        connectome: Connectome,
        targets: tuple[NeuronRow, ...],
        silenced: tuple[NeuronRow, ...],
        precision: str,
        /,
    ) -> tuple[ObservationSessionFactory, ReductionReader]: ...
