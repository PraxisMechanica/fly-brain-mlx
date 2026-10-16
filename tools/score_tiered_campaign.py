"""Score independent cohorts without substituting timing parity for statistics."""

import argparse
import csv
import json
import math
import subprocess
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict

from fly_brain.comparison.metrics import pearson_or_none
from fly_brain.infrastructure.output_paths import require_retained_output

from .run_tiered_campaign import Campaign, Completed, Profile, jobs, verify
from .tiered_trial import digest, sources

# Two-sided 95% t critical, df=29, computed with mpmath at 40 decimal digits.
# With 30 independent observations per group, Welch df is at least 29.
T29_95 = 2.0452296421327043
COHORTS = ('Brian2', 'MLX-A', 'MLX-B')


@dataclass(frozen=True)
class Welch:
    mean_a: NDArray[np.float64]
    mean_b: NDArray[np.float64]
    variance_a: NDArray[np.float64]
    variance_b: NDArray[np.float64]
    difference: NDArray[np.float64]
    standard_error: NDArray[np.float64]
    z: NDArray[np.float64]
    degrees_freedom: NDArray[np.float64]
    constant_discrepancy: NDArray[np.bool_]


def welch(a: NDArray[np.float64], b: NDArray[np.float64]) -> Welch:
    if (
        a.ndim != 2
        or b.ndim != 2
        or a.shape[1] != b.shape[1]
        or min(len(a), len(b)) < 2
        or not np.isfinite(a).all()
        or not np.isfinite(b).all()
    ):
        raise ValueError('Welch statistics require two finite sample matrices')
    ma, mb = a.mean(axis=0), b.mean(axis=0)
    va, vb = a.var(axis=0, ddof=1), b.var(axis=0, ddof=1)
    sa, sb = va / len(a), vb / len(b)
    se2 = sa + sb
    difference = ma - mb
    z = np.zeros_like(difference)
    np.divide(difference, np.sqrt(se2), out=z, where=se2 > 0)
    constant = (se2 == 0) & (difference != 0)
    z[constant] = np.copysign(np.inf, difference[constant])
    df = np.full_like(difference, np.nan)
    denominator = sa * sa / (len(a) - 1) + sb * sb / (len(b) - 1)
    np.divide(se2 * se2, denominator, out=df, where=denominator > 0)
    return Welch(ma, mb, va, vb, difference, np.sqrt(se2), z, df, constant)


def ratio_interval(
    reference: NDArray[np.float64], candidate: NDArray[np.float64]
) -> tuple[float, float] | None:
    """Conservative Fieller interval under the prospective t-model assumptions."""
    if min(len(reference), len(candidate)) < 30:
        raise ValueError('The recorded df29 confidence bound requires 30 samples')
    mb, mx = float(reference.mean()), float(candidate.mean())
    vb = float(reference.var(ddof=1) / len(reference))
    vx = float(candidate.var(ddof=1) / len(candidate))
    a = mb * mb - T29_95**2 * vb
    b = -2 * mb * mx
    c = mx * mx - T29_95**2 * vx
    discriminant = b * b - 4 * a * c
    if a <= 0 or discriminant < 0:
        return None
    root = math.sqrt(discriminant)
    return ((-b - root) / (2 * a), (-b + root) / (2 * a))


def eon_metrics(a: NDArray[np.float64], b: NDArray[np.float64]) -> dict[str, object]:
    first, second = a.sum(axis=0), b.sum(axis=0)
    active_a, active_b = first > 0, second > 0
    union, shared = active_a | active_b, active_a & active_b
    # Eon's pinned scorer uses zero for empty Jaccard; contract agreement is
    # reported separately. Undefined Pearson stays explicit instead of NaN.
    jaccard = float(shared.sum() / union.sum()) if union.any() else 0.0
    correlation = pearson_or_none(first[shared] / len(a), second[shared] / len(b))
    total_a, total_b = float(first.sum()), float(second.sum())
    ratio = total_b / total_a if total_a else None
    return {
        'jaccard_raw': jaccard,
        'jaccard_eon_rounded': round(jaccard, 4),
        'shared_active_pearson_raw': correlation,
        'shared_active_pearson_eon_rounded': round(correlation, 6)
        if correlation is not None
        else None,
        'spike_count_ratio_raw': ratio,
        'spike_count_ratio_eon_rounded': round(ratio, 4) if ratio is not None else None,
        'active_union': int(union.sum()),
        'shared_active': int(shared.sum()),
        'both_silent_exact_agreement': bool(not union.any()),
    }


def finite(value: float) -> float | None:
    return value if math.isfinite(value) else None


