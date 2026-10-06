import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest
from pydantic import ValidationError

from fly_brain.comparison.storage import read_spikes
from fly_brain.simulation.models import (
    Connectome,
    Experiment,
    InputPin,
    SimulationRequest,
    SimulationRun,
    SpikeEvents,
)
from fly_brain.simulation.schemas import SimulationOptions
from fly_brain.simulation.stimuli import generate
from fly_brain.simulation.storage import persist_stimulus, write_run

pytestmark = pytest.mark.integration


def network() -> Connectome:
    return Connectome(
        np.array([10, 20], dtype=np.int64),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )


def test_persisted_schedule_reloads_exact_bytes_and_trial_provenance(
    tmp_path: Path,
) -> None:
    c = network()
    experiment = Experiment('p9', 1, 1, (20,), (100.0,))
    stimulus = generate(c, experiment, 1000, (2, 4))
    output = tmp_path / 'run'
    restored = persist_stimulus(
        output, experiment, InputPin('csv', 'parquet', 2, 0), stimulus
    )
    np.testing.assert_array_equal(restored.events, stimulus.events)
    assert restored.sha256 == stimulus.sha256 and not restored.events.flags.writeable
    metadata = json.loads((output / 'stimulus.json').read_text())
    assert metadata['seed_tuples'] == [[20261004, 1, 2], [20261004, 1, 4]]
    assert metadata['per_trial_event_sha256'] == [
        hashlib.sha256(row.tobytes()).hexdigest() for row in stimulus.events
    ]
    with pytest.raises(FileExistsError):
        persist_stimulus(output, experiment, InputPin('csv', 'parquet', 2, 0), stimulus)


@pytest.mark.parametrize('count', [0, 2])
def test_spike_export_preserves_original_types_and_is_readable_when_empty(
    tmp_path: Path, count: int
) -> None:
    c = network()
    experiment = Experiment('p9', 1, 1, (20,), (100.0,))
    stimulus = generate(c, experiment, 1000, (0,))
    output = tmp_path / 'run'
    pin = InputPin('csv', 'parquet', 2, 0)
    persist_stimulus(output, experiment, pin, stimulus)
    request = SimulationRequest(tmp_path, output, 'p9', 0.1, 1, 20261004)
    events = SpikeEvents(
        np.zeros(count, dtype=np.int64),
        np.ones(count, dtype=np.int64),
        np.arange(count, dtype=np.int64) * 2 + 1,
    )
    result = write_run(
        request,
        c,
        pin,
        stimulus,
        SimulationRun(events, {}, 0, 'test'),
        {},
        3.0,
        iter((10.0, 12.0, 15.0)).__next__,
    )
    schema = pq.read_schema(result.spike_file)
    assert (
        str(schema)
        == 't: double\ntime_ms: double\ntrial: int64\nneuron_index: int64\nflywire_id: int64\nexp_name: string'
    )
    spikes = read_spikes(result.spike_file, 0.1)
    np.testing.assert_array_equal(spikes.neuron_ids, np.full(count, 20, dtype=np.int64))
    np.testing.assert_allclose(spikes.time_s, events.steps * 0.0001, rtol=0, atol=1e-18)
    assert result.spikes == count and result.active_neurons == bool(count)
    assert result.spike_file.name == 'mlx_t0.1s_n1.parquet'


def test_export_timings_use_the_injected_clock(tmp_path: Path) -> None:
    c = network()
    experiment = Experiment('silent', 0, 0, (), ())
    stimulus = generate(c, experiment, 10, (0,))
    pin = InputPin('csv', 'parquet', 2, 0)
    request = SimulationRequest(tmp_path, tmp_path / 'run', 'silent', 0.001, 1, 0)
    persist_stimulus(request.output, experiment, pin, stimulus)
    events = SpikeEvents(
        np.array([], dtype=np.int64),
        np.array([], dtype=np.int64),
        np.array([], dtype=np.int64),
    )
    run = SimulationRun(events, {'warm_simulation_s': 4.0}, 0, 'test')
    result = write_run(
        request,
        c,
        pin,
        stimulus,
        run,
        {'data_load_s': 2.0},
        3.0,
        iter((10.0, 12.0, 15.0)).__next__,
    )
    report = json.loads((request.output / 'simulation.json').read_text())
    assert report['timings'] == {
        'data_load_s': 2.0,
        'warm_simulation_s': 4.0,
        'spike_io_s': 2.0,
    }
    assert report['elapsed_s'] == result.elapsed_s == 12.0


@pytest.mark.parametrize('duration', [0.0, 0.00015, float('inf'), float('nan')])
def test_duration_rejects_incomplete_or_nonfinite_timesteps(
    tmp_path: Path, duration: float
) -> None:
    (tmp_path / 'data').mkdir()
    for name in ('2025_Completeness_783.csv', '2025_Connectivity_783.parquet'):
        (tmp_path / 'data' / name).touch()
    with pytest.raises(ValidationError):
        SimulationOptions(
            project=tmp_path, output=tmp_path / 'run', duration_s=duration
        )
