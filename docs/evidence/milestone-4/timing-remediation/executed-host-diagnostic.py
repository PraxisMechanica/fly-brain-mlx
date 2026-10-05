import hashlib
import io
import json
import math
import runpy
import zipfile
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path('/Users/ocasta/Code/fly-brain')
CAUSE = ROOT / 'docs/evidence/milestone-4/one-second-sugar-cause'
METRIC = ROOT / 'docs/evidence/milestone-4/one-second-sugar-metric-failure'
F = np.float32
support = runpy.run_path(str(CAUSE / 'executed-host-proof.py'))
factored = support['factored']
tree = support['tree']
two_product = support['two_product']
two_sum = support['two_sum']
proof = json.loads((CAUSE / 'parent-host-proof.json').read_text())
decision = json.loads((CAUSE / 'review-decision.json').read_text())
for filename in ('parent-host-proof.json', 'executed-host-proof.py'):
    assert hashlib.sha256((CAUSE / filename).read_bytes()).hexdigest() == decision['bound_artifact_sha256'][filename]
preflight = json.loads((CAUSE / 'first-cause-preflight.json').read_text())
metric = json.loads((METRIC / 'first-metrics.json').read_text())
assert hashlib.sha256((CAUSE / 'first-observation.zip').read_bytes()).hexdigest() == preflight['archive_sha256']
assert hashlib.sha256((METRIC / 'first-native-spikes.npz').read_bytes()).hexdigest() == metric['saved_native_spikes_sha256']
with zipfile.ZipFile(CAUSE / 'first-observation.zip') as archive:
    arrays = np.load(io.BytesIO(archive.read('observations/paired-first/spike-context.npz')), allow_pickle=False)
    causal = json.loads(archive.read('observations/paired-first/causal.json'))
    for name, desc in causal['contexts']['spike']['arrays'].items():
        value = arrays[name]
        assert {'dtype': value.dtype.str, 'shape': list(value.shape), 'sha256': hashlib.sha256(value.tobytes()).hexdigest()} == desc

sp = np.load(METRIC / 'first-native-spikes.npz', allow_pickle=False)
rn, rs = sp['brian_spike_i'], sp['brian_integer_steps']
mn, ms = sp['mlx_spike_neurons'], sp['mlx_integer_steps']
assert np.array_equal(sp['brian_spike_t'], rs * 0.0001)
assert (len(rs), len(ms)) == (16752, 16665)

def groups(neurons, steps):
    result = defaultdict(list)
    for neuron, step in zip(neurons.tolist(), steps.tolist()):
        result[neuron].append(step)
    return {neuron: sorted(times) for neuron, times in result.items()}

def match(first, second, width):
    pairs = []
    for neuron in sorted(set(first) & set(second)):
        x, y = first[neuron], second[neuron]
        i = j = 0
        while i < len(x) and j < len(y):
            if abs(y[j] - x[i]) <= width:
                pairs.append((neuron, x[i], y[j]))
                i += 1
                j += 1
            elif x[i] < y[j]:
                i += 1
            else:
                j += 1
    return np.asarray(pairs, dtype=np.int64).reshape(-1, 3)

rg, mg = groups(rn, rs), groups(mn, ms)
pairs = match(rg, mg, 10)
assert len(pairs) == 13347
assert Fraction(2 * len(pairs), len(rs) + len(ms)) == Fraction(2966, 3713)
exact = match(rg, mg, 0)
one = match(rg, mg, 1)
bins = []
for begin in range(0, 10000, 1000):
    end = begin + 1000
    r = (rs >= begin) & (rs < end)
    m = (ms >= begin) & (ms < end)
    local = match(groups(rn[r], rs[r]), groups(mn[m], ms[m]), 10)
    global_ref = (pairs[:, 1] >= begin) & (pairs[:, 1] < end)
    bins.append({'begin': begin, 'end': end, 'reference': int(r.sum()), 'mlx': int(m.sum()), 'matches_both_in_bin': len(local), 'local_diagnostic_f1': 2 * len(local) / (r.sum() + m.sum()), 'global_matches_by_reference_bin': int(global_ref.sum()), 'global_match_lags': {str(lag): int(np.sum(global_ref & ((pairs[:, 2] - pairs[:, 1]) == lag))) for lag in range(-10, 11) if np.any(global_ref & ((pairs[:, 2] - pairs[:, 1]) == lag))}})
changed = []
for neuron in sorted(set(rg) | set(mg)):
    rt, mt = rg.get(neuron, []), mg.get(neuron, [])
    difference = set(rt).symmetric_difference(mt)
    if difference:
        changed.append((min(difference), neuron, len(rt), len(mt)))
changed.sort()
post_r, post_m = rs >= 5719, ms >= 5719
post_pairs = match(groups(rn[post_r], rs[post_r]), groups(mn[post_m], ms[post_m]), 10)
first_target = 100750

