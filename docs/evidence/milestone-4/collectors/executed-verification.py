import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np

root = Path.cwd()
source = root / 'data/results/milestone-4-collector-regression-20261005-01'
destination = root / 'docs/evidence/milestone-4/collectors'
checkpoint = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
assert not subprocess.check_output(['git', 'status', '--porcelain'])
result = json.loads((source / 'result.json').read_text())
assert result['accepted'] and result['exit_code'] == 0
assert result['tests'] > 0 and all(result[name] == 0 for name in ('failures', 'errors', 'skipped'))
destination.mkdir(parents=True, exist_ok=False)
quality = []
for arguments in (
    ('ruff', 'format', '--check', '.'), ('ruff', 'check', '.'), ('pyright',),
    ('lint-imports', '--no-cache'), ('uv', 'lock', '--check', '--offline'),
):
    command = list(arguments) if arguments[0] == 'uv' else ['uv', 'run', '--locked', '--group', 'qualification', '--no-sync', *arguments]
    checked = subprocess.run(command, capture_output=True, text=True, check=True)
    quality.append({'command': command, 'stdout': checked.stdout, 'stderr': checked.stderr})
with (destination / 'quality.json').open('x') as artifact:
    json.dump(quality, artifact, indent=2)
for name in ('tests.xml', 'qualification.log', 'result.json'):
    shutil.copyfile(source / name, destination / name)
shutil.copyfile(root / 'data/results/milestone-4-collector-application-20261005-01.xml', destination / 'application-tests.xml')
traces = sorted(source.rglob('*.npz'))
assert traces
manifest = {}
array_count = 0
with zipfile.ZipFile(destination / 'traces.zip', 'x', compression=zipfile.ZIP_STORED) as archive:
    for path in traces:
        relative = str(path.relative_to(source))
        archive.write(path, relative)
        with np.load(path, allow_pickle=False) as arrays:
            array_count += len(arrays.files)
        manifest[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
with zipfile.ZipFile(destination / 'traces.zip') as archive:
    assert set(archive.namelist()) == set(manifest)
    assert all(hashlib.sha256(archive.read(name)).hexdigest() == digest for name, digest in manifest.items())
numerical_sources = (
    'src/fly_brain/simulation/backend',
    'src/fly_brain/qualification/adapters/brian_jobs.py',
    'src/fly_brain/qualification/adapters/torch_reference.py',
    'src/fly_brain/qualification/adapters/torch_setup.py',
    'pyproject.toml', 'uv.lock',
)
assert not subprocess.check_output(['git', 'diff', '7b70c29', '--', *numerical_sources])
suites = tuple(ET.parse(destination / 'application-tests.xml').getroot().iter('testsuite'))
counts = {key: sum(int(suite.get(key, '0')) for suite in suites) for key in ('tests', 'failures', 'errors', 'skipped')}
assert counts['tests'] > 0 and all(counts[key] == 0 for key in ('failures', 'errors', 'skipped'))
source_files = sorted((root / 'src/fly_brain').rglob('*.py'))
with (destination / 'verification.json').open('x') as artifact:
    json.dump({
        'checkpoint': checkpoint, 'scientific_result': result, 'application_tests': counts,
        'trace_files': len(traces), 'trace_arrays': array_count,
        'every_zipped_trace_sha256_matches_original': True, 'trace_sha256': manifest,
        'numerical_sources_and_dependencies_unchanged_since': '7b70c29',
        'observer_changes': 'MLX and CPU observers now declare their actual closable generator return type; execution bodies are unchanged.',
        'source_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files},
        'accepted_full_network_cases': 1, 'required_full_network_cases': 52,
        'full_matrix_accepted': False,
    }, artifact, indent=2)
shutil.copyfile(__file__, destination / 'executed-verification.py')
print(json.dumps({'scientific_tests': result['tests'], 'application_tests': counts['tests'], 'trace_files': len(traces), 'trace_arrays': array_count}), flush=True)
