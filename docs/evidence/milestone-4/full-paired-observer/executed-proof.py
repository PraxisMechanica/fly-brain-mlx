import gc
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

import mlx.core as mx
import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.brian_jobs import build, results, run
from fly_brain.qualification.adapters.causal_capture import CausalCapture
from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import observe, phase_fields, queue_hashes
from fly_brain.qualification.adapters.observer_stream import FinalSnapshot
from fly_brain.qualification.adapters.paired_observer import PairedBlock, pair_blocks, phase_hash
from fly_brain.qualification.adapters.reference_queues import ReferenceQueues
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import as_host, boolean_input, evaluate
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def raw(array):
    return {'dtype': array.dtype.str, 'shape': list(array.shape), 'sha256': hashlib.sha256(array.tobytes(order='C')).hexdigest()}


def physical(snapshot):
    return {'step': snapshot.step, 'clock_step': snapshot.clock_step, 'time_s_hex': snapshot.time_s.hex(), 'source_cursor': snapshot.source_cursor, 'spikes': raw(snapshot.spikes), 'source_spikes': raw(snapshot.source_spikes), 'pathways': [{'queues': [{'offset': queue.offset, 'slots': [raw(slot) for slot in queue.slots]} for queue in pathway.queues], 'delivered': raw(pathway.delivered)} for pathway in snapshot.pathways]}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


root = Path.cwd()
checkpoint = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
assert os.environ['MLX_ENABLE_TF32'] == '0' and mx.metal.is_available()
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
started = time.perf_counter()
connectome, pin = pinned_inputs(root)
stimulus = generate(connectome, EXPERIMENTS['sugar'], 1000, (0,))
events = stimulus.events
assert stimulus.sha256 == 'd7bb792f082eeca79d6e88a1e8ca0791dca210eb15c86ec70a34348b272a82b3'
with (output / 'stimulus.npz').open('xb') as artifact:
    np.savez_compressed(artifact, events=events, targets=np.asarray(stimulus.targets, dtype=np.int32))
print(json.dumps({'phase': 'building_reference'}), flush=True)
job = build(connectome, stimulus.targets, (), events[0], output / 'reference-build')
with (output / 'reference-job.json').open('x') as artifact:
    json.dump({'directory': str(job.directory), 'shape': asdict(job.shape), 'observed': job.observed, 'files': job.files}, artifact, indent=2)
execution = prepare(connectome, stimulus.targets, (), '0')
memory, mode = [], 'setup'
done = threading.Event()


def sample_memory():
    while not done.is_set():
        scoped = []
        for row in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,rss=,comm='], text=True).splitlines():
            columns = row.strip().split(None, 3)
            if len(columns) != 4:
                continue
            pid, parent, rss = map(int, columns[:3])
            if pid == os.getpid() or (parent == os.getpid() and Path(columns[3]).name == 'main'):
                scoped.append({'pid': pid, 'rss_bytes': rss * 1024, 'command': columns[3]})
        memory.append({'elapsed_s': time.perf_counter() - started, 'mode': mode, 'processes': scoped, 'rss_sum_bytes': sum(item['rss_bytes'] for item in scoped)})
        done.wait(0.25)


def ordinary():
    state = core.initial_state(execution.network)
    for begin in range(0, 1000, 32):
        rows, due_hashes = {}, []
        end = min(begin + 32, 1000)
        for step in range(begin, end):
            with mx.stream(mx.gpu):
                state, trace = execution.advance(state, boolean_input(events[:, step].astype(np.bool_)))
                fields = phase_fields(state, trace)
                evaluate(*state[:-1], *fields.values(), trace.due)
                due = np.asarray(trace.due, dtype=np.bool_)
                due_hashes.append(tuple(hashlib.sha256(memoryview(trial)).hexdigest() for trial in due))
                del due
            for name, value in fields.items():
                rows.setdefault(name, []).append(value)
        with mx.stream(mx.gpu):
            arrays = {name: mx.stack(values) for name, values in rows.items()}
            evaluate(*arrays.values())
            fields = {name: as_host(value) for name, value in arrays.items()}
            queue = np.asarray(state.queue, dtype=np.bool_)
        yield begin, end - begin, fields, queue, tuple(due_hashes)


