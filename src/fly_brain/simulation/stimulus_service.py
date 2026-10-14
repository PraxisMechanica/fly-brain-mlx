from pathlib import Path

from .experiments import EXPERIMENTS
from .identifiers import NeuronRow, TrialId
from .models import Connectome, Experiment, ExperimentName, InputPin, Stimulus
from .ports import StimulusWriter, UniformDraws
from .stimuli import generate, neuron_indices, trial_events


def schedule(
    connectome: Connectome,
    experiment: Experiment,
    steps: int,
    trials: tuple[TrialId, ...],
    seed: int,
    *,
    draw_uniforms: UniformDraws,
) -> Stimulus:
    prepared = tuple(
        trial_events(
            experiment.rates_hz,
            draw_uniforms(
                (seed, experiment.generator_code, trial),
                (steps, len(experiment.rates_hz)),
            ),
        )
        for trial in trials
    )
    return generate(connectome, experiment, steps, trials, seed, prepared=prepared)


def read_experiment(name: ExperimentName) -> Experiment:
    return EXPERIMENTS[name]


def record_stimulus(
    output: Path,
    connectome: Connectome,
    experiment: Experiment,
    pin: InputPin,
    stimulus: Stimulus,
    *,
    persist: StimulusWriter,
) -> tuple[Stimulus, tuple[NeuronRow, ...]]:
    stored = persist(output, experiment, pin, stimulus)
    silenced = neuron_indices(connectome, experiment.silenced_ids)
    return stored, silenced
