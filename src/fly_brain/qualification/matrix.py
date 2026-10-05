from fly_brain.simulation.models import ExperimentName

from .models import ParityCase


def required_cases() -> tuple[ParityCase, ...]:
    long = (1000, 10000, 100000)
    configurations: tuple[tuple[ExperimentName, tuple[int, ...], int], ...] = (
        ('sugar', long, 5),
        ('p9', long, 5),
        ('sugar-silenced', long[:2], 5),
        ('two-class', long[:2], 5),
        ('silent', long[:2], 1),
    )
    return tuple(
        ParityCase(experiment, steps, trial)
        for experiment, horizons, trials in configurations
        for steps in horizons
        for trial in range(trials)
    )