def save_context(label, context, destination):
    if context is None:
        return None
    arrays, steps = {}, []
    for position, observed in (('current', context.current), ('previous', context.previous)):
        if observed is None:
            continue
        arrays.update({position + '_reference_' + name: value for name, value in observed.reference.items()})
        arrays.update({position + '_mlx_' + name: value for name, value in observed.mlx.items()})
        arrays[position + '_mlx_due_edges'] = observed.mlx_due_edges
        for index, pathway in enumerate(observed.snapshot.pathways):
            arrays[f'{position}_reference_pathway_{index}_delivered'] = pathway.delivered
            for slot, values in enumerate(pathway.queues[0].slots):
                arrays[f'{position}_reference_pathway_{index}_slot_{slot}'] = values
        steps.append({'position': position, 'actual_snapshot': physical(observed.snapshot), 'mlx_due_mask_sha256': observed.mlx_due_sha256})
    reference_weights = np.memmap(destination / job.files['weights'], dtype=np.float64, mode='r')
    layout, reductions = execution.advance.args[1], []
    for neuron in context.neurons:
        for bucket in layout.buckets:
            rows = np.flatnonzero(np.asarray(bucket.targets) == neuron)
            if not len(rows):
                continue
            row = int(rows[0])
            with mx.stream(mx.gpu):
                ids, counts, occupied = (np.asarray(value[row]) for value in (bucket.edge_ids, bucket.counts, bucket.occupied))
            arrays[f'neuron_{neuron}_actual_mlx_leaf_edges'] = ids
            arrays[f'neuron_{neuron}_actual_mlx_leaf_counts'] = counts
            arrays[f'neuron_{neuron}_actual_mlx_leaf_occupied'] = occupied
            arrays[f'neuron_{neuron}_reference_native_weight_si'] = reference_weights[ids[occupied]]
            reductions.append({'neuron': neuron, 'neuron_id': int(connectome.neuron_ids[neuron]), 'padded_width': len(ids), 'reference_threshold_margin_mv': (float(context.current.reference['pre_v'][neuron]) + 0.045) * 1000, 'mlx_threshold_margin_mv': float(context.current.mlx['pre_v'][neuron]) + 45})
    with (output / (mode + '-' + label + '-context.npz')).open('xb') as artifact:
        np.savez_compressed(artifact, **arrays)
    return {'neurons': list(context.neurons), 'steps': steps, 'reductions': reductions, 'reduction_order': 'Actual padded leaf order; adjacent-pair compensated tree over integer counts; four high/low scale products; 16-leaf compensated final tree.'}


