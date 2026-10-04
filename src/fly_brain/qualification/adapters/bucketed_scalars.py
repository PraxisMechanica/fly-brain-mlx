import hashlib
import json
import math
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend.accumulation import SCALE
from fly_brain.simulation.backend.arrays import boolean_input
from fly_brain.simulation.backend.bucketed import Layout, accumulate, make_layout
from fly_brain.simulation.models import Connectome

from .accumulation_probe import Case
from .factored_probe import extended_cases


def execute(
    layout: Layout, case: Case, trials: int
) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
    initial = np.zeros((trials, case.weights.size + 1), dtype=np.float32)
    initial[:, -1] = case.initial
    accepted = np.broadcast_to(case.accepted, (trials, case.weights.size)).copy()
    with mx.stream(mx.gpu):
        arrays = accumulate(layout, boolean_input(accepted), mx.array(initial))
        host = tuple(np.asarray(value, dtype=np.float32) for value in arrays)
    for value in host:
        np.testing.assert_array_equal(value[:, :-1].view(np.uint32), 0)
    return host[0][:, -1], host[1][:, -1], host[2][:, -1]


def run(root: Path, output: Path, precision: str) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=False)
    assert precision == '0'
    assert mx.metal.is_available()
    mx.disable_compile()
    rows: list[dict[str, object]] = []
    for index, case in enumerate(extended_cases(root)):
        counts = np.rint(case.weights / SCALE).astype(np.int32)
        np.testing.assert_array_equal(counts.astype(np.float64) * SCALE, case.weights)
        assert np.max(np.abs(counts.astype(np.int64)), initial=0) <= 2**24
        assert np.abs(counts.astype(np.int64)).sum() <= 2**40
        connectome = Connectome(
            np.arange(counts.size + 1, dtype=np.int64),
            np.arange(counts.size, dtype=np.int32),
            np.full(counts.size, counts.size, dtype=np.int32),
            counts,
            case.weights,
        )
        layout = make_layout(connectome)
        actual, high, low = execute(layout, case, 3)
        repeated, repeat_high, repeat_low = execute(layout, case, 3)
        standalone, own_high, own_low = execute(layout, case, 1)
        identical = all(
            np.array_equal(left.view(np.uint32), right.view(np.uint32))
            for left, right in (
                (actual, repeated),
                (high, repeat_high),
                (low, repeat_low),
                (actual, np.repeat(standalone, 3)),
                (high, np.repeat(own_high, 3)),
                (low, np.repeat(own_low, 3)),
            )
        )
        exact_count = int(counts[case.accepted].astype(np.int64).sum())
        exact = bool(
            np.all(high.astype(np.float64) + low.astype(np.float64) == exact_count)
        )
        terms = np.concatenate(
            ([case.initial], np.where(case.accepted, case.weights, 0))
        )
        reference = np.array(
            [math.fsum(terms), float(np.add.accumulate(terms, dtype=np.float64)[-1])]
        )
        error = np.abs(actual.astype(np.float64)[:, None] - reference)
        one_step_budget = 2e-5 + 2e-6 * np.abs(reference)
        trajectory_budget = 1e-3 + 1e-5 * np.abs(reference)
        one_step = bool(np.isfinite(actual).all() and np.all(error <= one_step_budget))
        trajectory = bool(
            np.isfinite(actual).all() and np.all(error <= trajectory_budget)
        )
        copied = exact_count != 0 or bool(
            np.all(actual.view(np.uint32) == np.float32(case.initial).view(np.uint32))
        )
        artifact = output / f'case-{index:03}.npz'
        with artifact.open('xb') as destination:
            np.savez_compressed(
                destination,
                name=np.array(case.name),
                counts=counts,
                weights64=case.weights,
                accepted=case.accepted,
                initial64=np.array(case.initial),
                reference64=reference,
                result32=actual,
                count_high32=high,
                count_low32=low,
                repeated32=repeated,
                repeat_high32=repeat_high,
                repeat_low32=repeat_low,
                standalone32=standalone,
                standalone_high32=own_high,
                standalone_low32=own_low,
            )
        rows.append(
            {
                'name': case.name,
                'edges': int(counts.size),
                'exact_counts': exact_count,
                'one_step_pass': one_step,
                'trajectory_pass': trajectory,
                'repeat_and_standalone_bits_identical': identical,
                'integer_count_expansion_exact': exact,
                'zero_count_copied_bit_identically': copied,
                'accepted': one_step and trajectory and identical and exact and copied,
                'max_one_step_budget_fraction': float((error / one_step_budget).max()),
                'max_trajectory_budget_fraction': float(
                    (error / trajectory_budget).max()
                ),
                'artifact': artifact.name,
                'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
            }
        )
    report: dict[str, object] = {
        'accepted': all(row['accepted'] for row in rows),
        'cases': len(rows),
        'original_state_one_step_passes': sum(
            bool(row['one_step_pass']) for row in rows
        ),
        'original_state_trajectory_passes': sum(
            bool(row['trajectory_pass']) for row in rows
        ),
        'all_components_repeat_and_match_standalone': all(
            row['repeat_and_standalone_bits_identical'] for row in rows
        ),
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
            )
        },
        'measurements': rows,
        'scope': 'All 157 retained scalar cases through production layout accumulation; original-state budgets unchanged.',
    }
    with (output / 'bucketed-scalars.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')
    return {key: value for key, value in report.items() if key != 'measurements'}
