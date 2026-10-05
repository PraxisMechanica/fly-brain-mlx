import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from contextlib import ExitStack, closing
from dataclasses import asdict
from pathlib import Path

import mlx.core as mx
import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.brian_jobs import build, results, run
from fly_brain.qualification.adapters.causal_capture import CausalCapture
from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import observe
from fly_brain.qualification.adapters.paired_observer import finish_reference, read_block, trial_block
from fly_brain.qualification.adapters.reference_queues import ReferenceQueues
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def raw(value):
    return {'dtype': value.dtype.str, 'shape': list(value.shape), 'sha256': hashlib.sha256(value.tobytes(order='C')).hexdigest()}


root = Path.cwd()
checkpoint = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
assert os.environ['MLX_ENABLE_TF32'] == '0' and mx.metal.is_available()
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
started = time.perf_counter()
connectome, pin = pinned_inputs(root)
stimulus = generate(connectome, EXPERIMENTS['sugar'], 1000, (0, 1, 2, 3))
events = stimulus.events
sole = json.loads((root / 'docs/evidence/milestone-4/full-paired-observer/observed.json').read_text())
assert hashlib.sha256(events[0].tobytes()).hexdigest() == 'd7bb792f082eeca79d6e88a1e8ca0791dca210eb15c86ec70a34348b272a82b3'
with (output / 'stimulus.npz').open('xb') as artifact:
    np.savez_compressed(artifact, events=events, targets=np.asarray(stimulus.targets, dtype=np.int32))
jobs = []
for trial in range(4):
    print(json.dumps({'phase': 'building_reference', 'trial': trial}), flush=True)
    jobs.append(build(connectome, stimulus.targets, (), events[trial], output / f'reference-{trial}-build'))
with (output / 'reference-jobs.json').open('x') as artifact:
    json.dump([{'directory': str(job.directory), 'shape': asdict(job.shape), 'files': job.files} for job in jobs], artifact, indent=2)
execution = prepare(connectome, stimulus.targets, (), '0')
captures = [CausalCapture() for _ in range(4)]
ledgers = [ReferenceQueues(connectome.sources, pin.neurons, trial) for trial in events]
memory, blocks = [], []
done = threading.Event()


def sample_memory():
    while not done.is_set():
        processes = []
        for row in subprocess.check_output(['ps', '-axo', 'pid=,ppid=,rss=,comm='], text=True).splitlines():
            columns = row.strip().split(None, 3)
            if len(columns) != 4:
                continue
            pid, parent, rss = map(int, columns[:3])
            if pid == os.getpid() or (parent == os.getpid() and Path(columns[3]).name == 'main'):
                processes.append({'pid': pid, 'rss_bytes': rss * 1024, 'command': columns[3]})
        memory.append({'elapsed_s': time.perf_counter() - started, 'processes': processes, 'rss_sum_bytes': sum(process['rss_bytes'] for process in processes)})
        done.wait(0.25)


def save_context(trial, label, context):
    if context is None:
        return None
    arrays, observations = {}, []
    for position, observed in (('current', context.current), ('previous', context.previous)):
        if observed is None:
            continue
        arrays.update({f'{position}_reference_{name}': value for name, value in observed.reference.items()})
        arrays.update({f'{position}_mlx_{name}': value for name, value in observed.mlx.items()})
        arrays[position + '_mlx_due_edges'] = observed.mlx_due_edges
        snapshot = observed.snapshot
        arrays[position + '_reference_spikes'] = snapshot.spikes
        arrays[position + '_reference_source_spikes'] = snapshot.source_spikes
        for path, pathway in enumerate(snapshot.pathways):
            arrays[f'{position}_reference_path_{path}_delivered'] = pathway.delivered
            arrays[f'{position}_reference_path_{path}_offset'] = np.array([pathway.queues[0].offset], dtype=np.int32)
            for slot, value in enumerate(pathway.queues[0].slots):
                arrays[f'{position}_reference_path_{path}_slot_{slot}'] = value
        observations.append({'position': position, 'step': snapshot.step, 'clock_step': snapshot.clock_step, 'time_s': snapshot.time_s, 'source_cursor': snapshot.source_cursor, 'mlx_due_sha256': observed.mlx_due_sha256})
    weights = np.memmap(output / f'reference-{trial}-results' / jobs[trial].files['weights'], mode='r', dtype=np.float64)
    reductions = []
    for neuron in context.neurons:
        for bucket in execution.advance.args[1].buckets:
            matches = np.flatnonzero(np.asarray(bucket.targets) == neuron)
            if not len(matches):
                continue
            row = int(matches[0])
            with mx.stream(mx.gpu):
                ids, counts, occupied = (np.asarray(value[row]) for value in (bucket.edge_ids, bucket.counts, bucket.occupied))
            arrays[f'neuron_{neuron}_actual_leaf_edges'] = ids
            arrays[f'neuron_{neuron}_actual_leaf_counts'] = counts
            arrays[f'neuron_{neuron}_actual_leaf_occupied'] = occupied
            arrays[f'neuron_{neuron}_native_reference_weights_si'] = weights[ids[occupied]]
            reductions.append({'neuron': neuron, 'neuron_id': int(connectome.neuron_ids[neuron]), 'padded_width': len(ids), 'reference_threshold_margin_mv': (float(context.current.reference['pre_v'][neuron]) + 0.045) * 1000, 'mlx_threshold_margin_mv': float(context.current.mlx['pre_v'][neuron]) + 45})
    with (output / f'trial-{trial}-{label}-context.npz').open('xb') as artifact:
        np.savez_compressed(artifact, **arrays)
    return {'neurons': list(context.neurons), 'observations': observations, 'reductions': reductions, 'reduction_order': 'Actual padded leaves and adjacent-pair compensated integer-count tree; four high/low scale products; 16-leaf compensated final tree.'}


