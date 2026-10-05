import hashlib
import json
import signal
import statistics
import subprocess
import time
from pathlib import Path

import mlx.core as mx
import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import phase_fields, queue_hashes
from fly_brain.qualification.adapters.paired_observer import phase_hash
from fly_brain.simulation.backend import bucketed, core

ROOT = Path('/Users/ocasta/Code/fly-brain')
CASE = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01'
OUT = Path('/private/tmp/fly-brain-mlx-component-performance-20261005-01')
OUT.mkdir(exist_ok=False)
signal.alarm(90)
started = time.perf_counter()
connectome, pin = pinned_inputs(ROOT)
targets = tuple(json.loads((CASE / 'stimulus.json').read_text())['targets'])
execution = bucketed.prepare(connectome, targets, (), '0')
network, layout = execution.advance.args
with np.load(CASE / 'observations/paired-first/mlx-native.npz', allow_pickle=False) as saved:
    with mx.stream(mx.gpu):
        state = core.State(mx.array(saved['end_v'][None]), mx.array(saved['end_g'][None]), mx.array(saved['end_last_spike_step'][None]), mx.array(saved['queue']), 10000)
    spike_steps = saved['spike_steps'].copy()
    spike_neurons = saved['spike_neurons'].copy()
with mx.stream(mx.gpu):
    inputs = mx.array(np.zeros((1, len(targets)), dtype=np.bool_))
    mx.eval(*state[:-1], inputs, network.sources, network.destinations, network.input_targets)
    updated, trace = execution.advance(state, inputs)
    fields = phase_fields(updated, trace)
    mx.eval(*updated[:-1], *fields.values(), *trace)
    base_ledger = EventLedger(connectome, targets, 1, np.asarray(state.last_spike_step))
    history = [None] * 19
    for step in range(9981, 10000):
        row = np.zeros((1, pin.neurons), dtype=np.bool_)
        row[0, spike_neurons[spike_steps == step]] = True
        history[step % 19] = mx.array(row)
    base_last = base_ledger.last
    mx.eval(base_last, *history, base_ledger.sources, base_ledger.destinations, base_ledger.empty_edges)
setup_s = time.perf_counter() - started
print(json.dumps({'phase': 'prepared', 'setup_s': setup_s, 'endpoint_step': state.step, 'queue_bytes': state.queue.size}), flush=True)


def reset_ledger():
    base_ledger.step = state.step
    base_ledger.last = base_last
    base_ledger.history = list(history)
    return base_ledger


def measure_device(builder, repeats=5):
    samples = []
    with mx.stream(mx.gpu):
        mx.eval(*builder())
        for _ in range(repeats):
            begin = time.perf_counter()
            arrays = builder()
            built = time.perf_counter()
            mx.eval(*arrays)
            finished = time.perf_counter()
            samples.append({'graph_build_s': built - begin, 'synchronized_evaluation_s': finished - built, 'total_s': finished - begin})
    return {'samples': samples, 'median_graph_build_s': statistics.median(s['graph_build_s'] for s in samples), 'median_synchronized_evaluation_s': statistics.median(s['synchronized_evaluation_s'] for s in samples), 'median_total_s': statistics.median(s['total_s'] for s in samples)}


def production_step():
    new, phase = execution.advance(state, inputs)
    return [*new[:-1], phase.spikes]


def observed_step():
    new, phase = execution.advance(state, inputs)
    flags = reset_ledger().check(new, phase, inputs)
    return [*new[:-1], *phase_fields(new, phase).values(), flags]


def dense_queue_update():
    slots = mx.arange(core.QUEUE_SLOTS)[:, None, None]
    queue = mx.where(slots == state.step % core.QUEUE_SLOTS, False, state.queue)
    return [mx.where(slots == (state.step + core.DELAY_STEPS) % core.QUEUE_SLOTS, trace.spikes[:, network.sources][None, :, :], queue)]


def ledger_only():
    return [reset_ledger().check(updated, trace, inputs)]


def input_channel_updates():
    voltage = trace.pre_voltage_mv
    neurons = mx.arange(network.neurons)
    for channel in range(network.input_targets.size):
        target = neurons == network.input_targets[channel]
        voltage = mx.where(trace.accepted_inputs[:, channel, None] & target, voltage + 68.75, voltage)
    return [voltage]


