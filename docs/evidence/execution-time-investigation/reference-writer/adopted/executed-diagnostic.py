import ast
import hashlib
import json
import re
import statistics
import struct
import subprocess
import time
import zlib
from pathlib import Path

import numpy as np

root = Path('/Users/ocasta/Code/fly-brain')
output = Path('/private/tmp/fly-brain-adopted-writer-check-20261005')
output.mkdir(exist_ok=False)
source = root / 'src/fly_brain/qualification/adapters/brian_observer.py'
function = next(n for n in ast.parse(source.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'install')
setup = next(n.value.value for n in function.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'setup' for t in n.targets))
writer = re.search(r'static auto obs_write = .*?\n};', setup, re.S).group().replace('static auto obs_write', 'auto fast_write')
old = root / 'docs/evidence/execution-time-investigation/reference-writer/writer.cpp'
cpp = re.sub(r'auto fast_write=.*?\n    };', writer, old.read_text(), count=1, flags=re.S)
assert 'crc32_z(' in cpp
(output / 'writer.cpp').write_text(cpp)
endpoint = root / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/paired-first/reference-native.npz'
with np.load(endpoint, allow_pickle=False) as saved, (output / 'input.bin').open('xb') as stream:
    stream.write(struct.pack('<QQ', saved['v'].size, 32))
    for field in ('v', 'g', 'lastspike', 'not_refractory'):
        stream.write(saved[field].tobytes())
flags = ['-std=c++17', '-O3', '-ffast-math', '-fno-finite-math-only', '-lz']
subprocess.run(['/usr/bin/clang++', *flags, str(output / 'writer.cpp'), '-o', str(output / 'writer')], check=True, capture_output=True, timeout=30)
records = {'original': [], 'adopted': []}
expected = None
for repeat in range(3):
    for mode, label in ((0, 'original'), (2, 'adopted')):
        began = time.perf_counter()
        process = subprocess.Popen([str(output / 'writer'), str(mode), str(output / 'input.bin')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        digest, checksum, tail, size = hashlib.sha256(), 0, b'', 0
        while chunk := process.stdout.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
            joined = tail + chunk
            checksum = zlib.crc32(joined[:-4], checksum)
            tail = joined[-4:]
        details = json.loads(process.stderr.read())
        assert process.wait(timeout=5) == 0
        assert struct.unpack('<I', tail)[0] == checksum
        actual = digest.hexdigest()
        expected = actual if expected is None else expected
        assert actual == expected and size == 261751204
        records[label].append({'wall_s': time.perf_counter() - began, 'bytes': size, 'sha256': actual, **details})
record = {'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(), 'scope': 'Adopted writer component only, using repeated retained endpoint arrays; complete physical frame qualification is separate.', 'measurements': {name: {'samples': rows, 'median_wall_s': statistics.median(r['wall_s'] for r in rows), 'median_cpu_s': statistics.median(r['producer_cpu_s'] for r in rows)} for name, rows in records.items()}, 'all_six_complete_payload_hashes_and_crc32_match': True, 'flags': flags, 'application_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'reference_artifact_sha256': hashlib.sha256(endpoint.read_bytes()).hexdigest(), 'cpp_sha256': hashlib.sha256(cpp.encode()).hexdigest(), 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'zlib_runtime': zlib.ZLIB_RUNTIME_VERSION}
(output / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'output': str(output), 'medians': {n: {'wall_s': r['median_wall_s'], 'cpu_s': r['median_cpu_s']} for n, r in record['measurements'].items()}}))
