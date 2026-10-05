import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import build
from fly_brain.qualification.adapters.observer_evidence import array_record
from fly_brain.qualification.adapters.paired_collect import collect
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.models import Stimulus
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


@pytest.mark.parametrize('empty', [False, True])
def test_live_collection_retains_complete_native_and_physical_replay(
    precision: str, tmp_path: Path, empty: bool
) -> None:
    case = fixture(empty)
    events = case.events[:1]
    stimulus = Stimulus(
        events,
        case.targets,
        (200.0,) * len(case.targets),
        (0,),
        0,
        0,
        hashlib.sha256(events.tobytes()).hexdigest(),
    )
    job = build(case.connectome, case.targets, (3,), events[0], tmp_path / 'build')
    execution = prepare(case.connectome, case.targets, (3,), precision)
    outputs = (tmp_path / 'first', tmp_path / 'repeat')
    for output in outputs:
        capture = collect(job, execution, case.connectome, stimulus, output)
        assert capture.audit.step == 101
        assert capture.spike is None and capture.budget is None
        phases = [
            json.loads(line)
            for line in (output / 'phase-digests.jsonl').read_text().splitlines()
        ]
        assert [(row['begin'], row['rows']) for row in phases] == [
            (0, 32),
            (32, 32),
            (64, 32),
            (96, 5),
        ]
        physical = [
            json.loads(line)
            for line in (output / 'physical-digests.jsonl').read_text().splitlines()
        ]
        assert [row['step'] for row in physical] == list(range(102))
        assert all(len(row['sha256']) == 64 for row in physical)
        metadata = json.loads((output / 'reference-final-physical.json').read_text())
        assert metadata['step'] == metadata['clock_step'] == 101
        with np.load(output / 'reference-final-physical.npz') as queues:
            assert array_record(queues['reference_spikes']) == metadata['spikes']
            assert (
                array_record(queues['reference_source_spikes'])
                == metadata['source_spikes']
            )
            for index, path in enumerate(metadata['pathways']):
                prefix = f'reference_pathway_{index}'
                assert array_record(queues[prefix + '_delivered']) == path['delivered']
                for thread, queue in enumerate(path['queues']):
                    name = f'{prefix}_queue_{thread}'
                    assert queues[name + '_offset'].item() == queue['offset']
                    for slot, descriptor in enumerate(queue['slots']):
                        assert array_record(queues[f'{name}_slot_{slot}']) == descriptor
        with (
            np.load(output / 'reference-native.npz') as reference,
            np.load(output / 'mlx-native.npz') as mlx,
        ):
            assert reference['v'].dtype == np.float64
            assert mlx['end_v'].dtype == np.float32
            assert mlx['queue'].dtype == np.bool_
            assert mlx['queue'].shape == (19, 1, len(case.connectome.sources))
            assert reference['clock_step'].tolist() == [101]
            assert reference['spike_i'].tolist() == mlx['spike_neurons'].tolist()
            assert np.array_equal(reference['spike_t'], mlx['spike_steps'] * 0.0001)
    for filename in (
        'phase-digests.jsonl',
        'physical-digests.jsonl',
        'reference-final-physical.json',
    ):
        assert (outputs[0] / filename).read_bytes() == (
            outputs[1] / filename
        ).read_bytes()
    for filename in (
        'reference-native.npz',
        'mlx-native.npz',
        'reference-final-physical.npz',
    ):
        with (
            np.load(outputs[0] / filename) as first,
            np.load(outputs[1] / filename) as repeat,
        ):
            assert first.files == repeat.files
            for name in first.files:
                a, b = first[name], repeat[name]
                assert (a.dtype, a.shape, a.tobytes()) == (
                    b.dtype,
                    b.shape,
                    b.tobytes(),
                ), name
    with pytest.raises(FileExistsError):
        collect(job, execution, case.connectome, stimulus, outputs[0])
