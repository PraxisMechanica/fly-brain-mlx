import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.replay_evidence import cpu as verify_repeat
from fly_brain.qualification.adapters.torch_collect import collect
from fly_brain.qualification.adapters.torch_observer import observe
from fly_brain.qualification.adapters.torch_setup import prepare
from fly_brain.simulation.models import Stimulus
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference]


@pytest.mark.parametrize('empty', (False, True))
def test_cpu_collection_preserves_all_native_state_hashes_and_trial_spikes(
    tmp_path: Path, empty: bool
) -> None:
    case = fixture(empty)
    stimulus = Stimulus(
        case.events,
        case.targets,
        (200.0,) * len(case.targets),
        (0, 1, 2, 3),
        0,
        0,
        hashlib.sha256(case.events.tobytes()).hexdigest(),
    )
    model = prepare(case.connectome, case.targets, (3,), 4)
    expected = list(observe(model, case.events, case.targets))
    outputs = (tmp_path / 'first', tmp_path / 'repeat')
    for output in outputs:
        collect(model, stimulus, output)
        rows = [
            json.loads(line)
            for line in (output / 'native-digests.jsonl').read_text().splitlines()
        ]
        assert [row['step'] for row in rows] == list(range(-1, 101))
        assert [row['native_sha256'] for row in rows] == [
            list(row.native_sha256) for row in expected
        ]
        with np.load(output / 'native.npz') as archive:
            for name, value in expected[-1].fields.items():
                actual = archive[name]
                assert (actual.dtype, actual.shape, actual.tobytes()) == (
                    value.dtype,
                    value.shape,
                    value.tobytes(),
                )
            observed = list(
                zip(
                    archive['spike_trials'],
                    archive['spike_neurons'],
                    archive['spike_steps'],
                    strict=True,
                )
            )
            raster = [
                (trial, neuron, row.step)
                for row in expected[1:]
                for trial, neuron in zip(*np.nonzero(row.fields['spikes']), strict=True)
            ]
            assert observed == raster
    assert (outputs[0] / 'native-digests.jsonl').read_bytes() == (
        outputs[1] / 'native-digests.jsonl'
    ).read_bytes()
    with pytest.raises(FileExistsError):
        collect(model, stimulus, outputs[0])
    verify_repeat(*outputs)
