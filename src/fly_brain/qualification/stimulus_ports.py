from typing import Protocol

from fly_brain.simulation.identifiers import TrialId
from fly_brain.simulation.models import Connectome, Experiment, Stimulus


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
