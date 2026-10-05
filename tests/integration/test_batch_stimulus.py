import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.batch_stimulus import load
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.models import InputPin
from fly_brain.simulation.stimuli import generate
from fly_brain.simulation.storage import persist_stimulus
from tests.unit.test_stimuli import connectome

pytestmark = pytest.mark.integration


@pytest.mark.parametrize('trials', ((0,), (0, 1, 2, 3)))
def test_saved_batch_input_preserves_native_bytes_and_trial_provenance(
    tmp_path: Path, trials: tuple[int, ...]
) -> None:
    experiment = EXPERIMENTS['sugar']
    pin = InputPin('csv', 'parquet', len(connectome().neuron_ids), 0)
    expected = generate(connectome(), experiment, 35, trials)
    directory = tmp_path / 'input'
    persist_stimulus(directory, experiment, pin, expected)
    actual = load(directory, experiment, pin)
    assert (actual.events.dtype, actual.events.shape, actual.events.tobytes()) == (
        expected.events.dtype,
        expected.events.shape,
        expected.events.tobytes(),
    )
    assert not actual.events.flags.writeable and actual.trial_indices == trials


@pytest.mark.parametrize(
    'fault',
    (
        'artifact_hash',
        'event_hash',
        'precision',
        'bits',
        'truncated',
        'trial_shape',
        'pin',
        'channels',
        'seed_type',
        'step_size',
        'version',
        'extra_array',
    ),
)
def test_saved_input_cannot_hide_corruption_or_silently_convert_native_evidence(
    tmp_path: Path, fault: str
) -> None:
    experiment = EXPERIMENTS['p9']
    pin = InputPin('csv', 'parquet', len(connectome().neuron_ids), 0)
    expected = generate(connectome(), experiment, 35, (0, 1, 2, 3))
    directory = tmp_path / 'input'
    persist_stimulus(directory, experiment, pin, expected)
    path = directory / 'stimulus.json'
    metadata = json.loads(path.read_text())
    if fault in ('precision', 'bits', 'truncated', 'extra_array'):
        events = expected.events.copy()
        if fault == 'precision':
            events = events.astype(np.float32)
        elif fault == 'bits':
            events[3, -1, 1] = 2
        elif fault == 'truncated':
            events = events[:, :-1]
        with (directory / 'stimulus.npz').open('wb') as output:
            if fault == 'extra_array':
                np.savez_compressed(
                    output, events=events, targets=np.asarray(expected.targets)
                )
            else:
                np.savez_compressed(output, events=events)
        metadata['artifact_sha256'] = hashlib.sha256(
            (directory / 'stimulus.npz').read_bytes()
        ).hexdigest()
    elif fault == 'artifact_hash':
        metadata['artifact_sha256'] = '0' * 64
    elif fault == 'event_hash':
        metadata['per_trial_event_sha256'][3] = '0' * 64
    elif fault == 'trial_shape':
        metadata['trial_indices'] = [0, 1, 2]
    elif fault == 'pin':
        metadata['input_sha256']['connectivity'] = 'wrong'
    elif fault == 'channels':
        metadata['activated_ids'].reverse()
    elif fault == 'seed_type':
        metadata['seed'] = True
    elif fault == 'step_size':
        metadata['dt_ms'] = 0.01
    else:
        metadata['format_version'] = 2
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError):
        load(directory, experiment, pin)
