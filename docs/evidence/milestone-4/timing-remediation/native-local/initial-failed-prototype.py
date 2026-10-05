import hashlib
import io
import json
import math
import os
import platform
import sys
import zipfile
from pathlib import Path

import mlx.core as mx
import numpy as np

from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.accumulation import factored_sum
from fly_brain.simulation.backend.arrays import as_host

ROOT = Path('/Users/ocasta/Code/fly-brain')
EVIDENCE = ROOT / 'docs/evidence/milestone-4'
D = float(np.float32(math.expm1(-core.DT_MS / 20)))


def integrate(voltage_mv, synaptic_mv, available):
    _, b, c = core.COEFFICIENTS
    with mx.stream(mx.gpu):
        voltage = voltage_mv + (D * (voltage_mv + 52) + c * synaptic_mv)
        synaptic = b * synaptic_mv
        return mx.where(available, voltage, voltage_mv), mx.where(
            available, synaptic, synaptic_mv
        )


def main():
    assert __debug__
    assert os.environ['MLX_ENABLE_TF32'] == '0'
    assert mx.metal.is_available()
    assert np.__version__ == '1.26.4'
    mx.disable_compile()
    output = Path(sys.argv[1]).resolve()
    decision = json.loads(
        (EVIDENCE / 'timing-remediation/review-decision.json').read_text()
    )
    assert decision['d'] == D == -0.004987520631402731
    cause = EVIDENCE / 'one-second-sugar-cause'
    proof = json.loads((cause / 'parent-host-proof.json').read_text())
    host = json.loads(
        (EVIDENCE / 'timing-remediation/parent-host-diagnostic.json').read_text()
    )
    archive_path = cause / 'first-observation.zip'
    assert (
        hashlib.sha256(archive_path.read_bytes()).hexdigest() == proof['archive_sha256']
    )
    with zipfile.ZipFile(archive_path) as archive:
        causal = json.loads(archive.read('observations/paired-first/causal.json'))
        with np.load(
            io.BytesIO(archive.read('observations/paired-first/spike-context.npz'))
        ) as saved:
            arrays = {name: saved[name] for name in saved.files}
    for name, descriptor in causal['contexts']['spike']['arrays'].items():
        value = arrays[name]
        assert descriptor == {
            'dtype': value.dtype.str,
            'shape': list(value.shape),
            'sha256': hashlib.sha256(value.tobytes()).hexdigest(),
        }
    counts = arrays['neuron_100750_actual_mlx_leaf_counts']
    assert counts.dtype == np.float32 and counts.shape == (256,)
    events = {
        event['step']: event for event in proof['local_reconstruction']['event_rows']
    }
    traces = {}
    for label, update in (
        ('original', core.integrate),
        ('candidate', integrate),
        ('candidate-repeat', integrate),
    ):
        fields = {
            name: []
            for name in (
                'step',
                'available',
                'spikes',
                'receiving',
                'pre_v',
                'pre_g',
                'before_v',
                'before_g',
                'end_v',
                'end_g',
                'count_high',
                'count_low',
            )
        }
        with mx.stream(mx.gpu):
            v, g = mx.array([-52], dtype=mx.float32), mx.array([0], dtype=mx.float32)
            for step in range(5493, 5720):
                available = mx.array([step - 5492 >= 22])
                v, g = update(v, g, available)
                spikes = core.threshold_spikes(v, available)
                receiving = available & ~spikes
                event = events.get(step)
                leaves = np.zeros((1, 256), dtype=np.float32)
                if event is not None:
                    leaves[0, event['leaf_positions']] = counts[event['leaf_positions']]
                    assert bool(as_host(receiving)[0]) == event['accepted']
                summed, high, low = factored_sum(
                    mx.where(receiving[:, None], mx.array(leaves), 0), g
                )
                observed = {
                    'available': available,
                    'spikes': spikes,
                    'receiving': receiving,
                    'pre_v': v,
                    'pre_g': g,
                    'before_v': v,
                    'before_g': summed,
                    'count_high': high,
                    'count_low': low,
                }
                v, g = mx.where(spikes, -52, v), mx.where(spikes, 0, summed)
                observed.update({'end_v': v, 'end_g': g})
                fields['step'].append(step)
                for name, value in observed.items():
                    actual = as_host(value)
                    assert actual.dtype == (
                        np.bool_
                        if name in ('available', 'spikes', 'receiving')
                        else np.float32
                    )
                    fields[name].append(actual.copy())
        traces[label] = {
            name: np.asarray(values, dtype=np.int32)
            if name == 'step'
            else np.stack(values)
            for name, values in fields.items()
        }
    for name in traces['candidate']:
        assert (
            traces['candidate'][name].tobytes()
            == traces['candidate-repeat'][name].tobytes()
        ), name
    for label in ('original', 'candidate'):
        trace = traces[label]
        assert int(trace['available'].sum()) == 206
        assert trace['step'][trace['spikes'][:, 0]].tolist() == (
            [] if label == 'original' else [5719]
        )
        assert (
            float(trace['pre_v'][-1, 0])
            == host['local_206_updates'][
                'original' if label == 'original' else 'increment'
            ]['pre_v_mv']
        )
        assert (
            float(trace['pre_g'][-1, 0])
            == host['local_206_updates'][
                'original' if label == 'original' else 'increment'
            ]['pre_g_mv']
        )
    for step, position in ((5718, 'previous'), (5719, 'current')):
        row = step - 5493
        for field in ('v', 'g'):
            assert (
                traces['original']['pre_' + field][row, 0].tobytes()
                == arrays[position + '_mlx_pre_' + field][100750].tobytes()
            )
    assert traces['candidate']['end_v'][-1, 0] == np.float32(-52)
    assert traces['candidate']['end_g'][-1, 0] == np.float32(0)
    vp, gp = arrays['previous_mlx_end_v'], arrays['previous_mlx_end_g']
    available = arrays['current_mlx_pre_not_refractory']
    _, b, c = core.COEFFICIENTS
    predicted = np.where(
        available,
        vp + ((np.float32(D) * (vp + np.float32(52))) + (np.float32(c) * gp)),
        vp,
    )
    predicted_g = np.where(available, np.float32(b) * gp, gp)
    with mx.stream(mx.gpu):
        candidate_v, candidate_g = integrate(
            mx.array(vp), mx.array(gp), mx.array(available)
        )
        native_v, native_g = as_host(candidate_v), as_host(candidate_g)
        native_mask = as_host(core.threshold_spikes(candidate_v, mx.array(available)))
    assert (
        native_v.dtype == native_g.dtype == np.float32 and native_mask.dtype == np.bool_
    )
    assert native_v.tobytes() == predicted.tobytes()
    assert native_g.tobytes() == predicted_g.tobytes()
    expected_mask = available & (predicted > np.float32(-45))
    assert native_mask.tobytes() == expected_mask.tobytes()
    reference_mask = available & (arrays['current_reference_pre_v'] > -0.045)
    changed = np.flatnonzero(native_mask != reference_mask).tolist()
    expected_diagnostic = next(
        row
        for row in host['all_neuron_one_step_from_actual_preceding_state']
        if row['method'] == 'increment'
    )
    assert changed == expected_diagnostic['changed_predicates_from_reference']
    output.mkdir(parents=True, exist_ok=False)
    artifact = output / 'native.npz'
    with artifact.open('xb') as destination:
        np.savez_compressed(
            destination,
            **{
                label.replace('-', '_') + '_' + name: value
                for label, fields in traces.items()
                for name, value in fields.items()
            },
            full_neuron_pre_v=native_v,
            full_neuron_pre_g=native_g,
            full_neuron_spikes=native_mask,
        )
    sources = (
        'simulation/backend/core.py',
        'simulation/backend/accumulation.py',
        'simulation/backend/arrays.py',
    )
    record = {
        'scope': 'Isolated native incoming-event trajectory and one-step diagnostic from the recorded preceding state; no free-running full case or production replacement.',
        'D': D,
        'local_steps': 227,
        'local_available_updates': 206,
        'original_reproduces_saved_native_context': True,
        'candidate_reproduces_reviewed_host_prediction': True,
        'candidate_local_first_spike': 5719,
        'candidate_fresh_repeat_exact': True,
        'full_neuron_single_step_native_equals_host': True,
        'single_step_does_not_repair_already_drifted_state': changed == [100750],
        'remaining_full_neuron_predicate_differences': changed,
        'candidate_pre_v_mv': float(traces['candidate']['pre_v'][-1, 0]),
        'candidate_reference_error_mv': float(traces['candidate']['pre_v'][-1, 0])
        - float(arrays['current_reference_pre_v'][100750]) * 1000,
        'prototype_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_sha256': {
            name: hashlib.sha256(
                (ROOT / 'src/fly_brain' / name).read_bytes()
            ).hexdigest()
            for name in sources
        },
        'cause_archive_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        'native_artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'device': mx.device_info(),
        'platform': platform.platform(),
        'MLX_ENABLE_TF32': os.environ['MLX_ENABLE_TF32'],
        'compilation': 'disabled',
        'full_case_accepted': False,
    }
    with (output / 'result.json').open('x') as destination:
        destination.write(json.dumps(record, indent=2, allow_nan=False) + '\n')
    print(json.dumps(record, indent=2, allow_nan=False), flush=True)


if __name__ == '__main__':
    main()
