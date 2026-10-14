import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.batch_stimulus import load
from fly_brain.qualification.models import ParityCase
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.identifiers import TrialId
from fly_brain.simulation.models import Connectome, Experiment, InputPin, Stimulus
from tests.support.seeded_inputs import generate
from tests.unit.test_stimuli import connectome
from tools.qualify_matrix import canonical_inputs

pytestmark = pytest.mark.integration


def test_matrix_inputs_preserve_every_case_prefix_silencing_and_independent_trial(
    tmp_path: Path,
) -> None:
    network = connectome()
    pin = InputPin('csv', 'parquet', len(network.neuron_ids), 0)
    output = tmp_path / 'canonical'
    hashes = canonical_inputs(network, pin, output, generate)
    assert len(hashes) == 52
    assert hashes[ParityCase('p9', 100000, TrialId(4))] == (
        '0606dc7a953332dbf2d70ef70a2409270290735fb8097d41b733e6e6282c8fc3'
    )
    assert hashes[ParityCase('p9', 1000, TrialId(4))] == (
        '7e30ea0434fe5cdb4101fa93d36e7eca93ec70ee18da8005917b736f81dd0466'
    )
    longest = load(output / 'sugar-100000-4', EXPERIMENTS['sugar'], pin)
    prefix = load(output / 'sugar-silenced-1000-4', EXPERIMENTS['sugar-silenced'], pin)
    assert np.array_equal(longest.events[:, :1000], prefix.events)
    assert not prefix.events.flags.writeable
    assert json.loads((output / 'preflight.json').read_text())['accepted'] is True


@pytest.mark.parametrize('fault', ('duration', 'batch'))
def test_matrix_preflight_rejects_a_self_consistent_wrong_schedule(
    tmp_path: Path, fault: str
) -> None:
    network = connectome()
    pin = InputPin('csv', 'parquet', len(network.neuron_ids), 0)
    output = tmp_path / 'invalid'

    def incorrect(
        connectome: Connectome,
        experiment: Experiment,
        steps: int,
        trials: tuple[TrialId, ...],
        seed: int,
    ) -> Stimulus:
        result = generate(connectome, experiment, steps, trials, seed)
        if (fault == 'duration' and steps == 1000) or (
            fault == 'batch' and len(trials) > 1
        ):
            events = result.events.copy()
            events.flat[0] ^= 1
            events.setflags(write=False)
            return replace(
                result,
                events=events,
                sha256=hashlib.sha256(events.tobytes()).hexdigest(),
            )
        return result

    with pytest.raises(ValueError, match='prefix|PCG64'):
        canonical_inputs(network, pin, output, incorrect)
    assert not (output / 'preflight.json').exists()
