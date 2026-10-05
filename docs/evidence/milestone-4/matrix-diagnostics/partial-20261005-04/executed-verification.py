import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import numpy as np

from fly_brain.bootstrap import pinned_inputs
from fly_brain.comparison.models import SpikeSteps
from fly_brain.qualification.adjudication import require_reviewable, require_same_cause
from fly_brain.qualification.causality import CausalAudit
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.matrix_diagnostics import CaseRasters, summarize
from fly_brain.qualification.models import ParityCase


def encode(value):
    if isinstance(value, Fraction):
        return {
            'numerator': value.numerator,
            'denominator': value.denominator,
            'value': float(value),
        }
    raise TypeError(type(value).__name__)


root = Path.cwd()
output = Path(sys.argv[1]).resolve()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
connectome, pin = pinned_inputs(root)
mapping_digest = hashlib.sha256(connectome.neuron_ids.tobytes()).hexdigest()
rows, reports, failed, sources = [], {}, [], {}
reviewed, automatic_unaccepted = [], []
score_path = root / 'docs/evidence/milestone-4/case-adjudication/independent-score.py'
spec = importlib.util.spec_from_file_location(
    'independent_diagnostic_score', score_path
)
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)
for path in sorted((root / 'docs/evidence/milestone-4/cases').glob('*/case.json')):
    report = json.loads(path.read_text())
    case = ParityCase(**report['case'])
    assert case in required_cases() and case not in reports
    assert (
        report['input_pins'] == asdict(pin)
        and report['neuron_mapping_sha256'] == mapping_digest
    )
    rasters = {}
    artifact = path.parent / 'normalized-spikes.npz'
    with np.load(artifact, allow_pickle=False) as saved:
        for engine in ('brian', 'mlx', 'torch'):
            neurons, steps = saved[engine + '_neurons'], saved[engine + '_steps']
            assert (
                neurons.dtype == steps.dtype == np.int64
                and neurons.ndim == steps.ndim == 1
                and neurons.shape == steps.shape
            )
            assert np.isin(neurons, connectome.neuron_ids).all() and np.all(
                (steps >= 0) & (steps < case.steps)
            )
            assert len(
                set(zip(map(int, neurons), map(int, steps), strict=True))
            ) == len(steps)
            rasters[engine] = SpikeSteps(neurons, steps)
    rows.append(CaseRasters(case, rasters['brian'], rasters['mlx'], rasters['torch']))
    reports[case] = report
    if not report['case_accepted']:
        automatic_unaccepted.append(case)
        decision_path = path.parent / 'reviewed-decision.json'
        if decision_path.exists():
            decision = json.loads(decision_path.read_text())
            assert decision['case_accepted'] and not decision['full_matrix_accepted']
            assert decision['case'] == report['case']
            audit = CausalAudit()
            audit.step = report['causal']['steps']
            audit.first_spike_step = report['causal']['first_spike_step']
            audit.first_spike_neurons = tuple(report['causal']['first_spike_neurons'])
            assert report['causal']['first_budget_violation'] is None
            require_reviewable(
                case,
                report['case_checks'],
                report['metric_acceptance']['checks'],
                audit,
            )
            require_same_cause(
                case,
                audit,
                ParityCase(**decision['case']),
                decision['first_difference']['step'],
                tuple(decision['first_difference']['neurons']),
            )
            for name, digest in decision['local_evidence_sha256'].items():
                assert (
                    hashlib.sha256((path.parent / name).read_bytes()).hexdigest()
                    == digest
                )
            for name, digest in decision[
                'completed_review_policy_and_parent_applicability_sha256'
            ].items():
                assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
            verified = json.loads((path.parent / 'verification.json').read_text())
            assert (
                verified['case_accepted'] and not verified['automatic_report_accepted']
            )
            reviewed.append(case)
            sources[str(decision_path.relative_to(root))] = hashlib.sha256(
                decision_path.read_bytes()
            ).hexdigest()
        else:
            failed.append(case)
    for source in (path, artifact):
        sources[str(source.relative_to(root))] = hashlib.sha256(
            source.read_bytes()
        ).hexdigest()

