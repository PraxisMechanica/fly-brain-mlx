import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import numpy as np

root = Path('/Users/ocasta/Code/fly-brain')
source = root / 'data/results/performance-remediation-exact-count-full-native-20261005'
original = root / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01'
sealed = root / 'docs/evidence/milestone-4/one-second-sugar-metric-failure/completed-case'
destination = root / 'docs/evidence/execution-time-investigation/exact-count-reduction/full-native'
result = json.loads((source / 'result.json').read_text())
hash_file = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert hash_file(Path('/private/tmp/fly-brain-exact-count-full-native-20261005.py')) == result['runner_sha256']
for path, digest in result['source_sha256'].items():
    assert hash_file(root / path) == digest, path
assert (sealed / 'case.json').read_bytes() == (original / 'case.json').read_bytes()
case = json.loads((sealed / 'case.json').read_text())
assert not case['case_accepted'] and not case['metric_acceptance']['checks']['timing_floor']
coverage = {}
with zipfile.ZipFile(sealed / 'observations.zip') as archive:
    for name in ('first', 'repeat'):
        oracle = original / 'observations' / ('paired-' + name)
        run = source / name
        for filename in ('phase-digests.jsonl', 'mlx-native.npz'):
            suffix = 'paired-' + name + '/' + filename
            member = next(value for value in archive.namelist() if value.endswith(suffix))
            assert archive.read(member) == (oracle / filename).read_bytes()
        expected = [json.loads(row) for row in (oracle / 'phase-digests.jsonl').read_text().splitlines()]
        actual = [json.loads(row) for row in (run / 'phase-digests.jsonl').read_text().splitlines()]
        assert len(actual) == len(expected) == 313
        assert sum(row['rows'] for row in actual) == 10000
        for a, b in zip(actual, expected, strict=True):
            assert (a['begin'], a['rows'], a['native_phase_sha256'], a['mlx_queue_sha256'], a['mlx_due_sha256']) == (b['begin'], b['rows'], b['native_phase_sha256'][1], b['mlx_queue_sha256'], b['mlx_due_sha256'])
        with np.load(run / 'native.npz', allow_pickle=False) as a, np.load(oracle / 'mlx-native.npz', allow_pickle=False) as b:
            assert set(a.files) == set(b.files)
            for field in a.files:
                av, bv = a[field], b[field]
                assert (av.dtype.str, av.shape, av.tobytes()) == (bv.dtype.str, bv.shape, bv.tobytes()), (name, field)
        assert hash_file(run / 'native.npz') == result['runs'][name]['native_sha256']
        assert hash_file(run / 'phase-digests.jsonl') == result['runs'][name]['phase_sha256']
        coverage[name] = {'steps': 10000, 'queue_boundaries': 313, 'native_and_raster_exact': True}
with np.load(source / 'fresh-process-layout/device-layout.npz', allow_pickle=False) as a, np.load(root / 'docs/evidence/milestone-2/buckets/device-layout/device-layout.npz', allow_pickle=False) as b:
    assert a.files == b.files
    for field in a.files:
        av, bv = a[field], b[field]
        assert (av.dtype.str, av.shape, av.tobytes()) == (bv.dtype.str, bv.shape, bv.tobytes()), field
destination.mkdir(parents=True, exist_ok=False)
shutil.copytree(source, destination, dirs_exist_ok=True)
shutil.copy2('/private/tmp/fly-brain-exact-count-full-native-20261005.py', destination / 'executed-witness.py')
shutil.copy2(__file__, destination / 'executed-parent-verifier.py')
proof = {'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'original_case_sha256': hash_file(sealed / 'case.json'), 'original_observations_sha256': hash_file(sealed / 'observations.zip'), 'complete_original_archive_binding': True, 'runs': coverage, 'complete_fresh_process_layout_matches': True, 'source_inventory_verified': result['source_sha256'], 'parent_verifier_sha256': hash_file(Path(__file__)), 'known_original_metric_failure_preserved': True, 'scope': 'Same-engine qualification only; no cross-engine acceptance or whole-check performance claim.'}
(destination / 'parent-verification.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps({'accepted': True, 'coverage': coverage, 'destination': str(destination)}))
