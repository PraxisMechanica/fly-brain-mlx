import hashlib
import importlib.metadata
import json
from collections.abc import Callable
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.fan_in import FanInCases, compare_cases
from fly_brain.qualification.fan_in_ports import FanInCaseBuilder
from fly_brain.qualification.input_patterns import analyze_inputs
from fly_brain.simulation.backend.accumulation import factored_sum
from fly_brain.simulation.mapping import group_destinations
from fly_brain.simulation.models import Connectome, InputPin

Reduction = tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]
Evaluation = tuple[Reduction, Reduction, Reduction]


def execute(
    counts: NDArray[np.float32], initial: NDArray[np.float32]
) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
    with mx.stream(mx.gpu):
        result, high, low = factored_sum(mx.array(counts), mx.array(initial))
        return (
            np.asarray(result, dtype=np.float32),
            np.asarray(high, dtype=np.float32),
            np.asarray(low, dtype=np.float32),
        )


def evaluate_cases(
    connectome: Connectome, target: int, edges: NDArray[np.int32], cases: FanInCases
) -> Evaluation:
    initial = cases.initial64.astype(np.float32)
    actual = execute(cases.leaves32, initial)
    repeated = execute(cases.leaves32, initial)
    standalone = tuple(np.empty_like(value) for value in actual)
    for row in range(initial.size):
        own = execute(cases.leaves32[row], np.asarray(initial[row], dtype=np.float32))
        for destination, value in zip(standalone, own, strict=True):
            destination[row] = value
    return actual, repeated, (standalone[0], standalone[1], standalone[2])


