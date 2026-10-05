import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import build
from fly_brain.qualification.adapters.causal_capture import CausalCapture
from fly_brain.qualification.adapters.observer_evidence import array_record
from fly_brain.qualification.adapters.paired_collect import collect
from fly_brain.qualification.adapters.paired_observer import PairedBlock
from fly_brain.qualification.adapters.pending_queues import verify as verify_pending
from fly_brain.qualification.adapters.replay_evidence import paired as verify_repeat
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
        summary = json.loads((output / 'causal.json').read_text())
        assert summary['steps'] == 101 and summary['contexts'] == {
            'budget': None,
            'spike': None,
        }
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
        pending = verify_pending(output, 101, len(case.connectome.sources))
        assert len(pending) == 18
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
    verify_repeat(*outputs)


def test_injected_first_budget_fault_retains_actual_inputs_and_reference_weights(
    precision: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = fixture()
    events = case.events[:1]
    stimulus = Stimulus(
        events,
        case.targets,
        (200.0,) * 3,
        (0,),
        0,
        0,
        hashlib.sha256(events.tobytes()).hexdigest(),
    )
    job = build(case.connectome, case.targets, (3,), events[0], tmp_path / 'build')
    execution = prepare(case.connectome, case.targets, (3,), precision)
    capture = CausalCapture()
    check = capture.check

    def inject_fault(block: PairedBlock) -> None:
        if block.reference.begin == 0:
            fields = dict(block.mlx.fields)
            fields['pre_v'] = fields['pre_v'].copy()
            fields['pre_v'][7, 0, 2] += 0.02
            block = replace(block, mlx=replace(block.mlx, fields=fields))
        check(block)

    monkeypatch.setattr(capture, 'check', inject_fault)
    monkeypatch.setattr(
        'fly_brain.qualification.adapters.paired_collect.CausalCapture', lambda: capture
    )
    output = tmp_path / 'collected'
    collect(job, execution, case.connectome, stimulus, output)
    summary = json.loads((output / 'causal.json').read_text())
    assert summary['first_budget_violation']['step'] == 7
    assert summary['first_spike_step'] is None and summary['contexts']['spike'] is None
    with np.load(output / 'budget-context.npz') as archive:
        for position, step in (('current', 7), ('previous', 6)):
            assert (
                archive[position + '_stimulus_bits'].tobytes()
                == events[0, step].tobytes()
            )
        assert archive['affected_neuron_ids'].tolist() == [2]
        edges = archive['neuron_2_actual_mlx_leaf_edges']
        occupied = archive['neuron_2_actual_mlx_leaf_occupied']
        weights = np.fromfile(
            output / 'reference-results' / job.files['weights'], dtype=np.float64
        )
        assert (
            archive['neuron_2_reference_native_weight_si'].tobytes()
            == weights[edges[occupied]].tobytes()
        )
        for name in archive.files:
            assert (
                array_record(archive[name])
                == summary['contexts']['budget']['arrays'][name]
            )
