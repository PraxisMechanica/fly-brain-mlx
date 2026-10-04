import hashlib
import importlib.metadata
import json
import math
import platform
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend.accumulation import (
    SCALE,
    SCALE_HIGH,
    SCALE_LOW,
    factored_sum,
)

from .accumulation_probe import Case, diagnostic_cases


def extended_cases(root: Path) -> list[Case]:
    cases = diagnostic_cases(root)
    generator = np.random.Generator(np.random.PCG64(20261005))

    def add(name: str, counts: NDArray[np.int64], initial: float = 0.0) -> None:
        cases.append(
            Case(name, counts * SCALE, np.ones(counts.size, dtype=np.bool_), initial)
        )

    for maximum, copies in ((2405, 4096), (16383, 2048), (2**24, 1)):
        counts = np.tile(np.array([maximum, 1, -maximum], dtype=np.int64), copies)
        for name, ordered in (
            ('triplets', counts),
            ('ascending', np.sort(counts)),
            ('descending', np.sort(counts)[::-1]),
            ('permuted', generator.permutation(counts)),
        ):
            add(f'extended-{maximum}-{copies}-{name}', ordered)
        drift = np.tile(np.array([maximum, -maximum + 1, -1], dtype=np.int64), copies)
        add(f'extended-drift-{maximum}-{copies}', drift)
        add(f'extended-drift-permuted-{maximum}-{copies}', generator.permutation(drift))
    for size in (3, 33, 257, 4097, 16385):
        counts = np.floor(generator.random(size) * 32767).astype(np.int64) - 16383
        for sign in (1, -1):
            add(f'extended-random-{size}-{sign}', counts * sign, 1024.0 * sign)
    add('count-low-component', np.array([2**24, 1], dtype=np.int64))
    add('count-low-component-negative', np.array([-(2**24), -1], dtype=np.int64))
    add('negative-zero-empty', np.zeros(0, dtype=np.int64), -0.0)
    add('negative-zero-balanced', np.array([2405, -2405], dtype=np.int64), -0.0)
    return cases