def compare(
    a: NDArray[np.float64],
    b: NDArray[np.float64],
    ids: NDArray[np.int64],
    output: Path,
) -> dict[str, object]:
    if a.shape != b.shape or a.shape != (30, len(ids)):
        raise ValueError('Active cohorts require all 30 independent one-second trials')
    result = welch(a, b)
    active = (result.mean_a > 0) | (result.mean_b > 0)
    outliers = np.abs(result.z) >= 4
    fraction = float(outliers[active].sum() / active.sum()) if active.any() else 0.0
    np.savez_compressed(
        output.with_suffix('.npz'),
        neuron_ids=ids,
        mean_a_hz=result.mean_a,
        mean_b_hz=result.mean_b,
        sample_variance_a=result.variance_a,
        sample_variance_b=result.variance_b,
        difference_hz=result.difference,
        standard_error=result.standard_error,
        z=result.z,
        welch_df=result.degrees_freedom,
        constant_discrepancy=result.constant_discrepancy,
        difference_ci95_low=result.difference - T29_95 * result.standard_error,
        difference_ci95_high=result.difference + T29_95 * result.standard_error,
    )
    with output.with_suffix('.csv').open('x', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(
            ('flywire_id', 'mean_a_hz', 'mean_b_hz', 'z', 'constant_discrepancy')
        )
        for row in np.flatnonzero(outliers):
            writer.writerow(
                (
                    int(ids[row]),
                    float(result.mean_a[row]),
                    float(result.mean_b[row]),
                    float(result.z[row]),
                    bool(result.constant_discrepancy[row]),
                )
            )
    primary: dict[str, object] = {}
    alarm = bool(result.constant_discrepancy.any()) or fraction > 0.01
    for name, first, second in (
        ('total_spikes', a.sum(axis=1), b.sum(axis=1)),
        (
            'active_neurons',
            (a > 0).sum(axis=1).astype(np.float64),
            (b > 0).sum(axis=1).astype(np.float64),
        ),
    ):
        w = welch(first[:, None], second[:, None])
        triggered = bool(abs(w.z[0]) >= 4)
        alarm |= triggered
        primary[name] = {
            'mean_a': float(w.mean_a[0]),
            'mean_b': float(w.mean_b[0]),
            'sample_variance_a': float(w.variance_a[0]),
            'sample_variance_b': float(w.variance_b[0]),
            'difference': float(w.difference[0]),
            'z': finite(float(w.z[0])),
            'welch_df': finite(float(w.degrees_freedom[0])),
            'constant_discrepancy': bool(w.constant_discrepancy[0]),
            'difference_ci95': [
                float(w.difference[0] - T29_95 * w.standard_error[0]),
                float(w.difference[0] + T29_95 * w.standard_error[0]),
            ],
            'gross_error_alarm': triggered,
        }
    interval = ratio_interval(a.sum(axis=1), b.sum(axis=1))
    return {
        'primary': primary,
        'gross_error_alarm': alarm,
        'per_neuron_support': len(ids),
        'active_union': int(active.sum()),
        'per_neuron_outliers': int(outliers.sum()),
        'active_outlier_fraction': fraction,
        'constant_discrepancies': int(result.constant_discrepancy.sum()),
        'count_ratio_ci95': interval,
        'count_margin_2pct': 'resolved-within-margin'
        if interval is not None and 0.98 <= interval[0] <= interval[1] <= 1.02
        else 'inconclusive-or-outside-margin',
        'eon': eon_metrics(a, b),
    }


class Finished(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    execution_complete: bool
    reused: list[Completed]
    completed: list[Completed]
    scope: str


def score(project: Path, campaign: Path, output: Path) -> dict[str, object]:
    require_retained_output(output.resolve(), project)
    manifest = Campaign.model_validate_json((campaign / 'campaign.json').read_text())
    finished = Finished.model_validate_json((campaign / 'result.json').read_text())
    records = finished.reused + finished.completed
    expected = jobs(manifest.silent_trials)
    if (
        not finished.execution_complete
        or manifest.jobs != expected
        or len(records) != len(expected)
        or {r.job for r in records} != set(expected)
    ):
        raise ValueError(
            'Scoring requires complete, unique prospective cohort coverage'
        )
    identity = sources(project)
    profile = Profile.model_validate_json(manifest.profile_path.read_text())
    if (
        digest(manifest.profile_path) != manifest.profile_sha256
        or manifest.source_sha256 != identity
    ):
        raise ValueError('Campaign profile or source binding changed')
    output.mkdir(parents=True, exist_ok=False)
    groups: dict[tuple[str, str], list[tuple[int, NDArray[np.float64]]]] = {}
    hashes: dict[tuple[str, int], str] = {}
    ids: NDArray[np.int64] | None = None
    receipts: dict[str, str] = {}
    for row in records:
        if digest(row.directory / 'trial.json') != row.trial_sha256:
            raise ValueError('Trial receipt changed')
        verify(
            row.directory, row.job, identity, profile.execution_identity[row.job.engine]
        )
        stimulus = json.loads((row.directory / 'stimulus.json').read_text())
        hashes[(row.job.experiment, row.job.trial)] = stimulus['canonical_event_sha256']
        with np.load(row.directory / 'spikes.npz', allow_pickle=False) as saved:
            neuron_ids, counts = saved['neuron_ids'], saved['counts']
            neurons, steps = saved['neuron_rows'], saved['steps']
        if (
            neuron_ids.dtype != np.int64
            or counts.dtype != np.int64
            or counts.shape != neuron_ids.shape
            or neuron_ids.ndim != 1
            or row.job.steps != 10000
            or np.any(counts < 0)
            or neurons.dtype != np.int64
            or steps.dtype != np.int64
            or neurons.shape != steps.shape
            or np.any(neurons < 0)
            or np.any(neurons >= len(neuron_ids))
            or np.any(steps < 0)
            or np.any(steps >= 10000)
            or len(set(zip(neurons.tolist(), steps.tolist(), strict=True)))
            != len(steps)
            or not np.array_equal(
                np.bincount(neurons, minlength=len(neuron_ids)), counts
            )
        ):
            raise ValueError('Native events, counts or mapping are invalid')
        if ids is None:
            ids = neuron_ids
        elif not np.array_equal(ids, neuron_ids):
            raise ValueError('Cohorts use different neuron ordering')
        cohort = (
            'Brian2'
            if row.job.engine == 'brian'
            else ('MLX-A' if row.job.trial < 1000 else 'MLX-B')
        )
        groups.setdefault((row.job.experiment, cohort), []).append(
            (row.job.trial, counts.astype(np.float64))
        )
        receipts[row.job.name] = row.trial_sha256
    if ids is None:
        raise ValueError('No neuron support supplied')
    for (experiment, trial), canonical_hash in hashes.items():
        if (
            experiment == 'sugar-silenced'
            and hashes.get(('sugar', trial)) != canonical_hash
        ):
            raise ValueError('Sugar and silenced cohorts did not reuse the same inputs')
    experiments: dict[str, object] = {}
    alarm = False
    for name in ('sugar', 'p9', 'sugar-silenced', 'two-class', 'silent'):
        data = {
            cohort: np.stack([counts for _, counts in sorted(groups[(name, cohort)])])
            for cohort in COHORTS
        }
        np.savez_compressed(output / (name + '-cohorts.npz'), neuron_ids=ids, **data)
        pairs: dict[str, object] = {}
        for a, b in combinations(COHORTS, 2):
            value: dict[str, object]
            if name == 'silent':
                silent_alarm = bool(np.any(data[a]) or np.any(data[b]))
                value = {
                    'gross_error_alarm': silent_alarm,
                    'exact_zero': not silent_alarm,
                    'welch': 'not applicable: deterministic silent control',
                    'eon': eon_metrics(data[a], data[b]),
                }
            else:
                value = compare(
                    data[a], data[b], ids, output / (name + '-' + a + '-vs-' + b)
                )
            pairs[a + '-vs-' + b] = value
            alarm |= bool(value['gross_error_alarm'])
        experiments[name] = pairs
    result: dict[str, object] = {
        'execution_complete': True,
        'gross_error_alarm': alarm,
        'scientific_acceptance': False,
        'experiments': experiments,
        'confidence_method': 'Estimated-variance Welch statistics, ddof=1; conservative df29 t=2.0452296421327043 for 95% difference/Fieller intervals. Normal-sample assumptions and low-count limitations apply; passing alarms is not equivalence.',
        'per_neuron_coverage': 'All pinned neurons, including low-rate and all-zero support; every outlier in CSV, full vectors in NPZ.',
        'timing_metrics': 'Independent seeds: timing F1 is not a distributional gate.',
        'eon_source': 'eonsystemspbc/fly-brain@a3db62f:code/compare_ground_truth.py; empty Jaccard=0 and undefined/constant Pearson=null.',
        'scorer_sha256': digest(Path(__file__)),
        'trial_receipt_sha256': receipts,
        'campaign_sha256': digest(campaign / 'campaign.json'),
        'scorer_commit': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip(),
    }
    (output / 'statistics.json').write_text(
        json.dumps(result, indent=2, allow_nan=False) + '\n'
    )
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path.cwd())
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = score(
        args.project.resolve(), args.campaign.resolve(), args.output.resolve()
    )
    print(
        json.dumps(
            {
                'gross_error_alarm': result['gross_error_alarm'],
                'report': str(args.output / 'statistics.json'),
            }
        )
    )
    raise SystemExit(1 if result['gross_error_alarm'] else 0)
