"""Compare independent NumPy64 replay with retained full-network native results."""

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.comparison.acceptance import (
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.comparison.models import SpikeSteps
from fly_brain.infrastructure.output_paths import require_retained_output
from fly_brain.qualification.adapters.batch_environment import read_environment
from fly_brain.qualification.adapters.batch_stimulus import load as load_stimulus
from fly_brain.simulation.identifiers import NeuronRows64
from fly_brain.simulation.stimulus_service import read_experiment

from .qualification_cases import case_name, read_index
from .tiered_oracle import Integer, Oracle


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows_at(raster: tuple[Integer, Integer], step: int) -> Integer:
    times, rows = raster
    begin, end = np.searchsorted(times, (step, step + 1))
    return rows[begin:end]


def run(index: Path, name: str, output: Path, limit_s: float) -> dict[str, object]:
    started = perf_counter()
    if np.__version__ != '1.26.4':
        raise RuntimeError('Full oracle replay requires NumPy 1.26.4')
    project = Path(__file__).resolve().parents[1]
    require_retained_output(output.resolve(), project)
    selected = [
        (case, entry)
        for case, entry in read_index(index).items()
        if case_name(case) == name
    ]
    if len(selected) != 1 or limit_s <= 0:
        raise ValueError('Select one indexed case and a positive time limit')
    case, entry = selected[0]
    directory = entry.directory
    names = (
        'case.json',
        'environment.json',
        'launch.json',
        'stimulus.json',
        'stimulus.npz',
        'normalized-spikes.npz',
        'observations/paired-first/reference-native.npz',
        'observations/paired-first/mlx-native.npz',
        'observations/paired-first/causal.json',
    )
    bound = entry.artifact_sha256
    hashes = {name: digest(directory / name) for name in names}
    if bound is None or any(bound.get(name) != value for name, value in hashes.items()):
        raise ValueError('Consumed artifacts differ from the retained matrix binding')
    connectome, pin = pinned_inputs()(project)
    record = json.loads((directory / 'case.json').read_text())
    if record['input_pins'] != asdict(pin):
        raise ValueError('Retained case and current pinned connectome differ')
    launch = json.loads((directory / 'launch.json').read_text())['commit']

    def read_launch(commit: str, path: str) -> bytes:
        return subprocess.check_output(
            ['git', 'show', commit + ':' + path], cwd=project
        )

    read_environment(project, (directory, launch), read_launch)
    experiment = read_experiment(case.experiment)
    stimulus = load_stimulus(directory, experiment, pin)
    if stimulus.events.shape != (1, case.steps, len(stimulus.targets)):
        raise ValueError('Retained input does not contain exactly the selected trial')
    if stimulus.sha256 != record['stimulus_sha256']:
        raise ValueError('Canonical stimulus differs from the accepted case')
    silenced = tuple(
        map(
            int, np.flatnonzero(np.isin(connectome.neuron_ids, experiment.silenced_ids))
        )
    )
    oracle = Oracle(connectome, tuple(map(int, stimulus.targets)), silenced)
    rasters: dict[str, tuple[Integer, Integer]] = {}
    with np.load(directory / 'normalized-spikes.npz', allow_pickle=False) as normalized:
        for engine in ('brian', 'mlx'):
            native_name = 'reference' if engine == 'brian' else 'mlx'
            path = directory / f'observations/paired-first/{native_name}-native.npz'
            with np.load(path, allow_pickle=False) as native:
                if engine == 'brian':
                    times = steps_from_reference_clock(native['spike_t'], case.steps)
                    rows = native['spike_i'].astype(np.int64)
                else:
                    times = native['spike_steps'].astype(np.int64)
                    rows = native['spike_neurons'].astype(np.int64)
            validate_coordinates(
                SpikeSteps(NeuronRows64(rows), times),
                connectome.neuron_ids.size,
                case.steps,
            )
            if not np.array_equal(
                connectome.neuron_ids[rows], normalized[engine + '_neurons']
            ) or not np.array_equal(times, normalized[engine + '_steps']):
                raise ValueError(
                    'Native spike rows and saved FlyWire identifiers differ'
                )
            order = np.lexsort((rows, times))
            rasters[engine] = times[order], rows[order]
    output.mkdir(parents=True, exist_ok=False)
    report: dict[str, object] = {
        'oracle_gate_passed': False,
        'case': asdict(case),
        'reused_case': str(directory),
        'reused_index': str(index.resolve()),
        'index_sha256': digest(index),
        'consumed_artifact_sha256': hashes,
        'input_pins': asdict(pin),
        'stimulus_sha256': stimulus.sha256,
        'commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=project, text=True
        ).strip(),
        'source_sha256': {
            path: digest(project / path)
            for path in ('tools/tiered_oracle.py', 'tools/compare_full_oracle.py')
        },
        'scope': 'Fixed-input full-network precision diagnostic using retained MLX32/Brian2 results. No new candidate acceptance, ensemble evidence or GPU execution.',
        'phase_budget_mv': 1e-11,
        'numpy': np.__version__,
        'setup_s': perf_counter() - started,
        'first_oracle_reference_divergence': None,
        'first_mlx_oracle_divergence': None,
    }
    emitted_steps: list[Integer] = []
    emitted_rows: list[Integer] = []
    loop_started = perf_counter()
    try:
        for step, events in enumerate(stimulus.events[0]):
            frame = oracle.advance(events.astype(np.bool_))
            rows = np.flatnonzero(frame.spikes)
            emitted_steps.append(np.full(rows.size, step, dtype=np.int64))
            emitted_rows.append(rows)
            for engine in ('brian', 'mlx'):
                expected = rows_at(rasters[engine], step)
                if np.array_equal(rows, expected):
                    continue
                different = np.setxor1d(rows, expected)
                context = {
                    'step': step,
                    'time_ms': step * 0.1,
                    'neuron_rows': different.tolist(),
                    'flywire_ids': connectome.neuron_ids[different].tolist(),
                    'oracle_spikes': rows.tolist(),
                    engine + '_spikes': expected.tolist(),
                    'oracle_pre_voltage_mv': (frame.pre_v[different] * 1000).tolist(),
                    'oracle_pre_synaptic_mv': (frame.pre_g[different] * 1000).tolist(),
                    'oracle_available': frame.available[different].tolist(),
                }
                if engine == 'brian':
                    report['first_oracle_reference_divergence'] = context
                    raise ValueError(
                        f'Float64 oracle/reference spike mismatch at {step}'
                    )
                if report['first_mlx_oracle_divergence'] is None:
                    report['first_mlx_oracle_divergence'] = context
            elapsed = perf_counter() - started
            if elapsed > limit_s:
                raise ValueError(f'Bounded precision replay exceeded {limit_s} seconds')
            if (step + 1) % 1000 == 0:
                print(
                    json.dumps(
                        {'steps': step + 1, 'of': case.steps, 'elapsed_s': elapsed}
                    ),
                    flush=True,
                )
        neurons = connectome.neuron_ids.size
        reference_counts = np.bincount(rasters['brian'][1], minlength=neurons)
        mlx_counts = np.bincount(rasters['mlx'][1], minlength=neurons)
        if not np.array_equal(reference_counts, oracle.counts):
            raise ValueError('Full-network oracle/reference neuron counts differ')
        reference = directory / 'observations/paired-first/reference-native.npz'
        with np.load(reference, allow_pickle=False) as native:
            voltage_error = float(np.max(np.abs(oracle.v - native['v']))) * 1000
            synaptic_error = float(np.max(np.abs(oracle.g - native['g']))) * 1000
            last = np.rint(native['lastspike'] / 0.0001).astype(np.int64)
            receiving = (case.steps - 1 - oracle.last >= oracle.refractory) & (
                oracle.last != case.steps - 1
            )
            if not np.array_equal(oracle.last, last) or not np.array_equal(
                receiving, native['not_refractory']
            ):
                raise ValueError('Final oracle/reference refractory state differs')
        report['reference_final_voltage_error_mv'] = voltage_error
        report['reference_final_synaptic_error_mv'] = synaptic_error
        if max(voltage_error, synaptic_error) > 1e-11:
            raise ValueError('Final float64 reference phase-state budget failed')
        pending = np.zeros_like(oracle.queue)
        times, rows = rasters['brian']
        keep = times + 18 >= case.steps
        pending[(times[keep] + 18) % 19, rows[keep]] = True
        if not np.array_equal(oracle.queue, pending):
            raise ValueError('Final oracle queue differs from reference emissions')
        with np.load(
            directory / 'observations/paired-first/mlx-native.npz', allow_pickle=False
        ) as native:
            report['mlx_final_voltage_error_mv'] = float(
                np.max(np.abs(native['end_v'] - oracle.v * 1000))
            )
            report['mlx_final_synaptic_error_mv'] = float(
                np.max(np.abs(native['end_g'] - oracle.g * 1000))
            )
        np.savez_compressed(
            output / 'counts.npz',
            neuron_ids=connectome.neuron_ids,
            oracle=oracle.counts,
            brian=reference_counts,
            mlx=mlx_counts,
        )
        report['reference_spikes'] = int(reference_counts.sum())
        report['oracle_spikes'] = int(oracle.counts.sum())
        report['mlx_spikes'] = int(mlx_counts.sum())
        report['mlx_count_l1'] = int(np.abs(mlx_counts - oracle.counts).sum())
        report['oracle_gate_passed'] = True
    except Exception as error:
        report['failure'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        np.savez_compressed(
            output / 'oracle-state.npz',
            v=oracle.v,
            g=oracle.g,
            last=oracle.last,
            queue=oracle.queue,
            counts=oracle.counts,
            spike_steps=np.concatenate(emitted_steps),
            spike_neurons=np.concatenate(emitted_rows),
        )
        report['completed_steps'] = oracle.tick
        report['loop_s'] = perf_counter() - loop_started
        report['elapsed_s'] = perf_counter() - started
        report['artifact_sha256'] = {
            path.name: digest(path) for path in output.glob('*.npz')
        }
        (output / 'precision.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit-s', type=float, default=600)
    arguments = parser.parse_args()
    run(arguments.index, arguments.case, arguments.output, arguments.limit_s)