def run(root: Path, output: Path, precision: str) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    assert precision == '0'
    assert mx.metal.is_available(), 'Metal is required; CPU fallback is unsupported'
    assert importlib.metadata.version('mlx') == '0.32.3'
    assert importlib.metadata.version('mlx-metal') == '0.32.3'
    assert np.__version__ == '1.26.4'
    mx.disable_compile()
    cases = extended_cases(root)
    width = 1 << (max(case.weights.size for case in cases) - 1).bit_length()
    counts = np.zeros((len(cases), width), dtype=np.int64)
    weights = np.zeros((len(cases), width), dtype=np.float64)
    accepted = np.zeros((len(cases), width), dtype=np.bool_)
    original = np.zeros((len(cases), width + 1), dtype=np.float64)
    for index, case in enumerate(cases):
        connectivity = np.rint(case.weights / SCALE).astype(np.int64)
        np.testing.assert_array_equal(connectivity * SCALE, case.weights)
        np.testing.assert_array_equal(
            connectivity.astype(np.float32).astype(np.int64), connectivity
        )
        counts[index, : case.weights.size] = np.where(case.accepted, connectivity, 0)
        weights[index, : case.weights.size] = case.weights
        accepted[index, : case.weights.size] = case.accepted
        original[index, 0] = case.initial
        original[index, 1 : case.weights.size + 1] = np.where(
            case.accepted, case.weights, 0
        )
    initial = np.array([case.initial for case in cases], dtype=np.float32)
    reference = np.array([math.fsum(row) for row in original], dtype=np.float64)
    serial_reference = np.add.accumulate(original, axis=-1, dtype=np.float64)[:, -1]
    exact_counts = counts.sum(axis=-1, dtype=np.int64)
    with mx.stream(mx.gpu):
        result, count_high, count_low = factored_sum(
            mx.array(counts.astype(np.float32)), mx.array(initial)
        )
        actual = np.asarray(result, dtype=np.float32)
        high_host = np.asarray(count_high, dtype=np.float32)
        low_host = np.asarray(count_low, dtype=np.float32)
        repeated, repeat_high, repeat_low = factored_sum(
            mx.array(counts.astype(np.float32)), mx.array(initial)
        )
        repeated_host = np.asarray(repeated, dtype=np.float32)
        repeat_high_host = np.asarray(repeat_high, dtype=np.float32)
        repeat_low_host = np.asarray(repeat_low, dtype=np.float32)
        standalone = np.zeros(len(cases), dtype=np.float32)
        for index, case in enumerate(cases):
            own_width = 1 << (max(1, case.weights.size) - 1).bit_length()
            own, own_high, own_low = factored_sum(
                mx.array(counts[index, :own_width].astype(np.float32)),
                mx.array(initial[index]),
            )
            standalone[index] = np.asarray(own, dtype=np.float32)
            np.testing.assert_array_equal(
                np.asarray(own_high, dtype=np.float32).view(np.uint32),
                high_host[index].view(np.uint32),
            )
            np.testing.assert_array_equal(
                np.asarray(own_low, dtype=np.float32).view(np.uint32),
                low_host[index].view(np.uint32),
            )
    np.testing.assert_array_equal(
        high_host.astype(np.float64) + low_host.astype(np.float64), exact_counts
    )
    for observed, expected in (
        (actual, repeated_host),
        (actual, standalone),
        (high_host, repeat_high_host),
        (low_host, repeat_low_host),
    ):
        np.testing.assert_array_equal(
            observed.view(np.uint32), expected.view(np.uint32)
        )
    np.testing.assert_array_equal(
        actual[exact_counts == 0].view(np.uint32),
        initial[exact_counts == 0].view(np.uint32),
    )
    one_step_budget = 2e-5 + 2e-6 * np.abs(reference)
    trajectory_budget = 1e-3 + 1e-5 * np.abs(reference)
    error = np.abs(actual.astype(np.float64) - reference)
    serial_error = np.abs(actual.astype(np.float64) - serial_reference)
    one_step_pass = (error <= one_step_budget) & (
        serial_error <= 2e-5 + 2e-6 * np.abs(serial_reference)
    )
    trajectory_pass = (error <= trajectory_budget) & (
        serial_error <= 1e-3 + 1e-5 * np.abs(serial_reference)
    )
    artifact = output / 'factored.npz'
    with artifact.open('xb') as destination:
        np.savez_compressed(
            destination,
            names=np.array([case.name for case in cases]),
            counts=counts,
            weights64=weights,
            accepted=accepted,
            original64=original,
            initial32=initial,
            reference64=reference,
            serial_reference64=serial_reference,
            count_high32=high_host,
            count_low32=low_host,
            result32=actual,
            repeated32=repeated_host,
            standalone32=standalone,
            repeat_high32=repeat_high_host,
            repeat_low32=repeat_low_host,
        )
    rows: list[dict[str, object]] = []
    for index, case in enumerate(cases):
        rows.append(
            {
                'name': case.name,
                'edges': case.weights.size,
                'accepted_events': int(case.accepted.sum()),
                'initial64_mv': case.initial,
                'sum_signed_counts': int(exact_counts[index]),
                'sum_abs_counts': int(np.abs(counts[index]).sum()),
                'reference64_mv': float(reference[index]),
                'serial_reference64_mv': float(serial_reference[index]),
                'factored_mv': float(actual[index]),
                'abs_error_mv': float(error[index]),
                'serial_abs_error_mv': float(serial_error[index]),
                'one_step_budget_mv': float(one_step_budget[index]),
                'trajectory_budget_mv': float(trajectory_budget[index]),
                'one_step_pass': bool(one_step_pass[index]),
                'trajectory_pass': bool(trajectory_pass[index]),
            }
        )
    passed = bool(
        np.isfinite(actual).all() and one_step_pass.all() and trajectory_pass.all()
    )
    report = {
        'scalar_qualification_passed': passed,
        'cases': len(cases),
        'retained_cases': len(diagnostic_cases(root)),
        'one_step_passes': int(one_step_pass.sum()),
        'trajectory_passes': int(trajectory_pass.sum()),
        'max_one_step_budget_fraction': float(np.max(error / one_step_budget)),
        'exact_integer_count_expansions': True,
        'repeat_bit_identical': True,
        'standalone_batch_bit_identical': True,
        'scale_high': SCALE_HIGH,
        'scale_low': SCALE_LOW,
        'scale_expansion_error': SCALE_HIGH + SCALE_LOW - SCALE,
        'execution': 'Uncompiled float32 count tree, compensated common-scale products, state combined before final rounding; explicit Metal stream',
        'mlx': importlib.metadata.version('mlx'),
        'mlx_metal': importlib.metadata.version('mlx-metal'),
        'numpy': np.__version__,
        'python': platform.python_version(),
        'platform': platform.platform(),
        'device': mx.device_info(),
        'MLX_ENABLE_TF32': precision,
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'tree_source_sha256': hashlib.sha256(
            (
                Path(__file__).resolve().parents[2]
                / 'simulation/backend/accumulation.py'
            ).read_bytes()
        ).hexdigest(),
        'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'measurements': rows,
    }
    with (output / 'factored.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')

    if not passed:
        raise SystemExit(1)

    return {key: value for key, value in report.items() if key != 'measurements'}
