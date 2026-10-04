import hashlib
import json
import math
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend.arrays import as_host, boolean_input
from fly_brain.simulation.backend.bucketed import Layout, accumulate, make_layout
from fly_brain.simulation.mapping import bucket_destinations
from fly_brain.simulation.models import Connectome, InputPin

from .fan_in_probe import Reduction


def execute(
    layout: Layout, accepted: NDArray[np.bool_], initial: NDArray[np.float32]
) -> Reduction:
    with mx.stream(mx.gpu):
        arrays = accumulate(layout, boolean_input(accepted), mx.array(initial))
        host = tuple(np.asarray(value, dtype=np.float32) for value in arrays)
    return host[0], host[1], host[2]


def run(
    connectome: Connectome, pin: InputPin, output: Path, precision: str
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    assert precision == '0' and mx.metal.is_available()
    mx.disable_compile()
    neurons = connectome.neuron_ids.size
    seed = [20261004, 785]
    generator = np.random.Generator(np.random.PCG64(np.random.SeedSequence(seed)))
    source_spikes = np.zeros((5, neurons), dtype=np.bool_)
    receiving = np.ones((5, neurons), dtype=np.bool_)
    source_spikes[0] = True
    for row, (source_probability, receiving_probability) in enumerate(
        ((0.001, 0.8), (0.01, 0.6), (0.5, 0.5)), start=2
    ):
        source_spikes[row] = generator.random(neurons) < source_probability
        receiving[row] = generator.random(neurons) < receiving_probability
    accepted = (
        source_spikes[:, connectome.sources] & receiving[:, connectome.destinations]
    )
    initial = np.broadcast_to(
        np.array([0.0, -0.0, 1024.0, -1024.0, 0.0], dtype=np.float32)[:, None],
        (5, neurons),
    ).copy()
    exact_counts = np.zeros((5, neurons), dtype=np.int64)
    for row in range(5):
        np.add.at(
            exact_counts[row],
            connectome.destinations,
            np.where(accepted[row], connectome.counts, 0).astype(np.int64),
        )
    host_buckets = bucket_destinations(connectome)
    layout = make_layout(connectome)
    inverse = np.argsort(np.concatenate([b.targets for b in host_buckets])).astype(
        np.int32
    )
    with mx.stream(mx.gpu):
        actual_inverse = as_host(layout.inverse_targets)
        padded_events = mx.concatenate(
            [mx.zeros((5, 1), dtype=mx.bool_), boolean_input(accepted)], axis=1
        )
    assert actual_inverse.dtype == inverse.dtype
    assert actual_inverse.shape == inverse.shape
    assert actual_inverse.tobytes() == inverse.tobytes()
    reference = np.empty((5, neurons, 2), dtype=np.float64)
    buckets: list[dict[str, object]] = []
    for host, device in zip(host_buckets, layout.buckets, strict=True):
        fields: dict[str, object] = {}
        for name in ('targets', 'edge_ids', 'counts', 'occupied'):
            expected = getattr(host, name)
            with mx.stream(mx.gpu):
                observed = as_host(getattr(device, name))
            assert observed.dtype == expected.dtype
            assert observed.shape == expected.shape
            assert observed.tobytes() == expected.tobytes()
            fields[name] = {
                'dtype': observed.dtype.str,
                'shape': list(observed.shape),
                'sha256': hashlib.sha256(observed.tobytes()).hexdigest(),
                'exact_device_round_trip': True,
            }
        with mx.stream(mx.gpu):
            gathered = np.asarray(
                padded_events[:, device.edge_ids + 1] & device.occupied,
                dtype=np.bool_,
            )
        expected_events = np.zeros((5, *host.edge_ids.shape), dtype=np.bool_)
        expected_events[:, host.occupied] = accepted[:, host.edge_ids[host.occupied]]
        np.testing.assert_array_equal(gathered, expected_events)
        weights = np.zeros(host.edge_ids.shape, dtype=np.float64)
        weights[host.occupied] = connectome.weights_mv[host.edge_ids[host.occupied]]
        terms = np.concatenate(
            (
                initial[:, host.targets, None].astype(np.float64),
                np.where(expected_events, weights, 0),
            ),
            axis=-1,
        )
        reference[:, host.targets, 1] = np.add.accumulate(
            terms, axis=-1, dtype=np.float64
        )[..., -1]
        for row in range(5):
            reference[row, host.targets, 0] = np.fromiter(
                (math.fsum(values) for values in terms[row]),
                dtype=np.float64,
                count=host.targets.size,
            )
        buckets.append(
            {
                'width': host.edge_ids.shape[1],
                'fields': fields,
                'gathered_event_shape': list(gathered.shape),
                'gathered_event_sha256': hashlib.sha256(gathered.tobytes()).hexdigest(),
                'every_occupied_and_padding_event_matches': True,
            }
        )
        print(
            f'Complete device bucket {len(buckets)}/{len(host_buckets)} passes',
            flush=True,
        )
    actual, high, low = execute(layout, accepted, initial)
    repeated, repeat_high, repeat_low = execute(layout, accepted, initial)
    standalone = np.empty_like(actual)
    standalone_high, standalone_low = np.empty_like(high), np.empty_like(low)
    for row in range(5):
        own, own_high, own_low = execute(
            layout, accepted[row : row + 1], initial[row : row + 1]
        )
        standalone[row], standalone_high[row], standalone_low[row] = (
            own[0],
            own_high[0],
            own_low[0],
        )
    for left, right in (
        (actual, repeated),
        (high, repeat_high),
        (low, repeat_low),
        (actual, standalone),
        (high, standalone_high),
        (low, standalone_low),
    ):
        np.testing.assert_array_equal(left.view(np.uint32), right.view(np.uint32))
    np.testing.assert_array_equal(
        high.astype(np.float64) + low.astype(np.float64), exact_counts
    )
    zero = exact_counts == 0
    np.testing.assert_array_equal(
        actual[zero].view(np.uint32), initial[zero].view(np.uint32)
    )
    error = np.abs(actual.astype(np.float64)[..., None] - reference)
    one_step_budget = 2e-5 + 2e-6 * np.abs(reference)
    trajectory_budget = 1e-3 + 1e-5 * np.abs(reference)
    assert np.isfinite(actual).all()
    assert np.all(error <= one_step_budget)
    assert np.all(error <= trajectory_budget)
    artifact = output / 'device-layout.npz'
    with artifact.open('xb') as destination:
        np.savez_compressed(
            destination,
            seed=np.array(seed),
            source_spikes=source_spikes,
            receiving=receiving,
            initial32=initial,
            exact_counts=exact_counts,
            reference64=reference,
            result32=actual,
            count_high32=high,
            count_low32=low,
            repeated32=repeated,
            repeat_high32=repeat_high,
            repeat_low32=repeat_low,
            standalone32=standalone,
            standalone_high32=standalone_high,
            standalone_low32=standalone_low,
        )
    report: dict[str, object] = {
        'accepted': True,
        'neurons': int(neurons),
        'edges': int(connectome.counts.size),
        'patterns': [
            'all-accepted',
            'none-accepted-negative-zero',
            'source-0.001-receiving-0.8',
            'source-0.01-receiving-0.6',
            'source-0.5-receiving-0.5',
        ],
        'seed': seed,
        'accepted_events_per_trial': accepted.sum(axis=1).tolist(),
        'all_fields_round_trip_exactly': True,
        'inverse_target_order_exact': True,
        'every_gathered_event_and_padding_leaf_matches': True,
        'integer_count_expansions_exact': True,
        'repeat_and_standalone_bits_identical': True,
        'zero_counts_copy_initial_bits': True,
        'both_original_state_budgets_pass': True,
        'max_one_step_budget_fraction': float((error / one_step_budget).max()),
        'max_trajectory_budget_fraction': float((error / trajectory_budget).max()),
        'input_sha256': {
            'completeness': pin.completeness_sha256,
            'connectivity': pin.connectivity_sha256,
        },
        'accepted_event_sha256': hashlib.sha256(accepted.tobytes()).hexdigest(),
        'buckets': buckets,
        'artifact': artifact.name,
        'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'MLX_ENABLE_TF32': precision,
        'device': mx.device_info(),
        'compilation': 'disabled',
        'source_sha256': {
            str(path.relative_to(Path(__file__).resolve().parents[2])): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).resolve().parents[2] / 'simulation/backend/bucketed.py',
                Path(__file__).resolve().parents[2]
                / 'simulation/backend/accumulation.py',
                Path(__file__).resolve().parents[2] / 'simulation/mapping.py',
            )
        },
        'scope': 'Complete pinned-device representation and isolated propagation; no full-network parity or performance claim.',
    }
    with (output / 'device-layout.json').open('x') as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
        destination.write('\n')
    return {key: value for key, value in report.items() if key != 'buckets'}
