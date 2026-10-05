import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from contextlib import closing
from pathlib import Path

import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.brian_jobs import build, results, run
from fly_brain.qualification.adapters.observer_stream import FinalSnapshot, PhaseBlock, StepSnapshot
from fly_brain.qualification.adapters.reference_queues import ReferenceQueues
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.stimuli import generate


def raw(array):
    return {'dtype': array.dtype.str, 'shape': list(array.shape), 'sha256': hashlib.sha256(memoryview(array)).hexdigest()}


def physical(snapshot):
    return {'step': snapshot.step, 'clock_step': snapshot.clock_step, 'time_s_hex': snapshot.time_s.hex(), 'source_cursor': snapshot.source_cursor, 'spikes': raw(snapshot.spikes), 'source_spikes': raw(snapshot.source_spikes), 'pathways': [{'queues': [{'offset': queue.offset, 'slots': [raw(slot) for slot in queue.slots]} for queue in pathway.queues], 'delivered': raw(pathway.delivered)} for pathway in snapshot.pathways]}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


root = Path.cwd()
checkpoint = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
started = time.perf_counter()
connectome, pin = pinned_inputs(root)
stimulus = generate(connectome, EXPERIMENTS['sugar'], 1000, (0,))
events = stimulus.events[0]
with (output / 'stimulus.npz').open('xb') as artifact:
    np.savez_compressed(artifact, events=events, targets=np.asarray(stimulus.targets, dtype=np.int32))
jobs = {}
for name, size in (('ordinary', None), ('observed', 32)):
    beginning = time.perf_counter()
    print(json.dumps({'phase': 'compiling', 'mode': name}), flush=True)
    jobs[name] = build(connectome, stimulus.targets, (), events, output / (name + '-build'), size)
    print(json.dumps({'phase': 'compiled', 'mode': name, 'seconds': time.perf_counter() - beginning}), flush=True)
stock = jobs['ordinary'].directory
observed = jobs['observed'].directory
source_checks = []
for folder in ('code_objects', 'static_arrays'):
    for file in sorted((stock / folder).iterdir()):
        if folder == 'static_arrays' or file.suffix in ('.cpp', '.h'):
            first = hashlib.sha256(file.read_bytes()).hexdigest()
            second = hashlib.sha256((observed / folder / file.name).read_bytes()).hexdigest()
            assert first == second, file.name
            source_checks.append({'file': str(file.relative_to(stock)), 'sha256': first})
memory = []
done = threading.Event()


def sample_memory():
    while not done.is_set():
        text = subprocess.check_output(['ps', '-axo', 'pid=,ppid=,rss=,comm='], text=True)
        scoped = []
        for row in text.splitlines():
            columns = row.strip().split(None, 3)
            if len(columns) != 4:
                continue
            pid, parent, rss = map(int, columns[:3])
            if pid == os.getpid() or (parent == os.getpid() and Path(columns[3]).name == 'main'):
                scoped.append({'pid': pid, 'rss_bytes': rss * 1024, 'command': columns[3]})
        memory.append({'elapsed_s': time.perf_counter() - started, 'processes': scoped, 'rss_sum_bytes': sum(item['rss_bytes'] for item in scoped)})
        done.wait(0.25)


