import hashlib

import numpy as np

from .models import Connectome, Experiment, Stimulus


def neuron_indices(connectome: Connectome, ids: tuple[int, ...]) -> tuple[int, ...]:
    lookup = {
        int(identifier): index for index, identifier in enumerate(connectome.neuron_ids)
    }
    missing = set(ids) - lookup.keys()
    if missing:
        raise ValueError(
            f'Experiment neurons absent from pinned data: {sorted(missing)}'
        )
    return tuple(lookup[identifier] for identifier in ids)


def generate(
    connectome: Connectome,
    experiment: Experiment,
    steps: int,
    trials: tuple[int, ...],
    seed: int = 20261004,
) -> Stimulus:
    events = np.empty(
        (len(trials), steps, len(experiment.activated_ids)), dtype=np.uint8
    )
    probabilities = np.asarray(experiment.rates_hz, dtype=np.float64) * 0.0001
    for row, trial in enumerate(trials):
        generator = np.random.Generator(
            np.random.PCG64(
                np.random.SeedSequence([seed, experiment.generator_code, trial])
            )
        )
        events[row] = generator.random((steps, probabilities.size)) < probabilities
    events.setflags(write=False)
    return Stimulus(
        events,
        neuron_indices(connectome, experiment.activated_ids),
        experiment.rates_hz,
        trials,
        seed,
        experiment.generator_code,
        hashlib.sha256(events.tobytes()).hexdigest(),
    )