A = math.exp(-0.1 / 20)
B = math.exp(-0.1 / 5)
C = A * -math.expm1(-0.1 * (1 / 5 - 1 / 20)) / 3
D = math.expm1(-0.1 / 20)
a, b, c, d = map(F, (A, B, C, D))
ra = math.exp(-0.0001 / 0.02)
rb = math.exp(-0.0001 / 0.005)
rc = ((0.005 / (0.02 - 0.005)) * (-math.exp(0.0001 / 0.02) + math.exp(0.0001 / 0.005))) * ra * rb
rest = -0.052000000000000005
base = rest - rest * ra


def original(v, g):
    return F(F(F(-52) + F(a * F(v + F(52)))) + F(c * g))


def regrouped(v, g):
    return F(F(-52) + F(F(a * F(v + F(52))) + F(c * g)))


def increment(v, g):
    return F(v + F(F(d * F(v + F(52))) + F(c * g)))


def single_round_stored_coefficients(v, g):
    return F(-52 + float(a) * (float(v) + 52) + float(c) * float(g))


def single_round_unrounded_coefficients(v, g):
    return F(-52 + A * (float(v) + 52) + C * float(g))


methods = {'original': original, 'regrouped': regrouped, 'increment': increment, 'host_diagnostic_single_round_stored_coefficients': single_round_stored_coefficients, 'host_diagnostic_single_round_unrounded_coefficients': single_round_unrounded_coefficients}
events = {event['step']: event for event in proof['local_reconstruction']['event_rows']}
counts = arrays['neuron_100750_actual_mlx_leaf_counts']
ref_v, ref_g = rest, 0.0
states = {name: (F(-52), F(0)) for name in methods}
max_errors = {name: [0.0, 0.0] for name in methods}
spikes = {name: [] for name in methods}
records = {}
for step in range(5493, 5720):
    eligible = step - 5492 >= 22
    if eligible:
        ref_v, ref_g = base + (rc * ref_g + ra * ref_v), rb * ref_g
    for name, update in methods.items():
        v, g = states[name]
        if eligible:
            v, g = update(v, g), F(b * g)
        if eligible and v > F(-45):
            spikes[name].append(step)
        max_errors[name][0] = max(max_errors[name][0], abs(float(v) - ref_v * 1000))
        max_errors[name][1] = max(max_errors[name][1], abs(float(g) - ref_g * 1000))
        if step == 5719:
            records[name] = {'pre_v_mv': float(v), 'pre_g_mv': float(g), 'pre_v_error_mv': float(v) - ref_v * 1000, 'strict_predicate': bool(v > F(-45)), 'first_spike_in_local_window': spikes[name][0] if spikes[name] else None, 'max_pre_voltage_error_mv': max_errors[name][0], 'max_pre_synaptic_error_mv': max_errors[name][1]}
        event = events.get(step)
        leaves = np.zeros(256, dtype=np.float32)
        if event is not None and event['accepted']:
            leaves[event['leaf_positions']] = counts[event['leaf_positions']]
        g = factored(leaves, g)[0]
        states[name] = v, g
    if step in (5718, 5719):
        position = 'previous' if step == 5718 else 'current'
        assert ref_v == arrays[position + '_reference_pre_v'][first_target]
        assert ref_g == arrays[position + '_reference_pre_g'][first_target]
        assert states['original'][0].tobytes() == arrays[position + '_mlx_pre_v'][first_target].tobytes()
        assert states['original'][1].tobytes() == arrays[position + '_mlx_pre_g'][first_target].tobytes()
    event = events.get(step)
    if event is not None and event['accepted']:
        weight_by_row = dict(zip(event['rows'], event['native_weights_si']))
        for row in event['reference_delivery_order_rows']:
            ref_g += weight_by_row[row]
for name, times in spikes.items():
    assert times == ([] if name == 'original' else [5719]), (name, times)


single_step = []
vp = arrays['previous_mlx_end_v']
gp = arrays['previous_mlx_end_g']
vr = arrays['current_reference_pre_v'] * 1000
available = arrays['current_mlx_pre_not_refractory']
for name, update in methods.items():
    if name.startswith('host_'):
        predicted = (-52 + (float(a) if 'stored' in name else A) * (vp.astype(np.float64) + 52) + (float(c) if 'stored' in name else C) * gp.astype(np.float64)).astype(np.float32)
    else:
        predicted = update(vp, gp)
    predicted = np.where(available, predicted, vp)
    mask = available & (predicted > F(-45))
    rmask = available & (arrays['current_reference_pre_v'] > -0.045)
    if name == 'original':
        assert np.array_equal(predicted, arrays['current_mlx_pre_v'])
    single_step.append({'method': name, 'max_error_from_actual_preceding_state_mv': float(np.max(np.abs(predicted.astype(np.float64) - vr))), 'changed_predicates_from_reference': np.flatnonzero(mask != rmask).tolist(), 'local_target_predicate': bool(mask[first_target])})


