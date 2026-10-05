import hashlib
import io
import json
import math
import zipfile
from pathlib import Path

import numpy as np


ROOT = Path('/Users/ocasta/Code/fly-brain')
EVIDENCE = ROOT / 'docs/evidence/milestone-4/one-second-sugar-cause'
RUN = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01'
RESULTS = RUN / 'observations/paired-first/reference-results'
NEURON = 100750
FIRST_STEP = 5719
LAST_COMMON_SPIKE = 5492
ARCHIVE_SHA256 = '4c1daf70d48e97b8924e3e92f9f964e3c6b54a36f3f6dd0082d35d4ae20c29de'
AUXILIARY_SHA256 = {
    '_dynamic_array_default_synapses__synaptic_pre_3203942682':
        '8ec65c761057a2b000dcc246d6dc94a586b31596b8331c1db1ada61691d67f17',
    '_dynamic_array_default_synapses__synaptic_post_1892736623':
        '302786e9dacecf6f04683f7e46a6c3aa223b136b42b44880ccae0f0487dcd5f3',
    '_dynamic_array_default_synapses_w_937324336':
        'd5547fb81db7028cb949bf1e8a76b4d6808800f251c9b4255802c3188c22a51f',
}
F = np.float32


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read_npz(archive, member):
    return np.load(io.BytesIO(archive.read(member)), allow_pickle=False)


def two_sum(left, right):
    total = left + right
    recovered = total - left
    residual = (left - (total - recovered)) + (right - recovered)
    return total, residual


def tree(values):
    high, low = values, np.zeros_like(values)
    while len(high) > 1:
        total, residual = two_sum(high[::2], high[1::2])
        correction = (low[::2] + low[1::2]) + residual
        high, low = two_sum(total, correction)
    return high[0], low[0]


def split(value):
    expanded = F(4097) * value
    high = expanded - (expanded - value)
    return high, value - high


def two_product(left, right):
    product = left * right
    left_high, left_low = split(left)
    right_high, right_low = split(right)
    residual = left_low * right_low - (
        ((product - left_high * right_high) - left_low * right_high)
        - left_high * right_low
    )
    return product, residual


def factored(counts, initial):
    count_high, count_low = tree(counts)
    scale_high = F(0.275)
    scale_low = F(0.275 - float(scale_high))
    terms = [initial]
    for count in (count_high, count_low):
        for scale in (scale_high, scale_low):
            terms.extend(two_product(count, scale))
    terms.extend([F(0)] * 7)
    high, low = tree(np.asarray(terms, dtype=np.float32))
    result = (
        initial
        if count_high == 0 and count_low == 0
        else F(high + low)
    )
    return result, count_high, count_low, terms


