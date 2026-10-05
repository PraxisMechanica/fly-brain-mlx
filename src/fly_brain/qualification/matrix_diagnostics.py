from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fly_brain.comparison.diagnostics import time_bin_counts
from fly_brain.comparison.models import ParityMetrics, SpikeSteps
from fly_brain.comparison.pooling import measure_trials
from fly_brain.simulation.models import ExperimentName

from .matrix import required_cases
from .models import ParityCase


@dataclass(frozen=True)
class GroupCoverage:
    experiment: ExperimentName
    steps: int
    expected: tuple[int, ...]
    included: tuple[int, ...]
    missing: tuple[int, ...]
    invalid: tuple[int, ...]
    failed: tuple[int, ...]


@dataclass(frozen=True)
class CaseRasters:
    case: ParityCase
    brian: SpikeSteps
    mlx: SpikeSteps
    torch: SpikeSteps


@dataclass(frozen=True)
class GroupDiagnostics:
    coverage: GroupCoverage
    metrics: dict[str, ParityMetrics] | None
    trial_bin_counts: dict[int, dict[str, tuple[int, ...]]]
    pooled_bin_counts: dict[str, tuple[int, ...]] | None


def coverage(
    included: tuple[ParityCase, ...],
    invalid: tuple[ParityCase, ...] = (),
    failed: tuple[ParityCase, ...] = (),
) -> tuple[GroupCoverage, ...]:
    required = required_cases()
    available = (*included, *invalid)
    if len(set(available)) != len(available) or len(set(failed)) != len(failed):
        raise ValueError('Duplicate case identities cannot enter matrix summaries')
    if set(available) - set(required) or set(failed) - set(included):
        raise ValueError('Coverage requires prescribed cases and included failures')
    groups: dict[tuple[ExperimentName, int], list[ParityCase]] = {}
    for case in required:
        groups.setdefault((case.experiment, case.steps), []).append(case)
    return tuple(
        GroupCoverage(
            experiment,
            steps,
            tuple(case.trial for case in expected),
            tuple(case.trial for case in expected if case in included),
            tuple(case.trial for case in expected if case not in available),
            tuple(case.trial for case in expected if case in invalid),
            tuple(case.trial for case in expected if case in failed),
        )
        for (experiment, steps), expected in groups.items()
    )


def summarize(
    cases: tuple[CaseRasters, ...],
    invalid: tuple[ParityCase, ...] = (),
    failed: tuple[ParityCase, ...] = (),
) -> tuple[GroupDiagnostics, ...]:
    results: list[GroupDiagnostics] = []
    for group in coverage(tuple(row.case for row in cases), invalid, failed):
        rows = sorted(
            (
                row
                for row in cases
                if row.case.experiment == group.experiment
                and row.case.steps == group.steps
            ),
            key=lambda row: row.case.trial,
        )
        if not rows:
            results.append(GroupDiagnostics(group, None, {}, None))
            continue
        support: NDArray[np.int64] = np.unique(
            np.concatenate(
                [
                    spikes.neurons
                    for row in rows
                    for spikes in (row.brian, row.mlx, row.torch)
                ]
            )
        )
        metrics = {
            'mlx': measure_trials(
                tuple((row.brian, row.mlx) for row in rows),
                support,
                group.steps * 0.0001,
            ),
            'torch': measure_trials(
                tuple((row.brian, row.torch) for row in rows),
                support,
                group.steps * 0.0001,
            ),
        }
        bins = {
            row.case.trial: {
                engine: tuple(
                    int(value) for value in time_bin_counts(spikes.steps, group.steps)
                )
                for engine, spikes in (
                    ('brian', row.brian),
                    ('mlx', row.mlx),
                    ('torch', row.torch),
                )
            }
            for row in rows
        }
        pooled = {
            engine: tuple(
                sum(bins[trial][engine][index] for trial in group.included)
                for index in range(group.steps // 1000)
            )
            for engine in ('brian', 'mlx', 'torch')
        }
        results.append(GroupDiagnostics(group, metrics, bins, pooled))
    return tuple(results)
