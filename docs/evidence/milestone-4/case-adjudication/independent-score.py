import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path


def grouped(spikes):
    groups = defaultdict(list)
    for neuron, step in zip(*spikes, strict=True):
        groups[int(neuron)].append(int(step))
    return {neuron: sorted(steps) for neuron, steps in groups.items()}


def matched(first, second, window):
    errors = []
    maximum = 0
    for neuron in first.keys() & second.keys():
        a, b = first[neuron], second[neuron]
        remaining = iter(b)
        candidate = next(remaining, None)
        for expected in a:
            while candidate is not None and candidate < expected - window:
                candidate = next(remaining, None)
            if candidate is not None and candidate <= expected + window:
                errors.append(abs(candidate - expected))
                candidate = next(remaining, None)
        previous = [0] * (len(b) + 1)
        for expected in a:
            current = [0]
            for index, candidate in enumerate(b, 1):
                current.append(
                    max(
                        current[-1],
                        previous[index],
                        previous[index - 1] + (abs(expected - candidate) <= window),
                    )
                )
            previous = current
        maximum += previous[-1]
    assert len(errors) == maximum
    return errors


def correlation(first, second):
    if len(first) < 2 or len(set(first)) < 2 or len(set(second)) < 2:
        return None
    return statistics.correlation(first, second)


def score(trials, support, duration_s):
    assert trials
    first, second = Counter(), Counter()
    errors = {window: [] for window in (0, 1, 10)}
    for reference, candidate in trials:
        a, b = grouped(reference), grouped(candidate)
        first.update({neuron: len(steps) for neuron, steps in a.items()})
        second.update({neuron: len(steps) for neuron, steps in b.items()})
        for window in errors:
            errors[window].extend(matched(a, b, window))
    nb, nx = sum(first.values()), sum(second.values())
    total, matches = nb + nx, len(errors[10])
    union, shared = first.keys() | second.keys(), first.keys() & second.keys()
    a, b = [first[n] for n in support], [second[n] for n in support]
    rate_errors = [(second[n] - first[n]) / (len(trials) * duration_s) for n in support]
    return {
        'reference_spikes': nb,
        'candidate_spikes': nx,
        'active_jaccard': Fraction(len(shared), len(union)) if union else Fraction(1),
        'count_error': Fraction(abs(nx - nb), nb)
        if nb
        else None
        if nx
        else Fraction(0),
        'signed_count_ratio': Fraction(nx, nb) if nb else None,
        'neuron_count_error': Fraction(
            sum(abs(first[n] - second[n]) for n in support), nb
        )
        if nb
        else None
        if nx
        else Fraction(0),
        'rate_correlation': correlation(a, b),
        'counts_equal': a == b,
        'timing_matches': matches,
        'timing_f1': Fraction(2 * matches, total) if total else Fraction(1),
        'timing_precision': Fraction(matches, nx) if nx else Fraction(not nb),
        'timing_recall': Fraction(matches, nb) if nb else Fraction(not nx),
        'exact_step_f1': Fraction(2 * len(errors[0]), total) if total else Fraction(1),
        'one_step_f1': Fraction(2 * len(errors[1]), total) if total else Fraction(1),
        'mean_timing_error_ms': statistics.mean(errors[10]) * 0.1
        if errors[10]
        else None,
        'median_timing_error_ms': statistics.median(errors[10]) * 0.1
        if errors[10]
        else None,
        'shared_rate_correlation': correlation(
            [first[n] for n in shared], [second[n] for n in shared]
        ),
        'common_rate_mae_hz': statistics.mean(map(abs, rate_errors))
        if support
        else None,
        'common_rate_rmse_hz': math.sqrt(
            statistics.mean(value * value for value in rate_errors)
        )
        if support
        else None,
    }


