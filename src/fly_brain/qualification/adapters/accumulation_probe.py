import hashlib
import importlib.metadata
import json
import math
import platform
from dataclasses import dataclass
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend.accumulation import compensated_tree, plain_tree


@dataclass(frozen=True)
class Case:
    name: str
    weights: NDArray[np.float64]
    accepted: NDArray[np.bool_]
    initial: float = 0.0


def diagnostic_cases(root: Path) -> list[Case]:
    generator = np.random.Generator(np.random.PCG64(20261004))
    cases: list[Case] = []

    def add(name: str, weights: NDArray[np.float64], initial: float = 0.0) -> None:
        cases.append(
            Case(name, weights, np.ones(weights.size, dtype=np.bool_), initial)
        )

    with np.load(
        root / 'docs/evidence/milestone-1/final/accumulation-limit.npz'
    ) as raw:
        ordered = np.asarray(raw['ordered_weights_mv'], dtype=np.float64)
        add('retained-ordered', ordered)
        add('retained-interleaved', raw['interleaved_weights_mv'])
        add('retained-reversed', ordered[::-1].copy())
        add('retained-permuted', generator.permutation(ordered))
        add('retained-existing-state', ordered, -0.275)

    for size in (
        0,
        1,
        2,
        3,
        31,
        32,
        33,
        127,
        128,
        129,
        1023,
        1024,
        1025,
        4095,
        4096,
        4097,
        8193,
    ):
        counts = 1 + np.floor(generator.random(size) * 2405).astype(np.int64)
        signs = generator.choice(np.array([-1, 1], dtype=np.int64), size=size)
        weights = counts * signs * 0.275
        add(f'unbalanced-{size}', weights)
        add(f'positive-{size}', counts * 0.275)
        add(f'negative-{size}', counts * -0.275)
        add(f'balanced-{size}', np.concatenate((counts, -counts)) * 0.275, 0.125)
        mask = generator.random(size) < 0.5
        silenced = weights.copy()
        silenced[::3] = 0
        cases.append(Case(f'masked-silenced-{size}', silenced, mask, -1024.0))
        cases.append(
            Case(f'blocked-{size}', weights, np.zeros(size, dtype=np.bool_), 1024.0)
        )

    for copies in (1, 32, 128, 2048):
        weights = np.tile([2405, -2404, -1], copies) * 0.275
        add(f'cast-drift-{copies}', weights)
        add(f'cast-drift-reversed-{copies}', weights[::-1].copy())
        add(f'cast-drift-permuted-{copies}', generator.permutation(weights))

    for initial in (-1024.0, -1000.0, -0.275, 0.0001, 1000.0, 1024.0):
        counts = np.array([round(-initial / 0.275)], dtype=np.int64)
        add(f'existing-state-{initial}', counts * 0.275, initial)
    return cases


