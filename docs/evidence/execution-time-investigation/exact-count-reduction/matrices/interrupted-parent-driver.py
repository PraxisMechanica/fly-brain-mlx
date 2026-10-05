import hashlib
import json
import shutil
import subprocess
from pathlib import Path
import numpy as np

root = Path('/Users/ocasta/Code/fly-brain')
source = root / 'data/results/performance-remediation-exact-count-matrices-20261005'
layout = root / 'data/results/performance-remediation-exact-count-layout-20261005'
archive = root / 'docs/evidence/execution-time-investigation/exact-count-reduction/matrices'
archive.mkdir(exist_ok=False)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def equal(left, right, name):
    assert (left.dtype.str, left.shape, left.tobytes()) == (right.dtype.str, right.shape, right.tobytes()), name
scalars = json.loads((source / 'scalars/bucketed-scalars.json').read_text())
pinned = json.loads((source / 'pinned/fan-in.json').read_text())
assert scalars['accepted'] and scalars['cases'] == 157
assert pinned['accepted'] and pinned['cases'] == 24576 and pinned['original_one_step_conversion_failures'] == 99
scalar_fields = 0
scalar_payload = {}
for path in sorted((source / 'scalars').glob('case-*.npz')):
    original = root / 'docs/evidence/milestone-2/buckets/scalars' / path.name
    with np.load(original, allow_pickle=False) as expected, np.load(path, allow_pickle=False) as actual:
        assert expected.files == actual.files
        for field in expected.files:
            equal(expected[field], actual[field], path.name + ':' + field)
            scalar_payload[path.stem.replace('-', '_') + '_' + field] = actual[field]
            scalar_fields += 1
pinned_payload = {}
pinned_fields = 0
original_pinned = root / 'docs/evidence/milestone-2/buckets/pinned-replay/inputs-and-results.npz'
with np.load(original_pinned, allow_pickle=False) as expected:
    for row in pinned['measurements']:
        path = source / 'pinned' / row['artifact']
        assert digest(path) == row['artifact_sha256']
        prefix = 'target_' + str(row['target']) + '_'
        with np.load(path, allow_pickle=False) as actual:
            for field in actual.files:
                if field == 'leaves32':
                    counts = actual['signed_counts']
                    for index in range(actual['mask_indices'].size):
                        order = actual['orders'][actual['order_indices'][index]]
                        mask = actual['masks'][actual['mask_indices'][index]][order]
                        wanted = np.where(mask, counts[order], 0).astype(np.float32)
                        equal(actual[field][index][:wanted.size], wanted, path.name + ':' + field + ':' + str(index))
                    continue
                equal(expected[prefix + field], actual[field], path.name + ':' + field)
                pinned_payload[prefix + field] = actual[field]
                pinned_fields += 1
with np.load(root / 'docs/evidence/milestone-2/buckets/device-layout/device-layout.npz', allow_pickle=False) as expected, np.load(layout / 'device-layout.npz', allow_pickle=False) as actual:
    assert expected.files == actual.files
    for field in expected.files:
        equal(expected[field], actual[field], 'device-layout:' + field)
    layout_fields = len(expected.files)
with (archive / 'scalars.npz').open('xb') as out:
    np.savez_compressed(out, **scalar_payload)
with (archive / 'pinned-inputs-results.npz').open('xb') as out:
    np.savez_compressed(out, **pinned_payload)
for src, name in ((source / 'scalars/bucketed-scalars.json','scalar-report.json'),(source / 'pinned/fan-in.json','pinned-report.json'),(layout / 'device-layout.json','layout-report.json'),(layout / 'device-layout.npz','device-layout.npz'),(layout / 'verification.json','layout-verification.json'),(Path('/private/tmp/fly-brain-exact-count-qualification-20261005.py'),'executed-matrix-driver.py'),(Path('/private/tmp/fly-brain-exact-count-layout-check-20261005.py'),'executed-layout-driver.py')):
    shutil.copyfile(src, archive / name)
shutil.copyfile(Path(__file__), archive / 'executed-parent-verification.py')
record = {
    'checkpoint': subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
    'scalars': {'cases':157,'fields_compared':scalar_fields,'all_native_inputs_references_outputs_repeat_and_standalone_bytes_match_oracle':True,'exact_reduction_cases':sum(row['count_reduction']=='exact-integer' for row in scalars['measurements']),'oracle_fallback_cases':sum(row['count_reduction']=='compensated-tree' for row in scalars['measurements'])},
    'pinned': {'cases':24576,'targets':31,'fields_compared':pinned_fields,'all_complete_native_inputs_references_outputs_repeat_and_standalone_bytes_match_oracle':True,'original_one_step_conversion_limitations':99,'dense_leaves_reconstructed_and_verified':True,'local_originals_preserved':str(source)},
    'layout': {'buckets':15,'fields_compared':layout_fields,'all_native_arrays_match_retained_oracle':True},
    'execution_failures': ['Initial matrix driver completed scalar and pinned matrices, then failed before layout accumulation because a Boolean keyword reused a local array name. Corrected separate layout driver passed. No prior output was overwritten.'],
    'limits': 'Candidate disabled in normal execution. Full-network closed trajectory and fresh-process repeat qualification remain open; these results confer no new case acceptance.',
    'artifacts': {p.name:digest(p) for p in sorted(archive.iterdir()) if p.is_file()},
    'source_sha256': {str(p.relative_to(root)):digest(p) for p in (root/'src/fly_brain/simulation/backend/bucketed.py',root/'src/fly_brain/simulation/backend/accumulation.py',root/'src/fly_brain/qualification/adapters/device_layout_probe.py')}
}
(archive / 'parent-verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'verified':True,'scalars':157,'pinned':24576,'layout_fields':layout_fields,'archive':str(archive)}))