records = {}
sampler = threading.Thread(target=sample_memory, daemon=True)
sampler.start()
try:
    for mode in ('ordinary', 'observed', 'repeat'):
        mx.reset_peak_memory()
        beginning = time.perf_counter()
        blocks, physical_hashes, spike_steps, spike_neurons = [], [], [], []
        capture, final_reference, final_fields, final_queue = CausalCapture(), None, None, None
        if mode == 'ordinary':
            frames = ordinary()
        else:
            reference = run(job, output / (mode + '-reference-results'))
            mlx = observe(execution, core.initial_state(execution.network), events, EventLedger(connectome, stimulus.targets, 1))
            frames = pair_blocks(reference, mlx, ReferenceQueues(connectome.sources, pin.neurons, events[0]))
        print(json.dumps({'phase': 'executing', 'mode': mode}), flush=True)
        try:
            for frame in frames:
                if isinstance(frame, FinalSnapshot):
                    final_reference = frame
                    physical_hashes.append(fingerprint(physical(frame.step)))
                    continue
                if mode == 'ordinary':
                    begin, rows, fields, queue, due_hashes = frame
                    queue_digests = queue_hashes(queue)
                else:
                    assert isinstance(frame, PairedBlock)
                    capture.check(frame)
                    block = frame.mlx
                    begin, rows, fields, queue, due_hashes = block.begin, block.rows, block.fields, block.final_queue, block.due_sha256
                    queue_digests = block.queue_sha256
                    physical_hashes.extend(fingerprint(physical(snapshot)) for snapshot in frame.snapshots)
                assert all(np.isfinite(value).all() for value in fields.values())
                block_record = {'begin': begin, 'rows': rows, 'mlx_native_phase_sha256': phase_hash(fields), 'mlx_fields': {name: raw(value) for name, value in fields.items()}, 'mlx_queue_sha256': queue_digests, 'mlx_due_sha256': due_hashes}
                if mode != 'ordinary':
                    block_record['reference_native_phase_sha256'] = frame.native_sha256[0]
                blocks.append(block_record)
                local_steps, trials, neurons = np.nonzero(fields['spikes'])
                assert not trials.any()
                spike_steps.extend((local_steps + begin).tolist())
                spike_neurons.extend(neurons.tolist())
                final_fields = {name: np.asarray(value[-1, 0]).copy() for name, value in fields.items()}
                final_queue = queue
                if begin == 0 or (begin + rows) % 256 == 0:
                    print(json.dumps({'phase': 'progress', 'mode': mode, 'steps': begin + rows, 'seconds': time.perf_counter() - beginning}), flush=True)
        finally:
            frames.close()
            if mode != 'ordinary':
                reference.close()
        execution_s = time.perf_counter() - beginning
        assert final_fields is not None and final_queue is not None
        final_fields['queue'] = final_queue
        final_fields['spike_steps'] = np.asarray(spike_steps, dtype=np.int64)
        final_fields['spike_neurons'] = np.asarray(spike_neurons, dtype=np.int64)
        with (output / (mode + '-mlx-final.npz')).open('xb') as artifact:
            np.savez_compressed(artifact, **final_fields)
        record = {'execution_s': execution_s, 'mlx_allocator_peak_bytes': mx.get_peak_memory(), 'blocks': blocks, 'physical_reference_hashes': physical_hashes, 'spikes': len(spike_steps), 'active_neurons': len(set(spike_neurons)), 'mlx_final': {name: raw(value) for name, value in final_fields.items()}}
        if mode != 'ordinary':
            native = results(job, output / (mode + '-reference-results'))
            assert final_reference is not None and capture.audit.step == 1000
            assert all(value.tobytes() == native[name].tobytes() for name, value in final_reference.fields.items())
            with (output / (mode + '-reference-native.npz')).open('xb') as artifact:
                np.savez_compressed(artifact, **native)
            record.update({'reference_native': {name: raw(value) for name, value in native.items()}, 'first_budget_violation': asdict(capture.audit.first_budget_violation) if capture.audit.first_budget_violation else None, 'first_spike_step': capture.audit.first_spike_step, 'first_spike_neurons': capture.audit.first_spike_neurons, 'budget_context': save_context('budget', capture.budget, output / (mode + '-reference-results')), 'spike_context': save_context('spike', capture.spike, output / (mode + '-reference-results'))})
        records[mode] = record
        with (output / (mode + '.json')).open('x') as artifact:
            json.dump(record, artifact, indent=2)
        print(json.dumps({'phase': 'completed', 'mode': mode, 'seconds': execution_s, 'spikes': record['spikes'], 'first_budget_violation': record.get('first_budget_violation'), 'first_spike_step': record.get('first_spike_step')}), flush=True)
        del frames, frame, final_fields, final_queue, capture, fields, queue
        gc.collect()
finally:
    done.set()
    sampler.join(timeout=5)
assert records['ordinary']['mlx_final'] == records['observed']['mlx_final'] == records['repeat']['mlx_final']
for mode in ('observed', 'repeat'):
    for stock, block in zip(records['ordinary']['blocks'], records[mode]['blocks'], strict=True):
        assert all(stock[name] == block[name] for name in stock)
assert records['observed']['physical_reference_hashes'] == records['repeat']['physical_reference_hashes']
assert records['observed']['reference_native'] == records['repeat']['reference_native']
assert records['observed']['first_budget_violation'] == records['repeat']['first_budget_violation']
assert records['observed']['first_spike_step'] == records['repeat']['first_spike_step']
assert [block['reference_native_phase_sha256'] for block in records['observed']['blocks']] == [block['reference_native_phase_sha256'] for block in records['repeat']['blocks']]
report = {'implementation_commit': checkpoint, 'scope': 'Complete shortest sugar MLX observer transparency, fresh-state replay, live Brian2 causal audit, and sampled concurrent resident memory. No PyTorch comparison or full-matrix parity approval.', 'neurons': pin.neurons, 'edges': pin.edges, 'steps': 1000, 'trials': [0], 'stimulus_sha256': stimulus.sha256, 'records': records, 'memory_scope': 'Sampled resident-size sum of this proof process and its direct compiled reference child during execution/capture, after load/build/device setup. Shared pages may be counted twice. MLX allocator peaks are separate and are not added to RSS. This is not total system/unified-memory peak or four-trial qualification.', 'sampled_rss_sum_peak_bytes': max(sample['rss_sum_bytes'] for sample in memory), 'memory_samples': memory, 'total_seconds': time.perf_counter() - started}
with (output / 'paired-observer.json').open('x') as artifact:
    json.dump(report, artifact, indent=2)
    artifact.write('\n')
print(json.dumps({'completed': True, 'output': str(output), 'sampled_rss_sum_peak_bytes': report['sampled_rss_sum_peak_bytes']}), flush=True)
