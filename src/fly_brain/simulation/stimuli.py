import hashlib

import numpy as np
from numpy.typing import NDArray

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


def trial_events(
    rates_hz: tuple[float, ...], uniforms: NDArray[np.float64]
) -> NDArray[np.uint8]:
    if (uniforms.dtype, uniforms.ndim) != (np.float64, 2):
        raise ValueError('Stimulus uniforms require a native float64 matrix')
    probabilities = np.asarray(rates_hz, dtype=np.float64) * 0.0001
    return (uniforms < probabilities).astype(np.uint8)


def generate(
    connectome: Connectome,
    experiment: Experiment,
    steps: int,
    trials: tuple[int, ...],
    seed: int = 20261004,
    *,
    prepared: tuple[NDArray[np.uint8], ...],
) -> Stimulus:
    if len(prepared) != len(trials):
        raise ValueError('Stimulus requires every requested trial')
    events = np.empty(
        (len(trials), steps, len(experiment.activated_ids)), dtype=np.uint8
    )
    for row, values in enumerate(prepared):
        if (values.shape, values.dtype) != (
            (steps, len(experiment.activated_ids)),
            np.uint8,
        ):
            raise ValueError('Prepared stimulus has the wrong native shape or dtype')
        events[row] = values
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
