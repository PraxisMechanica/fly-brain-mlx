from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .models import (
    Connectome,
    Experiment,
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


class PinnedInputs(Protocol):
    def __call__(self, project: Path, /) -> tuple[Connectome, InputPin]: ...


class StimulusWriter(Protocol):
    def __call__(
        self, output: Path, experiment: Experiment, pin: InputPin, stimulus: Stimulus, /
    ) -> Stimulus: ...


class SimulationExecutor(Protocol):
    def __call__(
        self, connectome: Connectome, stimulus: Stimulus, silenced: tuple[int, ...], /
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
        self, seed: tuple[int, int, int], size: tuple[int, int], /
    ) -> NDArray[np.float64]: ...


class StimulusGenerator(Protocol):
    def __call__(
        self,
        connectome: Connectome,
        experiment: Experiment,
        steps: int,
        trials: tuple[int, ...],
        seed: int,
        /,
    ) -> Stimulus: ...


class SimulationUseCase(Protocol):
    def __call__(self, request: SimulationRequest, /) -> SimulationResult: ...


class SimulationCommand(Protocol):
    def __call__(self, request: SimulationRequest, /) -> int: ...