def main():
    if not __debug__:
        raise RuntimeError('Run this diagnostic without Python optimization flags')
    preflight = json.loads((EVIDENCE / 'first-cause-preflight.json').read_text())
    archive_path = EVIDENCE / 'first-observation.zip'
    assert file_sha256(archive_path) == ARCHIVE_SHA256
    assert preflight['archive_sha256'] == ARCHIVE_SHA256
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == set(preflight['artifact_sha256'])
        for member, expected in preflight['artifact_sha256'].items():
            assert hashlib.sha256(archive.read(member)).hexdigest() == expected, member
        environment = json.loads(archive.read('environment.json'))
        assert np.__version__ == environment['versions']['numpy'] == '1.26.4'
        causal = json.loads(archive.read('observations/paired-first/causal.json'))
        assert causal['steps'] == 10000
        assert causal['first_spike_step'] == FIRST_STEP
        assert causal['first_spike_neurons'] == [NEURON]
        assert causal['first_budget_violation'] is None
        context = causal['contexts']['spike']
        assert context['neurons'] == [NEURON]
        assert causal['contexts']['budget'] is None
        arrays = read_npz(archive, 'observations/paired-first/spike-context.npz')
        reference = read_npz(archive, 'observations/paired-first/reference-native.npz')
        mlx = read_npz(archive, 'observations/paired-first/mlx-native.npz')
        stimulus = read_npz(archive, 'stimulus.npz')['events']
        stimulus_metadata = json.loads(archive.read('stimulus.json'))
        job = json.loads(archive.read('reference-job.json'))
        assert set(arrays.files) == set(context['arrays'])
        assert len(arrays.files) == 112
        for name, expected in context['arrays'].items():
            value = arrays[name]
            actual = {
                'dtype': value.dtype.str,
                'shape': list(value.shape),
                'sha256': hashlib.sha256(value.tobytes()).hexdigest(),
            }
            assert actual == expected, name
        phase_blocks = [
            json.loads(line)
            for line in archive.read(
                'observations/paired-first/phase-digests.jsonl'
            ).splitlines()
        ]
        physical = [
            json.loads(line)
            for line in archive.read(
                'observations/paired-first/physical-digests.jsonl'
            ).splitlines()
        ]
    assert [(row['begin'], row['rows']) for row in phase_blocks] == [
        (begin, min(32, 10000 - begin)) for begin in range(0, 10000, 32)
    ]
    assert [row['step'] for row in physical] == list(range(10001))
    assert int(arrays['affected_neuron_ids'][0]) == 720575940630820919

    native_hashes = {}
    for name, expected in AUXILIARY_SHA256.items():
        native_hashes[name] = file_sha256(RESULTS / name)
        assert native_hashes[name] == expected, name
    sources_all = np.memmap(
        RESULTS / '_dynamic_array_default_synapses__synaptic_pre_3203942682',
        dtype=np.int32, mode='r',
    )
    destinations = np.memmap(
        RESULTS / '_dynamic_array_default_synapses__synaptic_post_1892736623',
        dtype=np.int32, mode='r',
    )
    assert job['files']['weights'] == '_dynamic_array_default_synapses_w_937324336'
    weights = np.memmap(
        RESULTS / job['files']['weights'], dtype=np.float64, mode='r'
    )
    prefix = f'neuron_{NEURON}_'
    edges = arrays[prefix + 'actual_mlx_leaf_edges']
    counts = arrays[prefix + 'actual_mlx_leaf_counts']
    occupied = arrays[prefix + 'actual_mlx_leaf_occupied']
    native_weights = arrays[prefix + 'reference_native_weight_si']
    rows = edges[occupied]
    assert edges.shape == counts.shape == occupied.shape == (256,)
    assert np.array_equal(occupied, np.arange(256) < 152)
    assert np.array_equal(np.flatnonzero(destinations == NEURON), rows)
    assert np.all(np.diff(rows) > 0)
    assert np.all(edges[~occupied] == -1) and np.all(counts[~occupied] == 0)
    assert np.array_equal(weights[rows], native_weights)
    assert np.array_equal(
        native_weights, counts[occupied].astype(np.float64) * (0.275 * 0.001)
    )
    sources = sources_all[rows]
    assert len(np.unique(sources)) == 152
    assert np.max(np.abs(counts)) == 155
    assert np.abs(counts.astype(np.float64)).sum() == 941

    reference_steps = np.rint(reference['spike_t'] / 0.0001).astype(np.int64)
    reference_neurons = reference['spike_i']
    mlx_steps, mlx_neurons = mlx['spike_steps'], mlx['spike_neurons']
    assert np.max(np.abs(reference_steps * 0.0001 - reference['spike_t'])) <= 1e-12
    earlier_reference = reference_steps < FIRST_STEP
    earlier_mlx = mlx_steps < FIRST_STEP
    assert int(earlier_reference.sum()) == int(earlier_mlx.sum()) == 9723
    assert np.array_equal(reference_steps[earlier_reference], mlx_steps[earlier_mlx])
    assert np.array_equal(reference_neurons[earlier_reference], mlx_neurons[earlier_mlx])
    target_reference_steps = reference_steps[
        (reference_neurons == NEURON) & (reference_steps <= FIRST_STEP)
    ]
    assert target_reference_steps[-2:].tolist() == [LAST_COMMON_SPIKE, FIRST_STEP]
    assert mlx_steps[(mlx_neurons == NEURON) & earlier_mlx][-1] == LAST_COMMON_SPIKE
    assert NEURON not in arrays['stimulus_targets']
    assert stimulus.dtype == np.uint8 and stimulus.shape == (1, 10000, 21)
    assert hashlib.sha256(stimulus.tobytes()).hexdigest() == stimulus_metadata[
        'canonical_event_sha256'
    ]
    assert np.array_equal(arrays['stimulus_targets'], stimulus_metadata['targets'])

    rfc = np.fromfile(RESULTS / '_array_default_neurons_rfc_3473843883', dtype=np.float64)
    expected_rfc = np.full(138639, 2.2) * 0.001
    expected_rfc[arrays['stimulus_targets']] = 0
    assert np.array_equal(rfc, expected_rfc)
    refractory_steps = np.rint(rfc / 0.0001).astype(np.int64)
    previous_last = arrays['previous_mlx_end_last_spike_step']
    assert np.array_equal(
        np.rint(arrays['previous_reference_end_lastspike'] / 0.0001), previous_last
    )
    assert previous_last[NEURON] == LAST_COMMON_SPIKE
    assert np.array_equal(
        FIRST_STEP - previous_last >= refractory_steps,
        arrays['current_reference_pre_not_refractory'],
    )
    previous_spikers = arrays['previous_mlx_spikes']
    previous_nonspikers = ~previous_spikers
    previous_available = FIRST_STEP - 1 - previous_last >= refractory_steps
    assert np.array_equal(
        previous_available[previous_nonspikers],
        arrays['previous_reference_pre_not_refractory'][previous_nonspikers],
    )
    assert arrays['previous_reference_pre_not_refractory'][previous_spikers].all()
    assert not previous_spikers[NEURON] and previous_available[NEURON]

    boundary_checks, context_reductions, budget_checks = [], [], []
    for step, position in ((5718, 'previous'), (5719, 'current')):
        reference_spikes = np.zeros(138639, dtype=np.bool_)
        reference_spikes[arrays[position + '_reference_spikes']] = True
        reference_available = arrays[position + '_reference_pre_not_refractory']
        mlx_available = arrays[position + '_mlx_pre_not_refractory']
        assert np.array_equal(reference_available, mlx_available)
        assert np.array_equal(
            reference_spikes,
            reference_available & (arrays[position + '_reference_pre_v'] > -0.045),
        )
        assert np.array_equal(
            arrays[position + '_mlx_spikes'],
            mlx_available & (arrays[position + '_mlx_pre_v'] > F(-45)),
        )
        changed = np.flatnonzero(
            reference_spikes != arrays[position + '_mlx_spikes']
        ).tolist()
        assert changed == ([] if position == 'previous' else [NEURON])
        for phase in (('pre',) if position == 'current' else ('pre', 'before', 'end')):
            assert np.array_equal(
                arrays[f'{position}_reference_{phase}_not_refractory'],
                arrays[f'{position}_mlx_{phase}_not_refractory'],
            )
            for field in ('v', 'g'):
                expected = arrays[f'{position}_reference_{phase}_{field}'] * 1000
                actual = arrays[f'{position}_mlx_{phase}_{field}'].astype(np.float64)
                budget = 0.001 + 0.00001 * np.abs(expected)
                assert np.isfinite(expected).all() and np.isfinite(actual).all()
                assert np.all(np.abs(actual - expected) <= budget)
                budget_checks.append({
                    'position': position, 'phase': phase, 'field': field,
                    'maximum_error_mv': float(np.max(np.abs(actual - expected))),
                })
        snapshot = next(
            entry['actual_snapshot'] for entry in context['steps']
            if entry['position'] == position
        )
        assert snapshot['step'] == snapshot['clock_step'] == step
        assert snapshot['source_cursor'] == 2391
        assert float.fromhex(snapshot['time_s_hex']) == step * 0.0001
        for phase in ('pre', 'before', 'end'):
            assert arrays[f'{position}_reference_{phase}_t'].item() == step * 0.0001
        source_spikes = reference_neurons[reference_steps == step - 18]
        expected_delivery = np.concatenate([
            np.flatnonzero(sources_all == source) for source in source_spikes
        ]).astype(np.int32)
        assert np.array_equal(
            expected_delivery, arrays[position + '_reference_pathway_0_delivered']
        )
        assert np.array_equal(np.sort(expected_delivery), arrays[position + '_mlx_due_edges'])
        assert len(expected_delivery) == (834 if position == 'previous' else 68)
        assert np.intersect1d(expected_delivery, rows).size == 0
        offset = arrays[position + '_reference_pathway_0_queue_0_offset'].item()
        assert offset == (step + 1) % 19
        assert np.array_equal(
            expected_delivery,
            arrays[f'{position}_reference_pathway_0_queue_0_slot_{offset}'],
        )
        bits = arrays[position + '_stimulus_bits'].astype(np.bool_)
        assert np.array_equal(bits, stimulus[0, step].astype(np.bool_))
        targets = arrays['stimulus_targets']
        receiving = arrays[position + '_mlx_before_not_refractory'][targets]
        assert np.array_equal(bits & receiving, arrays[position + '_mlx_accepted_inputs'])
        assert np.array_equal(np.flatnonzero(bits), arrays[position + '_reference_source_spikes'])
        assert np.array_equal(
            arrays[position + '_reference_source_spikes'],
            arrays[position + '_reference_pathway_1_delivered'],
        )
        assert not arrays[position + '_mlx_accepted_inputs'].any()
        active = occupied & np.isin(edges, arrays[position + '_mlx_due_edges'])
        leaves = np.where(
            active & bool(arrays[position + '_mlx_before_not_refractory'][NEURON]),
            counts, F(0),
        ).astype(np.float32)
        initial = arrays[position + '_mlx_pre_g'][NEURON]
        result, high, low, terms = factored(leaves, initial)
        assert np.count_nonzero(leaves) == 0 and high == 0 and low == 0
        assert result.tobytes() == arrays[position + '_mlx_before_g'][NEURON].tobytes()
        context_reductions.append({
            'step': step, 'count_high': float(high), 'count_low': float(low),
            'count_leaf_count': len(leaves),
            'final_16_leaves': [float(value) for value in terms],
            'synaptic_result_native_bytes_match': True,
        })
        boundary_checks.append({
            'step': step, 'changed_neurons': changed,
            'source_step': step - 18, 'source_neurons': source_spikes.tolist(),
            'delivered_rows': len(expected_delivery), 'affected_due_rows': [],
            'input_channels': np.flatnonzero(bits).tolist(),
            'accepted_input_channels': [], 'source_cursor': snapshot['source_cursor'],
        })

    a = F(math.exp(-0.1 / 20))
    b = F(math.exp(-0.1 / 5))
    c = F(math.exp(-0.1 / 20) * -math.expm1(-0.1 * (1 / 5 - 1 / 20)) / 3)
    reference_a = math.exp(-0.0001 / 0.02)
    reference_b = math.exp(-0.0001 / 0.005)
    reference_c = (
        (0.005 / (0.02 - 0.005))
        * (-math.exp(0.0001 / 0.02) + math.exp(0.0001 / 0.005))
    ) * reference_a * reference_b
    reference_rest = -0.052000000000000005
    reference_base = reference_rest - reference_rest * reference_a
    voltage, synaptic = F(-52), F(0)
    reference_voltage, reference_synaptic = reference_rest, 0.0
    available_updates = 0
    maximum_voltage_error = maximum_synaptic_error = 0.0
    events, reconstructed_boundaries = [], []
    for step in range(LAST_COMMON_SPIKE + 1, FIRST_STEP + 1):
        eligible = step - LAST_COMMON_SPIKE >= 22
        if eligible:
            available_updates += 1
            voltage = F(F(F(-52) + F(a * F(voltage + F(52)))) + F(c * synaptic))
            synaptic = F(b * synaptic)
            reference_voltage, reference_synaptic = (
                reference_base + (reference_c * reference_synaptic + reference_a * reference_voltage),
                reference_b * reference_synaptic,
            )
        mlx_spike = eligible and bool(voltage > F(-45))
        reference_spike = eligible and reference_voltage > -0.045
        assert mlx_spike == np.any((mlx_steps == step) & (mlx_neurons == NEURON))
        assert reference_spike == np.any(
            (reference_steps == step) & (reference_neurons == NEURON)
        )
        if step in (5718, 5719):
            position = 'previous' if step == 5718 else 'current'
            assert voltage.tobytes() == arrays[position + '_mlx_pre_v'][NEURON].tobytes()
            assert synaptic.tobytes() == arrays[position + '_mlx_pre_g'][NEURON].tobytes()
            assert reference_voltage == arrays[position + '_reference_pre_v'][NEURON]
            assert reference_synaptic == arrays[position + '_reference_pre_g'][NEURON]
            reconstructed_boundaries.append({
                'step': step,
                'mlx_pre_v_mv': float(voltage), 'mlx_pre_g_mv': float(synaptic),
                'reference_pre_v_si': reference_voltage,
                'reference_pre_g_si': reference_synaptic,
                'all_four_native_values_exact': True,
            })
        maximum_voltage_error = max(
            maximum_voltage_error, abs(float(voltage) - reference_voltage * 1000)
        )
        maximum_synaptic_error = max(
            maximum_synaptic_error, abs(float(synaptic) - reference_synaptic * 1000)
        )
        due_sources = reference_neurons[reference_steps == step - 18]
        active = np.zeros(256, dtype=np.bool_)
        active[occupied] = np.isin(sources, due_sources)
        accepted = eligible and not mlx_spike
        leaves = np.where(active & accepted, counts, F(0)).astype(np.float32)
        synaptic, high, low, _ = factored(leaves, synaptic)
        ordered_positions = (
            np.concatenate([np.flatnonzero(sources == source) for source in due_sources])
            if len(due_sources) else np.empty(0, dtype=np.int64)
        )
        if eligible and not reference_spike:
            for position in ordered_positions:
                reference_synaptic += native_weights[position]
        if len(ordered_positions):
            events.append({
                'step': step, 'accepted': accepted,
                'leaf_positions': np.flatnonzero(active).tolist(),
                'rows': edges[active].tolist(), 'counts': counts[active].tolist(),
                'reference_delivery_order_rows': rows[ordered_positions].tolist(),
                'native_weights_si': native_weights[active[occupied]].tolist(),
                'count_high': float(high), 'count_low': float(low),
            })
        if mlx_spike:
            voltage, synaptic = F(-52), F(0)
        if reference_spike:
            reference_voltage, reference_synaptic = reference_rest, 0.0
    due_rows = sum(len(event['rows']) for event in events)
    accepted_rows = sum(len(event['rows']) for event in events if event['accepted'])
    assert available_updates == 206 and len(events) == 29
    assert due_rows == 31 and accepted_rows == 28 and due_rows - accepted_rows == 3
    assert maximum_voltage_error == 4.35863434518069e-05
    assert maximum_synaptic_error == 7.4177575157818865e-06

    voltage = arrays['previous_mlx_end_v'][NEURON]
    synaptic = arrays['previous_mlx_end_g'][NEURON]
    reference_voltage = arrays['previous_reference_end_v'][NEURON]
    reference_synaptic = arrays['previous_reference_end_g'][NEURON]
    parts = [
        F(voltage + F(52)), F(a * F(voltage + F(52))),
        F(F(-52) + F(a * F(voltage + F(52)))), F(c * synaptic),
    ]
    predicted_voltage, predicted_synaptic = F(parts[2] + parts[3]), F(b * synaptic)
    assert predicted_voltage.tobytes() == arrays['current_mlx_pre_v'][NEURON].tobytes()
    assert predicted_synaptic.tobytes() == arrays['current_mlx_pre_g'][NEURON].tobytes()
    predicted_reference_voltage = reference_base + (
        reference_c * reference_synaptic + reference_a * reference_voltage
    )
    predicted_reference_synaptic = reference_b * reference_synaptic
    assert predicted_reference_voltage == arrays['current_reference_pre_v'][NEURON]
    assert predicted_reference_synaptic == arrays['current_reference_pre_g'][NEURON]
    exact_a = math.exp(-0.1 / 20)
    exact_c = exact_a * -math.expm1(-0.1 * (1 / 5 - 1 / 20)) / 3
    exact_mlx_initial_update = -52 + exact_a * (float(voltage) + 52) + exact_c * float(synaptic)
    cast_coefficient_update = -52 + float(a) * (float(voltage) + 52) + float(c) * float(synaptic)
    decomposition = {
        'previous_voltage_error_mv': float(voltage) - reference_voltage * 1000,
        'previous_synaptic_error_mv': float(synaptic) - reference_synaptic * 1000,
        'propagated_state_error_mv':
            exact_a * (float(voltage) - reference_voltage * 1000)
            + exact_c * (float(synaptic) - reference_synaptic * 1000),
        'coefficient_error_mv': cast_coefficient_update - exact_mlx_initial_update,
        'operation_error_mv': float(predicted_voltage) - cast_coefficient_update,
        'observed_current_error_mv':
            float(predicted_voltage) - arrays['current_reference_pre_v'][NEURON] * 1000,
        'reference_generated_vs_stable_update_mv':
            (-52 + exact_a * (reference_voltage * 1000 + 52) + exact_c * reference_synaptic * 1000)
            - arrays['current_reference_pre_v'][NEURON] * 1000,
    }
    expected_decomposition = {
        'previous_voltage_error_mv': -4.069283942698121e-05,
        'previous_synaptic_error_mv': 6.6057229908267345e-06,
        'propagated_state_error_mv': -4.045726441092287e-05,
        'coefficient_error_mv': -1.207127340308034e-07,
        'operation_error_mv': 4.744381953969423e-08,
        'observed_current_error_mv': -4.053053332597756e-05,
        'reference_generated_vs_stable_update_mv': 0.0,
    }
    assert decomposition == expected_decomposition
    reference_mv = arrays['current_reference_pre_v'][NEURON] * 1000
    margin = float(reference_mv + 45)
    error = float(abs(reference_mv - float(predicted_voltage)))
    budget = float(0.001 + 0.00001 * abs(reference_mv))
    assert error == margin == 4.053053332597756e-05
    assert budget == 0.0014499995946946668 and error <= budget and abs(margin) <= budget

    output = {
        'verified': True,
        'scope': 'Host-only reproduction of the bounded first-cause review; no case acceptance or native replay claim.',
        'assignment_commit': '2c9fd6b19f094aa7674574ab8258eaf6594abdd3',
        'program_sha256': file_sha256(Path(__file__)),
        'archive_sha256': ARCHIVE_SHA256,
        'auxiliary_sha256': native_hashes,
        'numpy_version': np.__version__,
        'context_array_descriptors_verified': 112,
        'phase_blocks': len(phase_blocks), 'physical_snapshots': len(physical),
        'preceding_native_spikes_exact': int(earlier_reference.sum()),
        'first_step': FIRST_STEP, 'complete_affected_neurons': [NEURON],
        'reference_margin_mv': margin, 'voltage_error_mv': error, 'unchanged_budget_mv': budget,
        'corrected_clock_diagnostic': {
            'all_previous_end_clocks_agree': True,
            'current_pre_eligibility_from_previous_end_clocks_all_neurons': True,
            'previous_pre_eligibility_from_own_end_clocks_nonspikers_only': True,
            'previous_spikers_pre_availability_checked_directly': True,
            'reason': 'A neuron that fired in the previous step already has an updated end clock; that clock cannot reconstruct its own earlier pre-threshold eligibility.',
            'target_last_common_spike': LAST_COMMON_SPIKE,
            'target_refractory_steps': int(refractory_steps[NEURON]),
        },
        'boundary_checks': boundary_checks,
        'all_neuron_budget_checks': budget_checks,
        'layout': {'occupied_rows': len(rows), 'padded_leaves': len(edges), 'maximum_absolute_count': 155, 'sum_absolute_counts': 941},
        'context_reductions': context_reductions,
        'local_reconstruction': {
            'reset_step': LAST_COMMON_SPIKE, 'last_step': FIRST_STEP,
            'available_updates': available_updates, 'due_rows': due_rows,
            'discarded_rows': due_rows - accepted_rows, 'accepted_rows': accepted_rows,
            'maximum_pre_voltage_error_mv': maximum_voltage_error,
            'maximum_pre_synaptic_error_mv': maximum_synaptic_error,
            'saved_boundaries': reconstructed_boundaries,
            'event_rows': events,
        },
        'final_update': {
            'coefficients_float32': [float(a), float(b), float(c)],
            'voltage_parts_float32': [float(value) for value in parts],
            'voltage_mv': float(predicted_voltage), 'synaptic_mv': float(predicted_synaptic),
            'error_decomposition': decomposition,
        },
    }
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
