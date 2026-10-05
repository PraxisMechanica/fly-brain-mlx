import hashlib
from dataclasses import replace

import numpy as np
import pytest

from fly_brain.qualification.batch_identity import require_stimuli
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.models import ExperimentName
from fly_brain.simulation.stimuli import generate
from tests.unit.test_stimuli import connectome

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('name', ('sugar', 'p9', 'silent'))
def test_batch_identity_binds_every_native_trial_to_canonical_generation(
    name: ExperimentName,
) -> None:
    expected = generate(connectome(), EXPERIMENTS[name], 10000, (0, 1, 2, 3))
    batch = generate(connectome(), EXPERIMENTS[name], 10000, (0, 1, 2, 3))
    singles = {
        trial: generate(connectome(), EXPERIMENTS[name], 10000, (trial,))
        for trial in range(4)
    }
    assert require_stimuli(expected, batch, singles) == tuple(
        singles[trial].sha256 for trial in range(4)
    )
    singles[0], singles[1] = singles[1], singles[0]
    with pytest.raises(ValueError, match='actual trial'):
        require_stimuli(expected, batch, singles)


@pytest.mark.parametrize(
    'fault',
    (
        'missing',
        'order',
        'seed',
        'generator',
        'channels',
        'rates',
        'hash',
        'events',
        'shape',
        'cast',
        'bits',
    ),
)
def test_input_metadata_or_event_corruption_cannot_grant_batch_identity(
    fault: str,
) -> None:
    expected = generate(connectome(), EXPERIMENTS['p9'], 100, (0, 1, 2, 3))
    batch = expected
    singles = {
        trial: generate(connectome(), EXPERIMENTS['p9'], 100, (trial,))
        for trial in range(4)
    }
    if fault == 'missing':
        del singles[3]
    elif fault == 'order':
        batch = replace(batch, trial_indices=(1, 0, 2, 3))
    elif fault == 'seed':
        batch = replace(batch, seed=0)
    elif fault == 'generator':
        batch = replace(batch, generator_code=0)
    elif fault == 'channels':
        batch = replace(batch, targets=tuple(reversed(batch.targets)))
    elif fault == 'rates':
        batch = replace(batch, rates_hz=(200.0, 200.0))
    elif fault == 'hash':
        batch = replace(batch, sha256='0' * 64)
    else:
        events = batch.events.copy()
        if fault == 'events':
            events[3, -1, 1] ^= 1
        elif fault == 'shape':
            events = events[:, :-1]
        elif fault == 'cast':
            events = events.astype(np.bool_)
        else:
            events[3, -1, 1] = 2
        batch = replace(
            batch, events=events, sha256=hashlib.sha256(events.tobytes()).hexdigest()
        )
    with pytest.raises(ValueError):
        require_stimuli(expected, batch, singles)
