import hashlib
import json
import math
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import as_host, boolean_input
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.models import Connectome, InputPin


def pulse_mode(
    connectome: Connectome,
    output: Path,
    source: int,
    blocked: int,
    silenced: tuple[int, ...],
    precision: str,
) -> dict[str, object]:
    execution = prepare(connectome, (), silenced, precision)
    network = execution.network
    outgoing = connectome.sources == source
    edges = np.flatnonzero(outgoing).astype(np.int32)
    tracked = np.unique(
        np.append(connectome.destinations[edges], [source, blocked])
    ).astype(np.int32)
    local_source = int(np.searchsorted(tracked, source))
    local_blocked = int(np.searchsorted(tracked, blocked))
    local_destinations = np.searchsorted(tracked, connectome.destinations[edges])
    weights = connectome.weights_mv[edges].copy()
    if silenced:
        weights[:] = 0
    neurons = connectome.neuron_ids.size
    voltage = np.full((2, neurons), -52.0)
    voltage[:, source] = -44
    last = np.full((2, neurons), core.INITIAL_LAST_SPIKE, dtype=np.int32)
    last[1, blocked] = 0
    state = core.initial_state(network, 2, voltage_mv=voltage, last_spike_step=last)
    expected_last = last.copy()
    expected_last[:, source] = 0
    available = np.ones((2, neurons), dtype=np.bool_)
    available[1, blocked] = False
    receiving = available.copy()
    receiving[:, source] = False
    source_spikes = np.zeros_like(available)
    source_spikes[:, source] = True
    due = np.broadcast_to(outgoing, (2, outgoing.size)).copy()
    accepted = due & receiving[:, connectome.destinations]
    discarded = due & ~receiving[:, connectome.destinations]
    with mx.stream(mx.gpu):
        for field, expected in (
            (network.sources, connectome.sources),
            (network.destinations, connectome.destinations),
            (
                network.weights_mv,
                np.where(
                    np.isin(connectome.sources, silenced), 0, connectome.weights_mv
                ).astype(np.float32),
            ),
            (network.refractory_steps, np.full(neurons, 22, dtype=np.int32)),
            (network.input_targets, np.array([], dtype=np.int32)),
        ):
            observed = as_host(field)
            assert observed.dtype == expected.dtype and observed.shape == expected.shape
            assert observed.tobytes() == expected.tobytes()
        device_tracked = mx.array(tracked)
        others = mx.array(
            np.flatnonzero(~np.isin(np.arange(neurons), tracked)).astype(np.int32)
        )
        device_last = mx.array(expected_last)
        device_available = boolean_input(available)
        device_receiving = boolean_input(receiving)
        device_spikes = boolean_input(source_spikes)
        device_due = boolean_input(due)
        device_accepted = boolean_input(accepted)
        device_discarded = boolean_input(discarded)
        pending = (mx.arange(core.QUEUE_SLOTS)[:, None, None] == 18) & device_due[
            None, :, :
        ]
        channels = mx.zeros((2, 0), dtype=mx.bool_)
        indices = mx.arange(neurons)
    reference_voltage = voltage[:, tracked].copy()
    reference_synaptic = np.zeros_like(reference_voltage)
    reference_last = last[:, tracked].copy()
    a, b = math.exp(-0.1 / 20), math.exp(-0.1 / 5)
    c = a * -math.expm1(-0.1 * (1 / 5 - 1 / 20)) / 3
    arrays: dict[
        str, list[NDArray[np.float32] | NDArray[np.float64] | NDArray[np.bool_]]
    ] = {}
    rows: list[dict[str, object]] = []
    first_conductance = first_voltage = None
    maximum_error = 0.0
    for step in range(20):
        reference_available = step - reference_last >= 22
        pre_voltage = np.where(
            reference_available,
            -52 + a * (reference_voltage + 52) + c * reference_synaptic,
            reference_voltage,
        )
        pre_synaptic = np.where(
            reference_available, b * reference_synaptic, reference_synaptic
        )
        spikes = reference_available & (pre_voltage > -45)
        np.testing.assert_array_equal(
            spikes, source_spikes[:, tracked] if step == 0 else False
        )
        reference_receiving = reference_available & ~spikes
        before_synaptic = pre_synaptic.copy()
        if step == 18:
            for trial in range(2):
                eligible = reference_receiving[trial, local_destinations]
                np.testing.assert_array_equal(eligible, accepted[trial, edges])
                np.add.at(
                    before_synaptic[trial],
                    local_destinations[eligible],
                    weights[eligible],
                )
        reference_last = np.where(spikes, step, reference_last)
        reference_voltage = np.where(spikes, -52, pre_voltage)
        reference_synaptic = np.where(spikes, 0, before_synaptic)
        state, trace = execution.advance(state, channels)
        with mx.stream(mx.gpu):
            checks = mx.stack(
                [
                    mx.all(
                        trace.available
                        == mx.where(indices == source, step == 0, device_available)
                    ),
                    mx.all(trace.spikes == (device_spikes if step == 0 else False)),
                    mx.all(trace.receiving == device_receiving),
                    mx.all(trace.due == (device_due if step == 18 else False)),
                    mx.all(
                        trace.accepted == (device_accepted if step == 18 else False)
                    ),
                    mx.all(
                        trace.discarded == (device_discarded if step == 18 else False)
                    ),
                    mx.all(state.queue == (pending if step < 18 else False)),
                    mx.all(state.last_spike_step == device_last),
                    mx.all(
                        state.voltage_mv[:, others].view(mx.uint32)
                        == mx.array(-52.0, dtype=mx.float32).view(mx.uint32)
                    ),
                    mx.all(state.synaptic_mv[:, others].view(mx.uint32) == 0),
                    mx.all(state.last_spike_step[:, others] == core.INITIAL_LAST_SPIKE),
                ]
            )
            flags = np.asarray(checks, dtype=np.bool_)
            assert flags.all(), (step, flags.tolist())
            for name, device, expected in (
                ('pre_voltage', trace.pre_voltage_mv, pre_voltage),
                ('pre_synaptic', trace.pre_synaptic_mv, pre_synaptic),
                ('before_reset_voltage', trace.before_reset_voltage_mv, pre_voltage),
                (
                    'before_reset_synaptic',
                    trace.before_reset_synaptic_mv,
                    before_synaptic,
                ),
                ('voltage', state.voltage_mv, reference_voltage),
                ('synaptic', state.synaptic_mv, reference_synaptic),
            ):
                actual = np.asarray(device[:, device_tracked], dtype=np.float32)
                error = np.abs(actual.astype(np.float64) - expected)
                assert np.isfinite(actual).all()
                assert np.all(error <= 1e-3 + 1e-5 * np.abs(expected))
                if step == 18 and name == 'before_reset_synaptic':
                    assert np.all(error <= 2e-5 + 2e-6 * np.abs(expected))
                maximum_error = max(maximum_error, float(error.max()))
                arrays.setdefault(name, []).append(actual)
                arrays.setdefault(f'reference_{name}', []).append(expected.copy())
            arrays.setdefault('complete_checks', []).append(flags)
        influenced = tracked != source
        if first_conductance is None and np.any(
            arrays['synaptic'][-1][:, influenced] != 0
        ):
            first_conductance = step
        if first_voltage is None and np.any(
            arrays['voltage'][-1][:, influenced] != -52
        ):
            first_voltage = step
        rows.append(
            {
                'step': step,
                'all_complete_masks_clocks_queues_and_unaffected_states_match': True,
                'due': int(due.sum()) if step == 18 else 0,
                'accepted': int(accepted.sum()) if step == 18 else 0,
                'discarded': int(discarded.sum()) if step == 18 else 0,
                'pending_events': int(due.sum()) if step < 18 else 0,
            }
        )
        print(
            f'Complete pulse {"silenced" if silenced else "original"}: step {step + 1}/20 passes',
            flush=True,
        )
    if silenced:
        assert first_conductance is None and first_voltage is None
    else:
        assert first_conductance == 18 and first_voltage == 19
    artifact = output / ('silenced.npz' if silenced else 'original.npz')
    with artifact.open('xb') as destination:
        np.savez_compressed(
            destination,
            **{name: np.stack(values) for name, values in arrays.items()},
            tracked=tracked,
            tracked_ids=connectome.neuron_ids[tracked],
            outgoing_edge_ids=edges,
            original_counts=connectome.counts[edges],
            original_weights64=connectome.weights_mv[edges],
            local_destinations=local_destinations,
            source=np.array(source),
            blocked=np.array(blocked),
            local_source=np.array(local_source),
            local_blocked=np.array(local_blocked),
        )
    return {
        'mode': 'outgoing-silenced' if silenced else 'original',
        'steps': 20,
        'trials': 2,
        'all_complete_checks_pass': True,
        'all_phase_state_budgets_pass': True,
        'arrival_one_step_budget_pass': True,
        'first_conductance_step': first_conductance,
        'first_voltage_influence_step': first_voltage,
        'max_phase_state_error_mv': maximum_error,
        'due_event_sha256': hashlib.sha256(due.tobytes()).hexdigest(),
        'accepted_event_sha256': hashlib.sha256(accepted.tobytes()).hexdigest(),
        'discarded_event_sha256': hashlib.sha256(discarded.tobytes()).hexdigest(),
        'measurements': rows,
        'artifact': artifact.name,
        'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
    }