def run(root: Path, output: Path, precision: str) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    assert precision == '0'
    assert mx.metal.is_available(), 'Metal is required; CPU fallback is unsupported'
    assert importlib.metadata.version('mlx') == '0.32.3'
    assert importlib.metadata.version('mlx-metal') == '0.32.3'
    assert np.__version__ == '1.26.4'
    mx.disable_compile()
    cases = diagnostic_cases(root)
    width = 1 << max(case.weights.size for case in cases).bit_length()
    leaves = np.zeros((len(cases), width), dtype=np.float64)
    weights = np.zeros_like(leaves)
    masks = np.zeros_like(leaves, dtype=np.bool_)
    for index, case in enumerate(cases):
        leaves[index, 0] = case.initial
        leaves[index, 1 : case.weights.size + 1] = np.where(
            case.accepted, case.weights, 0
        )
        weights[index, : case.weights.size] = case.weights
        masks[index, : case.weights.size] = case.accepted
    values32 = leaves.astype(np.float32)
    reference = np.array([math.fsum(row) for row in leaves], dtype=np.float64)
    cast_reference = np.array([math.fsum(row) for row in values32], dtype=np.float64)
    serial_reference = np.add.accumulate(leaves, axis=-1, dtype=np.float64)[:, -1]

    with mx.stream(mx.gpu):
        values = mx.array(values32)
        high, low = compensated_tree(values)
        compensated = high + low
        repeat_high, repeat_low = compensated_tree(mx.array(values32))
        repeated = repeat_high + repeat_low
        pairwise = plain_tree(values)
        library = mx.sum(values, axis=-1)
        actual = np.asarray(compensated, dtype=np.float32)
        high_host = np.asarray(high, dtype=np.float32)
        low_host = np.asarray(low, dtype=np.float32)
        standalone: list[float] = []
        for index in range(len(cases)):
            own_width = 1 << cases[index].weights.size.bit_length()
            own_high, own_low = compensated_tree(mx.array(values32[index, :own_width]))
            own = own_high + own_low
            np.testing.assert_array_equal(
                np.asarray(own_high, dtype=np.float32).view(np.uint32),
                high_host[index].view(np.uint32),
            )
            np.testing.assert_array_equal(
                np.asarray(own_low, dtype=np.float32).view(np.uint32),
                low_host[index].view(np.uint32),
            )
            standalone.append(float(np.asarray(own, dtype=np.float32)))
        np.testing.assert_array_equal(
            actual.view(np.uint32), np.asarray(repeated).view(np.uint32)
        )
        np.testing.assert_array_equal(
            np.asarray(high).view(np.uint32), np.asarray(repeat_high).view(np.uint32)
        )
        np.testing.assert_array_equal(
            np.asarray(low).view(np.uint32), np.asarray(repeat_low).view(np.uint32)
        )
        np.testing.assert_array_equal(
            actual.view(np.uint32),
            np.array(standalone, dtype=np.float32).view(np.uint32),
        )
        pairwise_host = np.asarray(pairwise, dtype=np.float32)
        library_host = np.asarray(library, dtype=np.float32)

    assert np.isfinite(actual).all()
    np.testing.assert_array_equal(
        high_host.astype(np.float64) + low_host.astype(np.float64), cast_reference
    )
    np.testing.assert_array_equal(
        actual.view(np.uint32), cast_reference.astype(np.float32).view(np.uint32)
    )
    cast_budget = 2e-5 + 2e-6 * np.abs(cast_reference)
    assert np.all(np.abs(actual.astype(np.float64) - cast_reference) <= cast_budget)
    one_step_budget = 2e-5 + 2e-6 * np.abs(reference)
    trajectory_budget = 1e-3 + 1e-5 * np.abs(reference)
    errors = np.abs(actual.astype(np.float64) - reference)
    serial_errors = np.abs(actual.astype(np.float64) - serial_reference)
    one_step_pass = (errors <= one_step_budget) & (
        serial_errors <= 2e-5 + 2e-6 * np.abs(serial_reference)
    )
    trajectory_pass = (errors <= trajectory_budget) & (
        serial_errors <= 1e-3 + 1e-5 * np.abs(serial_reference)
    )
    names = [case.name for case in cases]
    assert one_step_pass[names.index('retained-ordered')]
    assert not trajectory_pass[names.index('cast-drift-128')]
    for index, case in enumerate(cases):
        if case.name.startswith('blocked-'):
            assert actual[index] == np.float32(case.initial)
    rows: list[dict[str, object]] = []
    for index, case in enumerate(cases):
        terms = leaves[index]
        event_count = int(case.accepted.sum())
        magnitude = math.fsum(np.abs(terms))
        unit = 2**-24
        gamma = event_count * unit / (1 - event_count * unit)
        rows.append(
            {
                'name': case.name,
                'edges': case.weights.size,
                'accepted_events': event_count,
                'initial_mv': case.initial,
                'reference_fsum64_mv': float(reference[index]),
                'reference_serial64_mv': float(serial_reference[index]),
                'cast_fsum64_mv': float(cast_reference[index]),
                'input_cast_error_mv': float(cast_reference[index] - reference[index]),
                'compensated_mv': float(actual[index]),
                'pairwise_mv': float(pairwise_host[index]),
                'library_sum_mv': float(library_host[index]),
                'reduction_error_mv': float(actual[index] - cast_reference[index]),
                'total_abs_error_mv': float(errors[index]),
                'one_step_budget_mv': float(one_step_budget[index]),
                'trajectory_budget_mv': float(trajectory_budget[index]),
                'one_step_pass': bool(one_step_pass[index]),
                'trajectory_pass': bool(trajectory_pass[index]),
                'sum_abs_terms_mv': magnitude,
                'gamma_m_sum_abs_mv': gamma * magnitude,
            }
        )
    artifact = output / 'accumulation.npz'
    with artifact.open('xb') as destination:
        np.savez_compressed(
            destination,
            names=np.array(names),
            weights_mv=weights,
            accepted=masks,
            leaves64=leaves,
            leaves32=values32,
            reference64=reference,
            serial64=serial_reference,
            cast_reference64=cast_reference,
            high32=high_host,
            low32=low_host,
            compensated32=actual,
            repeated32=np.asarray(repeated, dtype=np.float32),
            repeated_high32=np.asarray(repeat_high, dtype=np.float32),
            repeated_low32=np.asarray(repeat_low, dtype=np.float32),
            standalone32=np.array(standalone, dtype=np.float32),
            pairwise32=pairwise_host,
            library32=library_host,
        )
    report = {
        'diagnostic_assertions_passed': True,
        'strategy_approved': False,
        'reason': 'Individual weight casting can exceed the fixed budgets before reduction',
        'cases': len(cases),
        'width': width,
        'reduction_against_cast_inputs_one_step_passes': len(cases),
        'expansion_exact_for_cast_inputs': True,
        'correctly_rounded_cast_sum': True,
        'source_reference_one_step_passes': int(one_step_pass.sum()),
        'source_reference_trajectory_passes': int(trajectory_pass.sum()),
        'repeat_bit_identical': True,
        'standalone_batch_bit_identical': True,
        'standalone_uses_minimum_power_of_two_width': True,
        'execution': 'Uncompiled adjacent-pair compensated tree; explicit Metal stream; state is leaf zero',
        'mlx': importlib.metadata.version('mlx'),
        'mlx_metal': importlib.metadata.version('mlx-metal'),
        'numpy': np.__version__,
        'python': platform.python_version(),
        'platform': platform.platform(),
        'device': mx.device_info(),
        'MLX_ENABLE_TF32': precision,
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'measurements': rows,
    }
    with (output / 'accumulation.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')

    return {key: value for key, value in report.items() if key != 'measurements'}