with mx.stream(mx.gpu):
    flags = ledger_only()[0]
    mx.eval(flags)
    assert np.asarray(flags).all()
    queue_check = dense_queue_update()[0]
    mx.eval(queue_check)
    assert np.asarray(queue_check).tobytes() == np.asarray(updated.queue).tobytes()
device_results = {}
builders = {
    'unchanged_full_production_step': production_step,
    'unchanged_full_observed_step': observed_step,
    'dense_two_selection_queue_update': dense_queue_update,
    'compensated_bucket_accumulation_output': lambda: [bucketed.accumulate(layout, trace.accepted, trace.pre_synaptic_mv)[0]],
    'independent_ledger_on_evaluated_step': ledger_only,
    'twenty_one_full_neuron_input_channel_updates': input_channel_updates,
    'neuron_integrate': lambda: list(core.integrate(state.voltage_mv, state.synaptic_mv, trace.available)),
}
for name, builder in builders.items():
    device_results[name] = measure_device(builder)
    print(json.dumps({'phase': 'device_component', 'name': name, 'median_total_s': device_results[name]['median_total_s'], 'median_graph_build_s': device_results[name]['median_graph_build_s']}), flush=True)

queue = np.asarray(updated.queue)
due = np.asarray(trace.due)
block = {name: np.stack([np.asarray(value)] * 32) for name, value in fields.items()}
host_builders = {
    'due_mask_hash_and_nonzero_scan': lambda: (hashlib.sha256(memoryview(due[0])).hexdigest(), np.flatnonzero(due[0]).astype(np.int32)),
    'complete_queue_hash': lambda: queue_hashes(queue),
    'native_phase_block_hash_including_tobytes': lambda: phase_hash(block),
}
host_results = {}
for name, operation in host_builders.items():
    operation()
    durations = []
    for _ in range(5):
        before = time.perf_counter()
        operation()
        durations.append(time.perf_counter() - before)
    host_results[name] = {'seconds': durations, 'median_s': statistics.median(durations)}
    print(json.dumps({'phase': 'host_component', 'name': name, 'median_s': host_results[name]['median_s']}), flush=True)

record = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'scope': 'Bounded components of unchanged MLX execution. Repeated single-step evaluation from retained final state at step 10000 with zero next inputs; not a new accepted case or model change.',
    'decision_confidence_percent': 95,
    'mlx_device': mx.device_info(), 'precision': 'MLX_ENABLE_TF32=0', 'compilation': 'disabled',
    'neurons': pin.neurons, 'edges': pin.edges, 'setup_s': setup_s,
    'endpoint_step': 10000, 'endpoint_firing_neurons': int(np.asarray(trace.spikes).sum()), 'endpoint_due_edges': int(due.sum()),
    'all_thirty_independent_ledger_checks_pass_on_probed_step': True,
    'separate_queue_expression_equals_unchanged_step_native_bytes': True,
    'device_components': device_results, 'host_components': host_results,
    'host_logical_scan_bytes': {'due': due.nbytes, 'queue': queue.nbytes, 'phase_block': sum(v.nbytes for v in block.values())},
    'elapsed_s': time.perf_counter() - started,
    'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'src/fly_brain/simulation/backend/bucketed.py', ROOT / 'src/fly_brain/simulation/backend/core.py', ROOT / 'src/fly_brain/qualification/adapters/mlx_ledger.py', ROOT / 'src/fly_brain/qualification/adapters/mlx_observer.py', ROOT / 'src/fly_brain/qualification/adapters/paired_observer.py')},
    'input_artifact_sha256': hashlib.sha256((CASE / 'observations/paired-first/mlx-native.npz').read_bytes()).hexdigest(),
    'application_changed': False, 'new_full_case_or_matrix_run': False, 'p9_resumed': False,
    'limits': 'Synchronized component timings include frontend dispatch, allocation and execution. Components use evaluated inputs and cannot be summed into a whole-step profile. Five samples from one preserved endpoint are not a representative horizon, a GPU hardware trace, acceptance, or a measured whole-run speedup. Phase block hash uses 32 copies of this single endpoint solely for byte-volume timing.',
}
with (OUT / 'result.json').open('x') as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'completed': True, 'elapsed_s': record['elapsed_s'], 'result': str(OUT / 'result.json')}), flush=True)