def run(
    connectome: Connectome, pin: InputPin, output: Path, precision: str
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    assert precision == '0' and mx.metal.is_available()
    source = int(
        np.flatnonzero(
            np.bincount(connectome.sources, minlength=connectome.neuron_ids.size)
        )[0]
    )
    outgoing = connectome.sources == source
    destinations = connectome.destinations[outgoing]
    blocked = int(destinations[destinations != source][0])
    sums = np.zeros(connectome.neuron_ids.size, dtype=np.float64)
    np.add.at(sums, destinations, connectome.weights_mv[outgoing])
    coefficient = math.exp(-0.1 / 20) * -math.expm1(-0.1 * (1 / 5 - 1 / 20)) / 3
    assert float(sums.max()) * coefficient < 7
    modes = [
        pulse_mode(connectome, output, source, blocked, silenced, precision)
        for silenced in ((), (source,))
    ]
    report: dict[str, object] = {
        'accepted': True,
        'neurons': int(connectome.neuron_ids.size),
        'edges': int(connectome.counts.size),
        'source': source,
        'source_id': int(connectome.neuron_ids[source]),
        'blocked_target_in_trial_1': blocked,
        'outgoing_rows': int(outgoing.sum()),
        'modes': modes,
        'network_fields_round_trip_exactly': True,
        'complete_event_masks_and_queues_checked_each_step': True,
        'unaffected_neural_state_bits_exact_each_step': True,
        'reference': 'Independent analytic float64 update and ordered original-weight delivery for the controlled pulse; not live full-network Brian2.',
        'MLX_ENABLE_TF32': precision,
        'device': mx.device_info(),
        'compilation': 'disabled',
        'input_sha256': {
            'completeness': pin.completeness_sha256,
            'connectivity': pin.connectivity_sha256,
        },
        'source_sha256': {
            str(path.relative_to(Path(__file__).resolve().parents[2])): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).resolve().parents[2] / 'simulation/backend/bucketed.py',
                Path(__file__).resolve().parents[2] / 'simulation/backend/core.py',
                Path(__file__).resolve().parents[2]
                / 'simulation/backend/accumulation.py',
            )
        },
        'scope': 'Controlled complete-connectome construction and delayed pulse, including blocked delivery and silenced edge identities; no full-experiment parity or performance claim.',
    }
    with (output / 'connectome-pulse.json').open('x') as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
        destination.write('\n')
    return report
