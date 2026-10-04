import hashlib
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from fly_brain.simulation.backend.runner import run
from fly_brain.simulation.models import Connectome, Stimulus

pytestmark = [pytest.mark.integration, pytest.mark.metal]


def test_production_collection_keeps_trial_identity_and_steps_across_blocks(
    precision: str, request: pytest.FixtureRequest
) -> None:
    c = Connectome(
        np.array([10, 20], dtype=np.int64),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    events = np.ones((2, 513, 2), dtype=np.uint8)
    events[0, :, 1] = 0
    stimulus = Stimulus(
        events,
        (0, 1),
        (10000.0, 10000.0),
        (2, 4),
        20261004,
        2,
        hashlib.sha256(events.tobytes()).hexdigest(),
    )
    result = run(c, stimulus, (), precision=precision)
    expected = np.array(
        [
            (trial, neuron, step)
            for trial, neurons in ((2, (0,)), (4, (0, 1)))
            for step in range(1, 513, 2)
            for neuron in neurons
        ],
        dtype=np.int64,
    )
    actual = np.column_stack(
        (result.spikes.trials, result.spikes.neurons, result.spikes.steps)
    )
    np.testing.assert_array_equal(actual, expected)
    path = cast(str | None, request.config.getoption('--artifact-output'))
    if path is not None:
        with (Path(path) / 'production-collection.npz').open('xb') as destination:
            np.savez_compressed(
                destination, events=events, actual=actual, expected=expected
            )
