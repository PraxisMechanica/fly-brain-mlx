from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .identifiers import NeuronRow, TrialId
from .models import (
    Connectome,
    DestinationBucket,
    DestinationGrouping,
    Experiment,
    ExperimentName,
    InputPin,
    SimulationRequest,
    SimulationResult,
    SimulationRun,
    Stimulus,
)


class ConnectomeReader(Protocol):
    def __call__(
        self, completeness: Path, connectivity: Path, pin: InputPin, /
    ) -> Connectome: ...


class ConnectomeReaderFactory(Protocol):
    def __call__(self, /) -> ConnectomeReader: ...


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


class StimulusWriter(Protocol):
    def __call__(
        self, output: Path, experiment: Experiment, pin: InputPin, stimulus: Stimulus, /
    ) -> Stimulus: ...


class SimulationExecutor(Protocol):
    def __call__(
        self,
        connectome: Connectome,
        stimulus: Stimulus,
        silenced: tuple[NeuronRow, ...],
        /,
    ) -> SimulationRun: ...


class SimulationWriter(Protocol):
    def __call__(
        self,
        request: SimulationRequest,
        connectome: Connectome,
        pin: InputPin,
        stimulus: Stimulus,
        run: SimulationRun,
        timings: dict[str, float],
        started: float,
        /,
    ) -> SimulationResult: ...


class Clock(Protocol):
    def __call__(self, /) -> float: ...


class UniformDraws(Protocol):
    def __call__(
        self, seed: tuple[int, int, TrialId], size: tuple[int, int], /
    ) -> NDArray[np.float64]: ...


class StimulusGenerator(Protocol):
    def __call__(
        self,
        connectome: Connectome,
        experiment: Experiment,
        steps: int,
        trials: tuple[TrialId, ...],
        seed: int,
        /,
    ) -> Stimulus: ...


class SimulationUseCase(Protocol):
    def __call__(self, request: SimulationRequest, /) -> SimulationResult: ...


class SimulationCommand(Protocol):
    def __call__(self, request: SimulationRequest, /) -> int: ...


class ExperimentReader(Protocol):
    def __call__(self, name: ExperimentName, /) -> Experiment: ...


class StimulusRecorder(Protocol):
    def __call__(
        self,
        output: Path,
        connectome: Connectome,
        experiment: Experiment,
        pin: InputPin,
        stimulus: Stimulus,
        /,
    ) -> tuple[Stimulus, tuple[NeuronRow, ...]]: ...