def gates(mlx, torch):
    def no_greater(a, b):
        return a is not None and (b is None or a <= b)

    return {
        'silent_reference_exact': bool(
            mlx['reference_spikes'] or not mlx['candidate_spikes']
        ),
        'activity_floor': mlx['active_jaccard'] >= Fraction(19, 20),
        'activity_paired': mlx['active_jaccard'] >= torch['active_jaccard'],
        'count_floor': no_greater(mlx['count_error'], Fraction(1, 50)),
        'count_paired': no_greater(mlx['count_error'], torch['count_error']),
        'neuron_count_floor': no_greater(mlx['neuron_count_error'], Fraction(1, 20)),
        'neuron_count_paired': no_greater(
            mlx['neuron_count_error'], torch['neuron_count_error']
        ),
        'correlation_floor_or_exact_counts': mlx['rate_correlation'] >= 0.99
        if mlx['rate_correlation'] is not None
        else mlx['counts_equal'],
        'correlation_paired': mlx['rate_correlation'] is None
        or torch['rate_correlation'] is None
        or mlx['rate_correlation'] >= torch['rate_correlation'] - 1e-12,
        'timing_floor': mlx['timing_f1'] >= Fraction(19, 20),
        'timing_paired': mlx['timing_f1'] >= torch['timing_f1'],
    }


def verify_metrics(actual, expected):
    assert set(actual) == set(expected) and len(expected) == 19
    for name, value in expected.items():
        if isinstance(value, Fraction):
            assert (
                Fraction(actual[name]['numerator'], actual[name]['denominator'])
                == value
            ), name
            assert actual[name]['value'] == float(value), name
        elif isinstance(value, float):
            assert math.isfinite(value) and math.isfinite(actual[name])
            assert math.isclose(actual[name], value, rel_tol=1e-12, abs_tol=1e-12), name
        else:
            assert actual[name] == value, name


def encode(value):
    if isinstance(value, Fraction):
        return {
            'numerator': value.numerator,
            'denominator': value.denominator,
            'value': float(value),
        }
    raise TypeError(type(value).__name__)


if __name__ == '__main__':
    import numpy as np

    root = Path.cwd()
    results = {}
    sources = {}
    for name in ('sugar', 'p9', 'sugar-silenced', 'two-class', 'silent'):
        folder = root / f'docs/evidence/milestone-4/cases/{name}-1000-0'
        report = json.loads((folder / 'case.json').read_text())
        with np.load(folder / 'normalized-spikes.npz', allow_pickle=False) as z:
            spikes = {
                engine: (z[engine + '_neurons'], z[engine + '_steps'])
                for engine in ('brian', 'mlx', 'torch')
            }
            support = sorted(
                set().union(*(map(int, rows[0]) for rows in spikes.values()))
            )
            metrics = {
                engine: score(((spikes['brian'], spikes[engine]),), support, 0.1)
                for engine in ('mlx', 'torch')
            }
        for engine in metrics:
            verify_metrics(report['metric_acceptance'][engine], metrics[engine])
        checks = gates(metrics['mlx'], metrics['torch'])
        assert checks == report['metric_acceptance']['checks'] and all(checks.values())
        results[name] = {'metrics': metrics, 'checks': checks}
        for path in (folder / 'case.json', folder / 'normalized-spikes.npz'):
            sources[str(path.relative_to(root))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    empty = ([], [])
    active = ([7], [999])
    exchanged = score(((active, empty), (empty, active)), [7], 0.1)
    assert exchanged['counts_equal'] and exchanged['timing_f1'] == 0
    record = {
        'checkpoint': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], text=True
        ).strip(),
        'cases': results,
        'source_artifact_sha256': sources,
        'all_19_metric_fields_and_11_gates_recomputed_for_all_five_actual_cases': True,
        'all_timing_window_cardinalities_verified_by_dynamic_program': True,
        'cross_trial_matches_refused': True,
        'float_diagnostic_verification_only': '1e-12 host comparison for independently evaluated diagnostic floats; never used to relax a gate. Primary rational gates exact and paired correlation retains its frozen 1e-12 slack.',
        'full_matrix_accepted': False,
        'case_accepted_by_this_regression': False,
    }
    with Path(sys.argv[1]).open('x') as destination:
        json.dump(record, destination, indent=2, default=encode, allow_nan=False)
    print(
        json.dumps(
            {
                'verified': True,
                'actual_cases': len(results),
                'metric_fields': 19,
                'frozen_checks': 11,
                'cross_trial_matches_refused': True,
            }
        )
    )