sampler = threading.Thread(target=sample_memory, daemon=True)
sampler.start()
records = {}
try:
    for mode in ('ordinary', 'observed', 'repeat'):
        job = jobs['ordinary' if mode == 'ordinary' else 'observed']
        destination = output / (mode + '-results')
        ledger = ReferenceQueues(connectome.sources, pin.neurons, events)
        snapshots, blocks, spike_steps, spike_neurons = [], [], [], []
        final = None
        beginning = time.perf_counter()
        print(json.dumps({'phase': 'executing', 'mode': mode}), flush=True)
        with closing(run(job, destination)) as frames:
            for frame in frames:
                if isinstance(frame, (StepSnapshot, FinalSnapshot)):
                    ledger.check(frame)
                    snapshot = frame.step if isinstance(frame, FinalSnapshot) else frame
                    snapshots.append(fingerprint(physical(snapshot)))
                    if isinstance(frame, StepSnapshot):
                        spike_steps.extend([frame.step] * len(frame.spikes))
                        spike_neurons.extend(frame.spikes.tolist())
                    else:
                        final = frame
                elif isinstance(frame, PhaseBlock):
                    expected_times = np.arange(frame.begin, frame.begin + frame.rows) * 0.0001
                    for name, values in frame.fields.items():
                        assert np.isfinite(values).all(), (mode, frame.begin, name)
                        if name.endswith('_t'):
                            assert np.max(np.abs(values - expected_times)) <= 1e-12, name
                    blocks.append({'begin': frame.begin, 'rows': frame.rows, 'fields': {name: raw(values) for name, values in frame.fields.items()}})
                    if (frame.begin + frame.rows) % 256 == 0:
                        print(json.dumps({'phase': 'observed', 'mode': mode, 'steps': frame.begin + frame.rows}), flush=True)
        native = results(job, destination)
        assert native['clock_step'].tolist() == [1000]
        assert np.isfinite(native['spike_t']).all()
        recovered = np.rint(native['spike_t'] / 0.0001).astype(np.int64)
        assert np.max(np.abs(native['spike_t'] - recovered * 0.0001), initial=0) <= 1e-12
        if job.observed:
            assert ledger.step == 1000 and final is not None
            assert len(blocks) == 32 and sum(block['rows'] for block in blocks) == 1000
            assert np.array_equal(recovered, np.asarray(spike_steps, dtype=np.int64))
            assert np.array_equal(native['spike_i'], np.asarray(spike_neurons, dtype=np.int32))
            for name, values in final.fields.items():
                assert values.tobytes() == native[name].tobytes(), name
            final_fields = dict(final.fields)
            for index, pathway in enumerate(final.step.pathways):
                final_fields[f'pathway_{index}_delivered'] = pathway.delivered
                for thread, queue in enumerate(pathway.queues):
                    final_fields[f'pathway_{index}_thread_{thread}_offset'] = np.asarray([queue.offset], dtype=np.int32)
                    for slot, values in enumerate(queue.slots):
                        final_fields[f'pathway_{index}_thread_{thread}_slot_{slot}'] = values
            with (output / (mode + '-observed-final.npz')).open('xb') as artifact:
                np.savez_compressed(artifact, **final_fields)
        with (output / (mode + '-native.npz')).open('xb') as artifact:
            np.savez_compressed(artifact, **native)
        records[mode] = {'seconds': time.perf_counter() - beginning, 'spikes': native['spike_i'].size, 'active_neurons': np.unique(native['spike_i']).size, 'native': {name: raw(values) for name, values in native.items()}, 'physical_snapshots': snapshots, 'phase_blocks': blocks}
        print(json.dumps({'phase': 'completed', 'mode': mode, 'seconds': records[mode]['seconds'], 'spikes': records[mode]['spikes']}), flush=True)
        del native, final, blocks, snapshots
finally:
    done.set()
    sampler.join(timeout=5)
assert records['ordinary']['native'] == records['observed']['native'] == records['repeat']['native']
assert records['observed']['physical_snapshots'] == records['repeat']['physical_snapshots']
assert records['observed']['phase_blocks'] == records['repeat']['phase_blocks']
assert memory and not sampler.is_alive()
report = {'implementation_commit': checkpoint, 'scope': 'Complete 0.1-second sugar reference observer transparency and fresh-process repeat only. No MLX/PyTorch paired parity, first-cause, or concurrent/four-trial memory acceptance.', 'neurons': pin.neurons, 'edges': pin.edges, 'steps': 1000, 'trials': [0], 'seed': stimulus.seed, 'generator_code': stimulus.generator_code, 'stimulus_sha256': stimulus.sha256, 'records': records, 'source_checks': source_checks, 'memory_scope': 'Sum of sampled resident set sizes for this Python proof process and its direct compiled reference child, after compilation. Shared pages can be counted twice. This is not total unified memory, system peak, or MLX/concurrent/four-trial memory.', 'sampled_rss_sum_peak_bytes': max(sample['rss_sum_bytes'] for sample in memory), 'memory_samples': memory, 'total_seconds': time.perf_counter() - started}
with (output / 'reference-observer.json').open('x') as artifact:
    json.dump(report, artifact, indent=2)
    artifact.write('\n')
print(json.dumps({'completed': True, 'spikes': records['ordinary']['spikes'], 'active_neurons': records['ordinary']['active_neurons'], 'sampled_rss_sum_peak_bytes': report['sampled_rss_sum_peak_bytes'], 'output': str(output)}), flush=True)