def run(
    connectome: Connectome,
    pin: InputPin,
    output: Path,
    precision: str,
    evaluator: Callable[
        [Connectome, int, NDArray[np.int32], FanInCases], Evaluation
    ] = evaluate_cases,
    scope: str = 'Isolated pinned-data fan-in qualification; not a full-network run.',
    *,
    build_cases: FanInCaseBuilder,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    assert precision == '0'
    assert mx.metal.is_available(), 'Metal is required; CPU fallback is unsupported'
    assert importlib.metadata.version('mlx') == '0.32.3'
    assert importlib.metadata.version('mlx-metal') == '0.32.3'
    assert np.__version__ == '1.26.4'
    mx.disable_compile()
    patterns = analyze_inputs(connectome)
    grouping = group_destinations(connectome)
    targets: list[dict[str, object]] = []
    all_accepted = True
    total_cases = total_one_step = total_trajectory = original_failures = 0
    worst_one_step = worst_trajectory = 0.0
    for target_index in patterns.targets:
        target = int(target_index)
        edges = grouping.edge_ids[
            grouping.offsets[target] : grouping.offsets[target + 1]
        ]
        sources = connectome.sources[edges]
        counts = connectome.counts[edges]
        weights = connectome.weights_mv[edges]
        cases = build_cases(target, sources, counts, weights)
        initial32 = cases.initial64.astype(np.float32)
        (
            (actual, high, low),
            (repeat, repeat_high, repeat_low),
            (standalone, standalone_high, standalone_low),
        ) = evaluator(connectome, target, edges, cases)
        checks = compare_cases(cases, actual)
        repeat_pass = (
            (actual.view(np.uint32) == repeat.view(np.uint32))
            & (high.view(np.uint32) == repeat_high.view(np.uint32))
            & (low.view(np.uint32) == repeat_low.view(np.uint32))
        )
        standalone_pass = (
            (actual.view(np.uint32) == standalone.view(np.uint32))
            & (high.view(np.uint32) == standalone_high.view(np.uint32))
            & (low.view(np.uint32) == standalone_low.view(np.uint32))
        )
        exact_expansion = high.astype(np.float64) + low.astype(np.float64)
        count_pass = exact_expansion == cases.exact_counts
        copy_pass = (cases.exact_counts != 0) | (
            actual.view(np.uint32) == initial32.view(np.uint32)
        )
        passed = (
            checks.one_step_pass
            & checks.trajectory_pass
            & repeat_pass
            & standalone_pass
            & count_pass
            & copy_pass
        )
        one_step_fraction = checks.stored_error64 / checks.one_step_budget64
        trajectory_fraction = checks.original_error64 / checks.trajectory_budget64
        artifact = output / f'target-{target}.npz'
        with artifact.open('xb') as destination:
            np.savez_compressed(
                destination,
                target=np.array(target, dtype=np.int32),
                flywire_id=np.array(connectome.neuron_ids[target], dtype=np.int64),
                edge_ids=edges,
                sources=sources,
                signed_counts=counts,
                weights64=weights,
                mask_names=np.array(cases.mask_names),
                masks=cases.masks,
                orders=cases.orders,
                mask_indices=cases.mask_indices,
                order_indices=cases.order_indices,
                state_names=np.array(cases.state_names),
                initial64=cases.initial64,
                initial32=initial32,
                initial_cast_error64=initial32.astype(np.float64) - cases.initial64,
                leaves32=cases.leaves32,
                original_reference64=cases.original64,
                stored_reference64=cases.stored64,
                cast_input_reference64=cases.cast_input64,
                exact_counts=cases.exact_counts,
                absolute_counts=cases.absolute_counts,
                absolute_weights64=cases.absolute_weights64,
                result32=actual,
                count_high32=high,
                count_low32=low,
                repeated32=repeat,
                repeat_high32=repeat_high,
                repeat_low32=repeat_low,
                standalone32=standalone,
                standalone_high32=standalone_high,
                standalone_low32=standalone_low,
                stored_error64=checks.stored_error64,
                original_error64=checks.original_error64,
                one_step_budget64=checks.one_step_budget64,
                trajectory_budget64=checks.trajectory_budget64,
                one_step_pass=checks.one_step_pass,
                trajectory_pass=checks.trajectory_pass,
                original_one_step_pass=checks.original_one_step_pass,
                repeat_pass=repeat_pass,
                standalone_pass=standalone_pass,
                count_pass=count_pass,
                zero_count_copy_pass=copy_pass,
                accepted=passed,
            )
        measurements: list[dict[str, object]] = []
        for row in range(initial32.size):
            mask_index = int(cases.mask_indices[row])
            events = int(cases.masks[mask_index].sum())
            gamma = events * 2**-24 / (1 - events * 2**-24)
            measurements.append(
                {
                    'row': row,
                    'mask': cases.mask_names[mask_index],
                    'state': cases.state_names[row],
                    'order': ('original', 'reversed', 'seeded-permutation')[
                        cases.order_indices[row]
                    ],
                    'accepted_events': events,
                    'initial64_mv': float(cases.initial64[row]),
                    'initial32_mv': float(initial32[row]),
                    'initial_cast_error_mv': float(initial32[row])
                    - float(cases.initial64[row]),
                    'original_reference64_mv': cases.original64[row].tolist(),
                    'stored_reference64_mv': cases.stored64[row].tolist(),
                    'cast_input_reference64_mv': float(cases.cast_input64[row]),
                    'factored_mv': float(actual[row]),
                    'stored_abs_error_mv': checks.stored_error64[row].tolist(),
                    'original_abs_error_mv': checks.original_error64[row].tolist(),
                    'one_step_budget_mv': checks.one_step_budget64[row].tolist(),
                    'trajectory_budget_mv': checks.trajectory_budget64[row].tolist(),
                    'sum_signed_counts': int(cases.exact_counts[row]),
                    'sum_abs_counts': int(cases.absolute_counts[row]),
                    'sum_abs_weights_mv': float(cases.absolute_weights64[row]),
                    'gamma_m_sum_abs_weights_mv': gamma
                    * float(cases.absolute_weights64[row]),
                    'one_step_pass': bool(checks.one_step_pass[row]),
                    'trajectory_pass': bool(checks.trajectory_pass[row]),
                    'original_one_step_pass': bool(checks.original_one_step_pass[row]),
                    'repeat_pass': bool(repeat_pass[row]),
                    'standalone_pass': bool(standalone_pass[row]),
                    'exact_count_expansion': bool(count_pass[row]),
                    'zero_count_copy_pass': bool(copy_pass[row]),
                    'accepted': bool(passed[row]),
                }
            )
        with (output / f'target-{target}.json').open('x') as destination:
            json.dump(measurements, destination, indent=2, allow_nan=False)
            destination.write('\n')
        target_report: dict[str, object] = {
            'target': target,
            'flywire_id': int(connectome.neuron_ids[target]),
            'edges': int(edges.size),
            'masks': len(cases.mask_names),
            'cases': int(initial32.size),
            'accepted': bool(passed.all()),
            'one_step_passes': int(checks.one_step_pass.sum()),
            'trajectory_passes': int(checks.trajectory_pass.sum()),
            'original_one_step_conversion_failures': int(
                (~checks.original_one_step_pass & checks.one_step_pass).sum()
            ),
            'max_one_step_budget_fraction': float(one_step_fraction.max()),
            'max_trajectory_budget_fraction': float(trajectory_fraction.max()),
            'repeat_bit_identical': bool(repeat_pass.all()),
            'standalone_batch_bit_identical': bool(standalone_pass.all()),
            'exact_integer_count_expansions': bool(count_pass.all()),
            'zero_count_copied_bit_identically': bool(copy_pass.all()),
            'failed_rows': np.flatnonzero(~passed).tolist(),
            'original_one_step_failed_rows': np.flatnonzero(
                ~checks.original_one_step_pass
            ).tolist(),
            'artifact': artifact.name,
            'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }
        targets.append(target_report)
        all_accepted &= bool(passed.all())
        total_cases += int(initial32.size)
        total_one_step += int(checks.one_step_pass.sum())
        total_trajectory += int(checks.trajectory_pass.sum())
        original_failures += int((~checks.original_one_step_pass).sum())
        worst_one_step = max(worst_one_step, float(one_step_fraction.max()))
        worst_trajectory = max(worst_trajectory, float(trajectory_fraction.max()))
        print(
            f'Target {len(targets)}/{patterns.targets.size}: {target}, '
            f'{int(passed.sum())}/{initial32.size} cases accepted',
            flush=True,
        )
    report: dict[str, object] = {
        'accepted': all_accepted,
        'targets': len(targets),
        'masks_per_target': 70,
        'orders_per_state': 3,
        'cases': total_cases,
        'one_step_passes': total_one_step,
        'trajectory_passes': total_trajectory,
        'original_one_step_conversion_failures': original_failures,
        'max_one_step_budget_fraction': worst_one_step,
        'max_trajectory_budget_fraction': worst_trajectory,
        'reference_columns': ['accurate-float64', 'ordered-float64'],
        'one_step_reference': 'Identical stored initial state; original float64 weights',
        'trajectory_reference': 'Original prescribed initial state and float64 weights',
        'original_one_step_failures': 'Retained conversion limitations, never passes',
        'input_sha256': {
            'completeness': pin.completeness_sha256,
            'connectivity': pin.connectivity_sha256,
        },
        'mlx': importlib.metadata.version('mlx'),
        'numpy': np.__version__,
        'device': mx.device_info(),
        'MLX_ENABLE_TF32': precision,
        'compilation': 'disabled',
        'source_sha256': {
            str(path.relative_to(Path(__file__).resolve().parents[2])): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in (
                Path(__file__),
                Path(__file__).resolve().parents[1] / 'fan_in.py',
                Path(__file__).resolve().parents[1] / 'input_patterns.py',
                Path(__file__).resolve().parents[2]
                / 'simulation/backend/accumulation.py',
                Path(__file__).with_name('bucketed_fan_in.py'),
                Path(__file__).resolve().parents[2] / 'simulation/backend/bucketed.py',
            )
        },
        'measurements': targets,
        'scope': scope,
    }
    with (output / 'fan-in.json').open('x') as destination:
        json.dump(report, destination, indent=2, allow_nan=False)
        destination.write('\n')
    return {key: value for key, value in report.items() if key != 'measurements'}
