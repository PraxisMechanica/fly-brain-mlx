"""Gate an independent NumPy64 oracle against pinned Brian2 on fixed input."""

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import brian2 as b
import numpy as np
from numpy.typing import ArrayLike, NDArray

from fly_brain.bootstrap import pinned_inputs
from fly_brain.infrastructure.output_paths import require_retained_output
from fly_brain.qualification.adapters.brian_reference import (
    default_parameters,
    silence_neurons,
)
from fly_brain.simulation.identifiers import FlyWireIds64, NeuronRows32
from fly_brain.simulation.models import Connectome

from .tiered_oracle import Boolean, Oracle

Trace = dict[str, NDArray[np.float64] | Boolean]


def network(
    neurons: int,
    sources: tuple[int, ...] = (),
    destinations: tuple[int, ...] = (),
    counts: tuple[int, ...] = (),
) -> Connectome:
    signed = np.asarray(counts, dtype=np.int32)
    return Connectome(
        FlyWireIds64(np.arange(neurons, dtype=np.int64)),
        NeuronRows32(np.asarray(sources, dtype=np.int32)),
        NeuronRows32(np.asarray(destinations, dtype=np.int32)),
        signed,
        signed.astype(np.float64) * 0.275,
    )


def subnet(full: Connectome, size: int = 800) -> tuple[Connectome, NDArray[np.int64]]:
    selected = np.zeros(full.neuron_ids.size, dtype=np.bool_)
    frontier = np.asarray([np.argmax(np.bincount(full.sources))], dtype=np.int64)
    selected[frontier] = True
    while np.count_nonzero(selected) < size:
        neighbors = np.unique(
            np.concatenate(
                (
                    full.destinations[np.isin(full.sources, frontier)],
                    full.sources[np.isin(full.destinations, frontier)],
                )
            )
        )
        frontier = neighbors[~selected[neighbors]][: size - np.count_nonzero(selected)]
        if not frontier.size:
            raise ValueError('Connected component is smaller than requested subnet')
        selected[frontier] = True
    rows = np.flatnonzero(selected)
    inverse = np.full(full.neuron_ids.size, -1, dtype=np.int32)
    inverse[rows] = np.arange(rows.size, dtype=np.int32)
    edges = np.flatnonzero(selected[full.sources] & selected[full.destinations])
    return Connectome(
        FlyWireIds64(full.neuron_ids[rows]),
        NeuronRows32(inverse[full.sources[edges]]),
        NeuronRows32(inverse[full.destinations[edges]]),
        full.counts[edges],
        full.weights_mv[edges],
    ), edges


def reference(
    connectome: Connectome,
    targets: tuple[int, ...],
    events: Boolean,
    output: Path,
    silenced: tuple[int, ...],
    voltage_mv: ArrayLike,
    synaptic_mv: ArrayLike,
    last_spike: ArrayLike,
    threshold_only: bool,
) -> Trace:
    b.set_device('runtime')
    b.start_scope()
    b.defaultclock.dt = 0.1 * b.ms
    b.prefs.codegen.target = 'numpy'
    b.prefs.legacy.refractory_timing = False
    params = default_parameters()
    neurons = connectome.neuron_ids.size
    group = b.NeuronGroup(
        neurons,
        params['eqs'],
        method='linear',
        threshold=params['eq_th'],
        reset=params['eq_rst'],
        refractory='rfc',
        namespace=params,
    )
    group.v = np.broadcast_to(voltage_mv, (neurons,)) * b.mV
    group.g = np.broadcast_to(synaptic_mv, (neurons,)) * b.mV
    group.lastspike = np.broadcast_to(last_spike, (neurons,)) * 0.1 * b.ms
    refractory = np.full(neurons, 2.2)
    refractory[list(targets)] = 0
    group.rfc = refractory * b.ms
    group.state_updater.active = not threshold_only
    objects: list[b.BrianObject] = [group]
    if connectome.sources.size:
        recurrent = b.Synapses(
            group, group, 'w : volt', on_pre='g += w', delay=1.8 * b.ms
        )
        recurrent.connect(i=connectome.sources, j=connectome.destinations)
        recurrent.w = connectome.counts * params['w_syn']
        silence_neurons(recurrent, silenced)
        objects.append(recurrent)
    if targets:
        steps, channels = np.nonzero(events)
        source = b.SpikeGeneratorGroup(len(targets), channels, steps * 0.1 * b.ms)
        external = b.Synapses(source, group, on_pre='v += 68.75*mV')
        external.connect(i=np.arange(len(targets)), j=np.asarray(targets))
        external.pre.order = 0
        objects.extend((source, external))
    pre = b.StateMonitor(
        group, ('v', 'g', 'not_refractory'), record=True, when='thresholds', order=-1
    )
    before = b.StateMonitor(
        group, ('v', 'g', 'not_refractory'), record=True, when='resets', order=-1
    )
    end = b.StateMonitor(group, ('v', 'g', 'lastspike'), record=True, when='end')
    spikes = b.SpikeMonitor(group)
    b.Network(*objects, pre, before, end, spikes).run(len(events) * 0.1 * b.ms)
    if not threshold_only:
        (output / 'generated-update.py.txt').write_text(
            str(group.state_updater.codeobj.code['run'])
        )
    raster = np.zeros((len(events), neurons), dtype=np.bool_)
    ticks = np.rint(spikes.t[:] / b.defaultclock.dt).astype(np.int64)
    raster[ticks, spikes.i[:]] = True
    return {
        'pre_v': np.asarray(pre.v[:]).T,
        'pre_g': np.asarray(pre.g[:]).T,
        'available': np.asarray(pre.not_refractory[:]).T,
        'before_v': np.asarray(before.v[:]).T,
        'before_g': np.asarray(before.g[:]).T,
        'receiving': np.asarray(before.not_refractory[:]).T,
        'v': np.asarray(end.v[:]).T,
        'g': np.asarray(end.g[:]).T,
        'last_spike': np.rint(end.lastspike[:] / b.defaultclock.dt).T,
        'spikes': raster,
    }


