from .models import Connectome, Experiment, Stimulus
from .ports import UniformDraws
from .stimuli import generate, trial_events


def schedule(
    connectome: Connectome,
    experiment: Experiment,
    steps: int,
    trials: tuple[int, ...],
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
