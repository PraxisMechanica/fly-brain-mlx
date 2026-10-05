import hashlib
from collections.abc import Mapping

import numpy as np

from fly_brain.simulation.models import Stimulus


def require_stimuli(
    canonical: Stimulus, batch: Stimulus, singletons: Mapping[int, Stimulus]
) -> tuple[str, ...]:
    if set(singletons) != {0, 1, 2, 3}:
        raise ValueError(
            'Batch identity requires independent trials zero through three'
        )
    if canonical.trial_indices != (0, 1, 2, 3) or batch.trial_indices != (0, 1, 2, 3):
        raise ValueError('Batch identity requires prescribed trial order')
    for actual in (canonical, batch, *singletons.values()):
        if (
            actual.events.ndim != 3
            or actual.events.dtype != np.uint8
            or actual.events.shape[0] != len(actual.trial_indices)
            or actual.events.shape[1] < 1
            or actual.events.shape[2] != len(actual.targets)
            or len(actual.rates_hz) != len(actual.targets)
            or np.any(actual.events > 1)
            or hashlib.sha256(actual.events.tobytes()).hexdigest() != actual.sha256
        ):
            raise ValueError(
                'Stimulus identity requires complete native bits and hashes'
            )
        if (
            actual.targets != canonical.targets
            or actual.rates_hz != canonical.rates_hz
            or actual.seed != canonical.seed
            or actual.generator_code != canonical.generator_code
        ):
            raise ValueError(
                'Stimulus identity requires canonical channels and generator'
            )
    if (batch.events.shape, batch.events.tobytes()) != (
        canonical.events.shape,
        canonical.events.tobytes(),
    ):
        raise ValueError('Batch events differ from canonical generation')
    hashes: list[str] = []
    for trial in range(4):
        actual = singletons[trial]
        expected = canonical.events[trial : trial + 1]
        if actual.trial_indices != (trial,) or (
            actual.events.shape,
            actual.events.tobytes(),
        ) != (expected.shape, expected.tobytes()):
            raise ValueError(f'Singleton stimulus differs from actual trial {trial}')
        hashes.append(actual.sha256)
    return tuple(hashes)
