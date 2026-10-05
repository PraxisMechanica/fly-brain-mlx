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
OUT = Path('/private/tmp/fly-brain-mlx-optimized-components-20261005-01')
OUT.mkdir(exist_ok=False)
signal.alarm(180)
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

from dataclasses import replace
from fly_brain.simulation.mapping import absolute_count_sums
assert np.all(absolute_count_sums(connectome) <= 2**24)
candidate_layout = replace(layout, exact_counts=True)
original_ledger_source = subprocess.check_output(['git','show','7e702c6:src/fly_brain/qualification/adapters/mlx_ledger.py'],cwd=ROOT,text=True)
(OUT / 'original-ledger.py').write_text(original_ledger_source)
namespace = {'__name__': 'private_original_ledger'}
exec(compile(original_ledger_source, 'private_original_ledger.py','exec'),namespace)
old_ledger = namespace['EventLedger'](connectome,targets,1,np.asarray(state.last_spike_step))
old_last = old_ledger.last

def reset_old():
    old_ledger.step = state.step
    old_ledger.last = old_last
    old_ledger.history = list(history)
    return old_ledger

def candidate_step():
    new, phase = bucketed.advance(network,candidate_layout,state,inputs)
    return [*new[:-1],phase.spikes]

def original_observed():
    new, phase = execution.advance(state,inputs)
    flags = reset_old().check(new,phase,inputs)
    return [*new[:-1],*phase_fields(new,phase).values(),flags]

def optimized_observed():
    new, phase = bucketed.advance(network,candidate_layout,state,inputs)
    flags = reset_ledger().check(new,phase,inputs)
    return [*new[:-1],*phase_fields(new,phase).values(),flags]

with mx.stream(mx.gpu):
    candidate_state,candidate_trace = bucketed.advance(network,candidate_layout,state,inputs)
    old_flags = reset_old().check(updated,trace,inputs)
    new_flags = reset_ledger().check(candidate_state,candidate_trace,inputs)
    mx.eval(*candidate_state[:-1],*candidate_trace,old_flags,new_flags)
    assert np.asarray(old_flags).all() and np.asarray(new_flags).all()
    for name,left,right in zip(('voltage','synaptic','last','queue'),updated[:-1],candidate_state[:-1],strict=True):
        assert np.asarray(left).tobytes() == np.asarray(right).tobytes(),name
    for left,right in zip(trace,candidate_trace,strict=True):
        assert np.asarray(left).tobytes() == np.asarray(right).tobytes()
    assert np.asarray(old_flags).tobytes() == np.asarray(new_flags).tobytes()

builders = {
 'original_production_step':production_step,
 'exact_count_production_step':candidate_step,
 'original_observed_step':original_observed,
 'exact_count_vector_ledger_observed_step':optimized_observed,
 'original_compensated_accumulation':lambda:[bucketed.accumulate(layout,trace.accepted,trace.pre_synaptic_mv)[0]],
 'exact_count_accumulation':lambda:[bucketed.accumulate(candidate_layout,trace.accepted,trace.pre_synaptic_mv)[0]],
 'original_independent_ledger':lambda:[reset_old().check(updated,trace,inputs)],
 'vector_independent_ledger':ledger_only,
}
measurements = {}
for name,builder in builders.items():
    measurements[name] = measure_device(builder,7)
    print(json.dumps({'component':name,'median_s':measurements[name]['median_total_s']}),flush=True)
record = {
 'checkpoint':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
 'device':mx.device_info(),'compilation':'disabled','MLX_ENABLE_TF32':'0',
 'scope':'Repeated unchanged endpoint at step10000; candidate count mode explicitly active. Synchronized components overlap and cannot be summed into whole-check time.',
 'same_native_state_trace_and_all_thirty_flags':True,
 'absolute_integer_count_bound':int(absolute_count_sums(connectome).max()),
 'measurements':measurements,'elapsed_s':time.perf_counter()-started,
 'endpoint_sha256':hashlib.sha256((CASE/'observations/paired-first/mlx-native.npz').read_bytes()).hexdigest(),
 'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'src/fly_brain/simulation/backend/bucketed.py',ROOT/'src/fly_brain/simulation/backend/accumulation.py',ROOT/'src/fly_brain/qualification/adapters/mlx_ledger.py')},
 'original_ledger_source_sha256':hashlib.sha256(original_ledger_source.encode()).hexdigest(),
 'limits':'Single endpoint and seven samples per component; not full native trajectory qualification, acceptance or measured end-to-end speedup. Candidate remains disabled in normal execution.',
}
(OUT/'result.json').write_text(json.dumps(record,indent=2)+'\n')
signal.alarm(0)
print(json.dumps({'completed':True,'elapsed_s':record['elapsed_s'],'output':str(OUT)}),flush=True)