# Host diagnostics only; the extra grid may leave the ordinary state envelope.
linear = []
for name, update in methods.items():
    v0, g0 = np.meshgrid(np.array([-256, -52, -45, 0, 256], dtype=np.float64), np.array([-1024, -100, 0, 100, 1024], dtype=np.float64))
    v, g = v0.astype(np.float32), g0.astype(np.float32)
    rv, gg = v0.copy(), g0.copy()
    maximum_v = maximum_g = 0.0
    maximum_normalized_trajectory_error = 0.0
    maximum_reference_voltage = 0.0
    for step in range(10000):
        if name.startswith('host_'):
            ca = float(a) if 'stored' in name else A
            cc = float(c) if 'stored' in name else C
            v = (-52 + ca * (v.astype(np.float64) + 52) + cc * g.astype(np.float64)).astype(np.float32)
        else:
            v = update(v, g)
        g = (b * g).astype(np.float32)
        rv, gg = -52 + A * (rv + 52) + C * gg, B * gg
        maximum_v = max(maximum_v, float(np.max(np.abs(v.astype(np.float64) - rv))))
        maximum_g = max(maximum_g, float(np.max(np.abs(g.astype(np.float64) - gg))))
        maximum_reference_voltage = max(maximum_reference_voltage, float(np.max(np.abs(rv))))
        maximum_normalized_trajectory_error = max(maximum_normalized_trajectory_error, float(np.max(np.abs(v.astype(np.float64) - rv) / (0.001 + 0.00001 * np.abs(rv)))), float(np.max(np.abs(g.astype(np.float64) - gg) / (0.001 + 0.00001 * np.abs(gg)))))
    linear.append({'method': name, 'states': v.size, 'steps': 10000, 'maximum_v_error_mv': maximum_v, 'maximum_g_error_mv': maximum_g, 'maximum_reference_abs_voltage_mv': maximum_reference_voltage, 'maximum_error_divided_by_trajectory_budget': maximum_normalized_trajectory_error})

existing_fixture = []
for name, update in methods.items():
    v = np.array([-52, -50, -100, -52, -52, -52], dtype=np.float32)
    g = np.array([0, 0, -100, 100, 1024, -1024], dtype=np.float32)
    rv, gg = v.astype(np.float64) * 0.001, g.astype(np.float64) * 0.001
    max_v = max_g = max_ratio = first_ratio = 0.0
    for step in range(10000):
        if name.startswith('host_'):
            ca = float(a) if 'stored' in name else A
            cc = float(c) if 'stored' in name else C
            v = (-52 + ca * (v.astype(np.float64) + 52) + cc * g.astype(np.float64)).astype(np.float32)
        else:
            v = update(v, g)
        g = (b * g).astype(np.float32)
        rv, gg = base + (rc * gg + ra * rv), rb * gg
        ev, eg = np.abs(v.astype(np.float64) - rv * 1000), np.abs(g.astype(np.float64) - gg * 1000)
        max_v, max_g = max(max_v, float(ev.max())), max(max_g, float(eg.max()))
        ratio = max(float(np.max(ev / (0.001 + 0.00001 * np.abs(rv * 1000)))), float(np.max(eg / (0.001 + 0.00001 * np.abs(gg * 1000)))))
        max_ratio = max(max_ratio, ratio)
        if step == 0:
            first_ratio = max(float(np.max(ev / (0.00002 + 0.000002 * np.abs(rv * 1000)))), float(np.max(eg / (0.00002 + 0.000002 * np.abs(gg * 1000)))))
    existing_fixture.append({'method': name, 'states': 6, 'steps': 10000, 'maximum_v_error_mv': max_v, 'maximum_g_error_mv': max_g, 'maximum_error_divided_by_trajectory_budget': max_ratio, 'maximum_first_step_error_divided_by_one_step_budget': first_ratio})

result = {'scope': 'Read-only native spike drift and host-only bounded arithmetic diagnostics; no engine, device, full-network simulation, requalification or acceptance.', 'numpy': np.__version__, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'evidence_sha256': {'spikes': metric['saved_native_spikes_sha256'], 'cause_archive': preflight['archive_sha256']}, 'spike_drift': {'ten_step_matches': len(pairs), 'exact_matches': len(exact), 'one_step_matches': len(one), 'post_first_fork': {'reference': int(post_r.sum()), 'mlx': int(post_m.sum()), 'matches': len(post_pairs), 'f1': 2 * len(post_pairs) / (post_r.sum() + post_m.sum())}, 'changed_neurons': len(changed), 'first_20_changed_neurons': changed[:20], 'first_target_spikes_reference': rg[first_target], 'first_target_spikes_mlx': mg[first_target], 'bins': bins}, 'coefficients': {'a': float(a), 'b': float(b), 'c': float(c), 'd_host_expm1_rounded_once': float(d), 'd_from_rounded_a': float(F(a - F(1))), 'a_error': float(a) - A, 'b_error': float(b) - B, 'c_error': float(c) - C, 'd_error': float(d) - D}, 'local_206_updates': records, 'all_neuron_one_step_from_actual_preceding_state': single_step, 'extra_linear_host_grid': linear, 'existing_six_state_host_fixture': existing_fixture, 'single_state_threshold_spacing_mv': float(np.nextafter(F(-45), F(0)) - F(-45)), 'minimum_additional_matches_if_counts_unchanged': (19 * (len(rs) + len(ms)) + 39) // 40 - len(pairs)}
print(json.dumps(result, indent=2, allow_nan=False))