def run_case(
    output: Path,
    name: str,
    connectome: Connectome,
    targets: tuple[int, ...],
    events: Boolean,
    *,
    silenced: tuple[int, ...] = (),
    voltage_mv: ArrayLike = -52,
    synaptic_mv: ArrayLike = 0,
    last_spike: ArrayLike = -100000000,
    threshold_only: bool = False,
    require_propagation: bool = False,
) -> dict[str, object]:
    directory = output / name
    directory.mkdir()
    started = perf_counter()
    np.savez_compressed(
        directory / 'input.npz',
        events=events,
        targets=targets,
        silenced=silenced,
        voltage_mv=voltage_mv,
        synaptic_mv=synaptic_mv,
        last_spike=last_spike,
        sources=connectome.sources,
        destinations=connectome.destinations,
        counts=connectome.counts,
        neuron_ids=connectome.neuron_ids,
    )
    expected = reference(
        connectome,
        targets,
        events,
        directory,
        silenced,
        voltage_mv,
        synaptic_mv,
        last_spike,
        threshold_only,
    )
    oracle = Oracle(
        connectome,
        targets,
        silenced,
        voltage_mv=voltage_mv,
        synaptic_mv=synaptic_mv,
        last_spike=last_spike,
        threshold_only=threshold_only,
    )
    observed = np.zeros_like(expected['spikes'], dtype=np.bool_)
    maximum = 0.0
    accepted_events = discarded_events = 0
    for tick, inputs in enumerate(events):
        frame = oracle.advance(inputs)
        observed[tick] = frame.spikes
        for field in ('spikes', 'available', 'receiving', 'last_spike'):
            if not np.array_equal(getattr(frame, field), expected[field][tick]):
                raise ValueError(f'{name}: exact {field} gate failed at step {tick}')
        for field in ('pre_v', 'pre_g', 'before_v', 'before_g', 'v', 'g'):
            difference = np.abs(getattr(frame, field) - expected[field][tick])
            maximum = max(maximum, float(difference.max(initial=0)) * 1000)
            if np.any(difference > 1e-14):
                np.savez_compressed(
                    directory / 'first-failure.npz',
                    oracle=getattr(frame, field),
                    reference=expected[field][tick],
                    tick=tick,
                )
                raise ValueError(f'{name}: float64 {field} state gate failed at {tick}')
        due = (
            np.flatnonzero(expected['spikes'][tick - 18][connectome.sources])
            if tick >= 18
            else np.empty(0, dtype=np.int64)
        )
        accepted = due[expected['receiving'][tick][connectome.destinations[due]]]
        if not np.array_equal(np.sort(frame.due_edges), due) or not np.array_equal(
            np.sort(frame.accepted_edges), accepted
        ):
            raise ValueError(f'{name}: exact delivery membership failed at {tick}')
        accepted_events += accepted.size
        discarded_events += due.size - accepted.size
    reference_events = np.column_stack(np.nonzero(expected['spikes']))
    oracle_events = np.column_stack(np.nonzero(observed))
    propagated = int(
        observed[:, ~np.isin(np.arange(connectome.neuron_ids.size), targets)].sum()
    )
    if require_propagation and not propagated:
        raise ValueError(f'{name}: no recurrently driven spikes; gate is uninformative')
    np.savez_compressed(
        directory / 'result.npz',
        reference_events=reference_events,
        oracle_events=oracle_events,
        reference_counts=np.count_nonzero(expected['spikes'], axis=0),
        oracle_counts=oracle.counts,
        reference_v=expected['v'][-1],
        oracle_v=oracle.v,
        reference_g=expected['g'][-1],
        oracle_g=oracle.g,
        oracle_queue=oracle.queue,
        oracle_last=oracle.last,
    )
    result: dict[str, object] = {
        'case': name,
        'accepted': True,
        'neurons': connectome.neuron_ids.size,
        'edges': connectome.sources.size,
        'steps': len(events),
        'spikes': len(reference_events),
        'propagated_spikes': propagated,
        'accepted_arrivals': accepted_events,
        'discarded_arrivals': discarded_events,
        'max_phase_state_error_mv': maximum,
        'elapsed_s': perf_counter() - started,
        'input_sha256': hashlib.sha256(
            (directory / 'input.npz').read_bytes()
        ).hexdigest(),
        'result_sha256': hashlib.sha256(
            (directory / 'result.npz').read_bytes()
        ).hexdigest(),
    }
    (directory / 'case.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
    return result


def run(output: Path) -> dict[str, object]:
    if b.__version__ != '2.8.0' or np.__version__ != '1.26.4':
        raise RuntimeError('Exact tier requires Brian2 2.8.0 and NumPy 1.26.4')
    project = Path(__file__).resolve().parents[1]
    require_retained_output(output.resolve(), project)
    output.mkdir(parents=True, exist_ok=False)
    report: dict[str, object] = {
        'accepted': False,
        'commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], text=True
        ).strip(),
        'brian2': b.__version__,
        'numpy': np.__version__,
        'sources': {
            name: hashlib.sha256((project / name).read_bytes()).hexdigest()
            for name in (
                'tools/tiered_oracle.py',
                'tools/validate_exact_tier.py',
                'src/fly_brain/qualification/adapters/brian_reference.py',
            )
        },
        'scope': 'Exact SI float64 oracle qualification; no MLX or full-network acceptance.',
        'reduction_order': 'Brian2-style source order, original row order within source; no coalescing.',
        'phase_budget_mv': 1e-11,
    }
    results: list[dict[str, object]] = []
    report['cases'] = results
    try:
        micro = network(4, (0, 0, 0, 1, 2), (0, 1, 1, 2, 1), (3, 400, 1, -2, 8))
        events = np.zeros((120, 3), dtype=np.bool_)
        events[[0, 1, 20, 21, 22, 37, 38, 60, 80], 0] = True
        events[[0, 21, 22, 40, 60], 1] = True
        events[[0, 22, 60], 2] = True
        results.append(
            run_case(
                output,
                'delay-reset-overlap-zero-rate',
                micro,
                (0, 2, 0),
                events,
                voltage_mv=(-44, -44, -52, -52),
            )
        )
        results.append(
            run_case(
                output,
                'outgoing-silencing',
                micro,
                (0, 2, 0),
                events,
                silenced=(0,),
                voltage_mv=(-44, -44, -52, -52),
            )
        )
        results.append(
            run_case(
                output,
                'refractory-freeze-release',
                micro,
                (0,),
                events[:, :1],
                voltage_mv=(-44, -50, -52, -52),
                synaptic_mv=(0, 1, 0, 0),
                last_spike=(-100000000, 0, 0, 0),
            )
        )
        spacing = float(np.spacing(np.float32(45)))
        results.append(
            run_case(
                output,
                'strict-threshold',
                network(3),
                (),
                np.zeros((1, 0), dtype=np.bool_),
                voltage_mv=(-45 - spacing, -45, -45 + spacing),
                threshold_only=True,
            )
        )
        full, pin = pinned_inputs()(project)
        small, edge_rows = subnet(full)
        report['input_pins'] = asdict(pin)
        np.savez_compressed(
            output / 'subnet.npz',
            neuron_ids=small.neuron_ids,
            sources=small.sources,
            destinations=small.destinations,
            counts=small.counts,
            original_edge_rows=edge_rows,
        )
        degree = np.bincount(small.sources, minlength=800)
        targets = tuple(map(int, np.lexsort((np.arange(800), -degree))[:16]))
        random = np.random.Generator(np.random.PCG64(20261015))
        draws = random.random((10000, 16))
        ordinary = draws < 0.02
        results.append(
            run_case(
                output,
                'connected-800-drive',
                small,
                targets,
                ordinary,
                require_propagation=True,
            )
        )
        two_class = draws < np.asarray([0.02] * 8 + [0.01] * 7 + [0.0])
        results.append(
            run_case(
                output,
                'connected-800-two-class',
                small,
                targets,
                two_class,
                require_propagation=True,
            )
        )
        results.append(
            run_case(
                output,
                'connected-800-silenced',
                small,
                targets,
                ordinary,
                silenced=targets,
            )
        )
        results.append(
            run_case(
                output,
                'connected-800-silent',
                small,
                (),
                np.zeros((1000, 0), dtype=np.bool_),
            )
        )
        report['accepted'] = True
    except (ValueError, AssertionError) as error:
        report['failure'] = str(error)
        raise
    finally:
        (output / 'exact-tier.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    run(options.output)
