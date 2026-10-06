import hashlib
import importlib.metadata
import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from .models import (
    Connectome,
    Experiment,
    InputPin,
    SimulationRequest,
    SimulationResult,
    SimulationRun,
    Stimulus,
)

SPIKE_SCHEMA = pa.schema(
    [
        ('t', pa.float64()),
        ('time_ms', pa.float64()),
        ('trial', pa.int64()),
        ('neuron_index', pa.int64()),
        ('flywire_id', pa.int64()),
        ('exp_name', pa.string()),
    ]
)


def persist_stimulus(
    output: Path, experiment: Experiment, pin: InputPin, stimulus: Stimulus
) -> Stimulus:
    output.mkdir(parents=True, exist_ok=False)
    artifact = output / 'stimulus.npz'
    with artifact.open('xb') as destination:
        np.savez_compressed(destination, events=stimulus.events)
    metadata = {
        'format_version': 1,
        'layout': ['trial', 'step', 'channel'],
        'shape': list(stimulus.events.shape),
        'dtype': stimulus.events.dtype.str,
        'dt_ms': 0.1,
        'generator': 'PCG64',
        'numpy': np.__version__,
        'seed': stimulus.seed,
        'generator_code': stimulus.generator_code,
        'trial_indices': list(stimulus.trial_indices),
        'targets': list(stimulus.targets),
        'activated_ids': list(experiment.activated_ids),
        'rates_hz': list(stimulus.rates_hz),
        'experiment': experiment.name,
        'experiment_code': experiment.code,
        'silenced_ids': list(experiment.silenced_ids),
        'canonical_event_sha256': stimulus.sha256,
        'per_trial_event_sha256': [
            hashlib.sha256(row.tobytes()).hexdigest() for row in stimulus.events
        ],
        'seed_tuples': [
            [stimulus.seed, stimulus.generator_code, trial]
            for trial in stimulus.trial_indices
        ],
        'input_sha256': {
            'completeness': pin.completeness_sha256,
            'connectivity': pin.connectivity_sha256,
        },
        'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }
    with (output / 'stimulus.json').open('x') as destination:
        json.dump(metadata, destination, indent=2, allow_nan=False)
        destination.write('\n')
    with np.load(artifact, allow_pickle=False) as saved:
        restored = saved['events']
    if (
        restored.dtype != np.uint8
        or restored.shape != stimulus.events.shape
        or hashlib.sha256(restored.tobytes()).hexdigest() != stimulus.sha256
    ):
        raise ValueError('Stored stimulus does not match canonical input')
    restored.setflags(write=False)
    return replace(stimulus, events=restored)


def write_run(
    request: SimulationRequest,
    connectome: Connectome,
    pin: InputPin,
    stimulus: Stimulus,
    run: SimulationRun,
    timings: dict[str, float],
    started: float,
    clock: Callable[[], float],
) -> SimulationResult:
    spike_io = clock()
    name = f'mlx_t{request.duration_s:g}s_n{request.trials}'
    times = run.spikes.steps.astype(np.float64) * 0.0001
    table = pa.table(
        {
            't': times,
            'time_ms': times * 1000,
            'trial': run.spikes.trials,
            'neuron_index': run.spikes.neurons,
            'flywire_id': connectome.neuron_ids[run.spikes.neurons],
            'exp_name': [name] * times.size,
        },
        schema=SPIKE_SCHEMA,
    )
    path = request.output / f'{name}.parquet'
    pq.write_table(table, path, compression='brotli')
    timings = {**timings, **run.timings, 'spike_io_s': clock() - spike_io}
    elapsed = clock() - started
    spikes = int(times.size)
    active = int(np.unique(run.spikes.neurons).size)
    report = {
        'completed': True,
        'backend': 'mlx',
        'experiment': request.experiment,
        'duration_s': request.duration_s,
        'trials': request.trials,
        'seed': request.seed,
        'spikes': spikes,
        'active_neurons': active,
        'spike_file': str(path),
        'timings': timings,
        'elapsed_s': elapsed,
        'device': run.device_name,
        'mlx_peak_allocation_bytes': run.peak_device_bytes,
        'memory_scope': 'MLX allocator peak, not total system unified-memory usage',
        'compilation': 'disabled',
        'MLX_ENABLE_TF32': '0',
        'canonical_stimulus_sha256': stimulus.sha256,
        'spike_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'input_sha256': {
            'completeness': pin.completeness_sha256,
            'connectivity': pin.connectivity_sha256,
        },
        'versions': {
            package: importlib.metadata.version(package)
            for package in (
                'fly-brain',
                'mlx',
                'mlx-metal',
                'numpy',
                'pyarrow',
                'pydantic',
            )
        },
        'source_sha256': {
            name: hashlib.sha256(
                (Path(__file__).parent / name).read_bytes()
            ).hexdigest()
            for name in (
                'inputs.py',
                'mapping.py',
                'experiments.py',
                'stimuli.py',
                'service.py',
                'storage.py',
                'backend/core.py',
                'backend/accumulation.py',
                'backend/bucketed.py',
                'backend/runner.py',
            )
        },
        'scope': 'Production MLX execution and file export; scientific parity and performance acceptance are separate gates.',
    }
    with (request.output / 'simulation.json').open('x') as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
        destination.write('\n')
    return SimulationResult(path, spikes, active, elapsed)