groups = summarize(tuple(rows), failed=tuple(failed))
assert len(groups) == 12
assert sum(len(group.coverage.expected) for group in groups) == 52
assert sum(len(group.coverage.included) for group in groups) == len(rows)
assert sum(len(group.coverage.missing) for group in groups) == 52 - len(rows)
for group in groups:
    if not group.coverage.included:
        assert (
            group.metrics is None
            and group.pooled_bin_counts is None
            and not group.trial_bin_counts
        )
        continue
    assert group.metrics is not None and group.pooled_bin_counts is not None
    included = sorted(
        (
            row
            for row in rows
            if row.case.experiment == group.coverage.experiment
            and row.case.steps == group.coverage.steps
        ),
        key=lambda row: row.case.trial,
    )
    support = sorted(
        set().union(
            *(
                map(int, spikes.neurons)
                for row in included
                for spikes in (row.brian, row.mlx, row.torch)
            )
        )
    )
    for engine, metric in group.metrics.items():
        trials = tuple(
            (
                (row.brian.neurons, row.brian.steps),
                (getattr(row, engine).neurons, getattr(row, engine).steps),
            )
            for row in included
        )
        expected = scorer.score(trials, support, group.coverage.steps * 0.0001)
        actual = json.loads(json.dumps(asdict(metric), default=encode, allow_nan=False))
        scorer.verify_metrics(actual, expected)
    expected_pooled = {
        engine: [0] * (group.coverage.steps // 1000)
        for engine in ('brian', 'mlx', 'torch')
    }
    for row in included:
        for engine in expected_pooled:
            bins = [0] * len(expected_pooled[engine])
            for step in getattr(row, engine).steps:
                bins[int(step) // 1000] += 1
            assert group.trial_bin_counts[row.case.trial][engine] == tuple(bins)
            expected_pooled[engine] = [
                a + b for a, b in zip(expected_pooled[engine], bins, strict=True)
            ]
    assert group.pooled_bin_counts == {
        engine: tuple(bins) for engine, bins in expected_pooled.items()
    }

output.mkdir(parents=True, exist_ok=False)
report = {
    'checkpoint': subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], text=True
    ).strip(),
    'included_cases': [asdict(row.case) for row in rows],
    'included_count': len(rows),
    'missing_count': 52 - len(rows),
    'full_matrix_accepted': False,
    'groups': [asdict(group) for group in groups],
    'source_sha256': {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in (
            'src/fly_brain/qualification/matrix_diagnostics.py',
            'src/fly_brain/comparison/pooling.py',
            'src/fly_brain/comparison/diagnostics.py',
        )
    },
    'case_evidence_sha256': sources,
    'all_trial_separated_pooled_metrics_independently_verified': True,
    'all_trial_and_pooled_bins_independently_counted_from_actual_integer_coordinates': True,
    'automatic_unaccepted_cases_preserved': [
        asdict(case) for case in automatic_unaccepted
    ],
    'parent_reviewed_accepted_cases': [asdict(case) for case in reviewed],
    'scientifically_failed_valid_cases': [asdict(case) for case in failed],
    'independent_scorer_sha256': hashlib.sha256(score_path.read_bytes()).hexdigest(),
    'scope': 'Partial frozen matrix evidence; missing groups remain unavailable. Pooled diagnostics do not determine individual or matrix acceptance.',
}
with (output / 'partial-matrix.json').open('x') as destination:
    json.dump(report, destination, indent=2, default=encode, allow_nan=False)
shutil.copyfile(__file__, output / 'executed-verification.py')
print(
    json.dumps(
        {
            'verified': True,
            'included': len(rows),
            'missing': 52 - len(rows),
            'groups': len(groups),
        }
    ),
    flush=True,
)
