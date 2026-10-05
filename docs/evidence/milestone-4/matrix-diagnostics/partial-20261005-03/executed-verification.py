import hashlib
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
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.matrix_diagnostics import CaseRasters, summarize
from fly_brain.qualification.models import ParityCase


def encode(value):
    if isinstance(value, Fraction):
        return {'numerator': value.numerator, 'denominator': value.denominator, 'value': float(value)}
    raise TypeError(type(value).__name__)


root = Path.cwd()
output = Path(sys.argv[1]).resolve()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
connectome, pin = pinned_inputs(root)
mapping_digest = hashlib.sha256(connectome.neuron_ids.tobytes()).hexdigest()
rows, reports, failed, sources = [], {}, [], {}
for path in sorted((root / 'docs/evidence/milestone-4/cases').glob('*/case.json')):
    report = json.loads(path.read_text())
    case = ParityCase(**report['case'])
    assert case in required_cases() and case not in reports
    assert report['input_pins'] == asdict(pin) and report['neuron_mapping_sha256'] == mapping_digest
    rasters = {}
    artifact = path.parent / 'normalized-spikes.npz'
    with np.load(artifact, allow_pickle=False) as saved:
        for engine in ('brian', 'mlx', 'torch'):
            neurons, steps = saved[engine + '_neurons'], saved[engine + '_steps']
            assert neurons.dtype == steps.dtype == np.int64 and neurons.ndim == steps.ndim == 1 and neurons.shape == steps.shape
            assert np.isin(neurons, connectome.neuron_ids).all() and np.all((steps >= 0) & (steps < case.steps))
            assert len(set(zip(map(int, neurons), map(int, steps), strict=True))) == len(steps)
            rasters[engine] = SpikeSteps(neurons, steps)
    rows.append(CaseRasters(case, rasters['brian'], rasters['mlx'], rasters['torch']))
    reports[case] = report
    if not report['case_accepted']:
        failed.append(case)
    for source in (path, artifact):
        sources[str(source.relative_to(root))] = hashlib.sha256(source.read_bytes()).hexdigest()

groups = summarize(tuple(rows), failed=tuple(failed))
assert len(groups) == 12
assert sum(len(group.coverage.expected) for group in groups) == 52
assert sum(len(group.coverage.included) for group in groups) == len(rows)
assert sum(len(group.coverage.missing) for group in groups) == 52 - len(rows)
for group in groups:
    if not group.coverage.included:
        assert group.metrics is None and group.pooled_bin_counts is None and not group.trial_bin_counts
        continue
    assert group.metrics is not None and group.pooled_bin_counts is not None
    assert group.coverage.steps == 1000 and len(group.coverage.included) == 1
    case = ParityCase(group.coverage.experiment, group.coverage.steps, group.coverage.included[0])
    for engine, metric in group.metrics.items():
        encoded = json.loads(json.dumps(asdict(metric), default=encode, allow_nan=False))
        assert encoded == reports[case]['metric_acceptance'][engine], (case, engine)
    for engine in ('brian', 'mlx', 'torch'):
        expected = group.metrics['mlx'].reference_spikes if engine == 'brian' else group.metrics[engine].candidate_spikes
        assert group.trial_bin_counts[case.trial][engine] == group.pooled_bin_counts[engine] == (expected,)

output.mkdir(parents=True, exist_ok=False)
report = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'included_cases': [asdict(row.case) for row in rows],
    'included_count': len(rows), 'missing_count': 52 - len(rows),
    'full_matrix_accepted': False, 'groups': [asdict(group) for group in groups],
    'source_sha256': {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ('src/fly_brain/qualification/matrix_diagnostics.py', 'src/fly_brain/comparison/pooling.py', 'src/fly_brain/comparison/diagnostics.py')},
    'case_evidence_sha256': sources,
    'all_single_trial_pooled_metrics_equal_recorded_complete_case_metrics': True,
    'all_bin_counts_equal_recorded_spike_counts': True,
    'scope': 'Partial frozen matrix evidence; missing groups remain unavailable. Pooled diagnostics do not determine individual or matrix acceptance.',
}
with (output / 'partial-matrix.json').open('x') as destination:
    json.dump(report, destination, indent=2, default=encode, allow_nan=False)
shutil.copyfile(__file__, output / 'executed-verification.py')
print(json.dumps({'verified': True, 'included': len(rows), 'missing': 52 - len(rows), 'groups': len(groups)}), flush=True)