sampler = threading.Thread(target=sample_memory, daemon=True)
sampler.start()
mx.reset_peak_memory()
beginning = time.perf_counter()
try:
    with ExitStack() as stack:
        references = [stack.enter_context(closing(run(job, output / f'reference-{trial}-results'))) for trial, job in enumerate(jobs)]
        mlx = stack.enter_context(closing(observe(execution, core.initial_state(execution.network, 4), events, EventLedger(connectome, stimulus.targets, 4))))
        for block in mlx:
            paired = [read_block(references[trial], trial_block(block, trial), ledgers[trial]) for trial in range(4)]
            for trial, frame in enumerate(paired):
                captures[trial].check(frame)
            independent = sole['blocks'][len(blocks)]
            assert paired[0].native_sha256[1] == independent['mlx_native_phase_sha256']
            assert paired[0].mlx.queue_sha256 == tuple(independent['mlx_queue_sha256'])
            assert [list(row) for row in paired[0].mlx.due_sha256] == independent['mlx_due_sha256']
            blocks.append({'begin': block.begin, 'rows': block.rows, 'native_phase_sha256': [frame.native_sha256 for frame in paired], 'actual_queue_sha256': block.queue_sha256, 'actual_due_sha256': block.due_sha256, 'independent_trial_0_all_raw_fields_queues_and_due_masks_identical': True})
            if block.begin == 0 or (block.begin + block.rows) % 256 == 0:
                print(json.dumps({'phase': 'progress', 'steps': block.begin + block.rows, 'seconds': time.perf_counter() - beginning, 'sampled_rss_sum_peak_bytes': max(sample['rss_sum_bytes'] for sample in memory)}), flush=True)
            if block.final_queue is not None:
                final_fields = {name: value[-1].copy() for name, value in block.fields.items()}
                final_fields['queue'] = block.final_queue
            del paired, frame, block
        finals = [finish_reference(references[trial], ledgers[trial]) for trial in range(4)]
    execution_s = time.perf_counter() - beginning
    with (output / 'batch-final.npz').open('xb') as artifact:
        np.savez_compressed(artifact, **final_fields)
    trials = []
    for trial, final in enumerate(finals):
        native = results(jobs[trial], output / f'reference-{trial}-results')
        assert all(value.tobytes() == native[name].tobytes() for name, value in final.fields.items())
        assert captures[trial].audit.step == 1000
        with (output / f'reference-{trial}-native.npz').open('xb') as artifact:
            np.savez_compressed(artifact, **native)
        trials.append({'trial': trial, 'reference_spikes': len(native['spike_i']), 'first_budget_violation': asdict(captures[trial].audit.first_budget_violation) if captures[trial].audit.first_budget_violation else None, 'first_spike_step': captures[trial].audit.first_spike_step, 'first_spike_neurons': captures[trial].audit.first_spike_neurons, 'budget_context': save_context(trial, 'budget', captures[trial].budget), 'spike_context': save_context(trial, 'spike', captures[trial].spike), 'reference_native': {name: raw(value) for name, value in native.items()}})
finally:
    done.set()
    sampler.join(timeout=5)
assert len(blocks) == 32 and sum(block['rows'] for block in blocks) == 1000
assert any(len(sample['processes']) == 5 for sample in memory)
report = {'implementation_commit': checkpoint, 'scope': 'Complete 0.1-second four-trial sugar memory qualification with four independent continuously streamed references and actual device/queue auditing. Trial 0 matches its separately qualified sole execution exactly. No four-trial repeat or independent trials 1-3, one-second batch gate, PyTorch baseline, or full-matrix acceptance is implied.', 'neurons': pin.neurons, 'edges': pin.edges, 'steps': 1000, 'trial_indices': [0, 1, 2, 3], 'stimulus_sha256': stimulus.sha256, 'trial_stimulus_sha256': [hashlib.sha256(trial.tobytes()).hexdigest() for trial in events], 'execution_s': execution_s, 'mlx_allocator_peak_bytes': mx.get_peak_memory(), 'sampled_rss_sum_peak_bytes': max(sample['rss_sum_bytes'] for sample in memory), 'memory_scope': 'Sampled RSS sum for this Python proof process and its four direct reference children after load/compilation/prepare return, including fresh state, execution and collection. Shared pages can be counted twice. MLX allocator is separate; this is not total system/unified memory.', 'blocks': blocks, 'trials': trials, 'final_native_mlx': {name: raw(value) for name, value in final_fields.items()}, 'memory_samples': memory, 'total_seconds': time.perf_counter() - started}
with (output / 'four-trial-memory.json').open('x') as artifact:
    json.dump(report, artifact, indent=2)
    artifact.write('\n')
print(json.dumps({'completed': True, 'execution_s': execution_s, 'sampled_rss_sum_peak_bytes': report['sampled_rss_sum_peak_bytes'], 'trials': [{'trial': trial['trial'], 'first_spike_step': trial['first_spike_step'], 'first_budget_violation': trial['first_budget_violation']} for trial in trials]}), flush=True)
