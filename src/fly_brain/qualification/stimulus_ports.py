from pathlib import Path
from typing import Protocol

from fly_brain.simulation.identifiers import NeuronRow, TrialId
from fly_brain.simulation.models import (
    Connectome,
    Experiment,
    ExperimentName,
    InputPin,
    Stimulus,
)

from .models import ParityCase


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


class CaseStimulusPreparation(Protocol):
    def __call__(
        self, connectome: Connectome, pin: InputPin, case: ParityCase, output: Path, /
    ) -> tuple[Stimulus, tuple[NeuronRow, ...]]: ...
