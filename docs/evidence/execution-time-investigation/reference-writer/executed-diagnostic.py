import ast
import hashlib
import json
import signal
import statistics
import struct
import subprocess
import time
import zlib
from pathlib import Path

import numpy as np

ROOT = Path('/Users/ocasta/Code/fly-brain')
OUT = Path('/private/tmp/fly-brain-writer-performance-20261005-01')
OUT.mkdir(exist_ok=False)
signal.alarm(90)
source_path = ROOT / 'src/fly_brain/qualification/adapters/brian_observer.py'
parsed = ast.parse(source_path.read_text())
install = next(n for n in parsed.body if isinstance(n, ast.FunctionDef) and n.name == 'install')
setup = next(n.value.value for n in install.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'setup' for t in n.targets))
assert 'std::cout.write' in setup and 'for(size_t i=0; i<size; ++i)' in setup
endpoint = ROOT / 'data/results/milestone-4-parity-sugar-10000-0-20261005-01/observations/paired-first/reference-native.npz'
with np.load(endpoint, allow_pickle=False) as saved:
    arrays = tuple(saved[name].copy() for name in ('v', 'g', 'lastspike', 'not_refractory'))
neurons = arrays[0].size
rows = 32
with (OUT / 'input.bin').open('xb') as stream:
    stream.write(struct.pack('<QQ', neurons, rows))
    for array in arrays:
        stream.write(array.tobytes())
cpp = r'''
#include <chrono>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iostream>
#include <vector>
#include <zlib.h>

template<bool Buffered, typename Writer>
void emit_phases(size_t neurons, size_t rows, const std::vector<double>& v,
                 const std::vector<double>& g, const std::vector<double>& last,
                 const std::vector<uint8_t>& mask, Writer& write) {
    std::vector<double> times(rows);
    std::vector<uint8_t> canonical(neurons);
    for(size_t row=0; row<rows; ++row) times[row]=row*0.0001;
    for(int phase=0; phase<3; ++phase) {
        write(times.data(), rows*sizeof(double));
        for(size_t row=0; row<rows; ++row) write(v.data(), neurons*sizeof(double));
        for(size_t row=0; row<rows; ++row) write(g.data(), neurons*sizeof(double));
        if(phase==2) for(size_t row=0; row<rows; ++row) write(last.data(), neurons*sizeof(double));
        for(size_t row=0; row<rows; ++row) {
            if constexpr(Buffered) {
                for(size_t neuron=0; neuron<neurons; ++neuron) canonical[neuron]=mask[neuron] ? 1 : 0;
                write(canonical.data(), neurons);
            } else {
                for(size_t neuron=0; neuron<neurons; ++neuron) {
                    const uint8_t value=mask[neuron] ? 1 : 0;
                    write(&value, 1);
                }
            }
        }
    }
}

int main(int argc, char** argv) {
    if(argc!=3) return 2;
    const int mode=std::atoi(argv[1]);
    std::ifstream input(argv[2], std::ios::binary);
    uint64_t neurons, rows;
    input.read(reinterpret_cast<char*>(&neurons), 8);
    input.read(reinterpret_cast<char*>(&rows), 8);
    std::vector<double> v(neurons), g(neurons), last(neurons);
    std::vector<uint8_t> mask(neurons);
    input.read(reinterpret_cast<char*>(v.data()), neurons*8);
    input.read(reinterpret_cast<char*>(g.data()), neurons*8);
    input.read(reinterpret_cast<char*>(last.data()), neurons*8);
    input.read(reinterpret_cast<char*>(mask.data()), neurons);
    if(!input) return 3;
__ORIGINAL_SETUP__
    auto fast_write=[](const void* pointer, size_t size) {
        if(size) {
            const auto* data=static_cast<const unsigned char*>(pointer);
            std::cout.write(reinterpret_cast<const char*>(data), size);
            obs_crc=static_cast<uint32_t>(crc32(obs_crc^0xffffffffu, data, static_cast<uInt>(size)))^0xffffffffu;
        }
    };
    const auto began=std::chrono::steady_clock::now();
    const auto cpu_began=std::clock();
    if(mode==0) emit_phases<false>(neurons, rows, v, g, last, mask, obs_write);
    else if(mode==1) emit_phases<true>(neurons, rows, v, g, last, mask, obs_write);
    else if(mode==2) emit_phases<true>(neurons, rows, v, g, last, mask, fast_write);
    else return 4;
    obs_finish();
    std::cout.flush();
    const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count();
    const double cpu=static_cast<double>(std::clock()-cpu_began)/CLOCKS_PER_SEC;
    std::cerr << "{\"producer_wall_s\":" << elapsed << ",\"producer_cpu_s\":" << cpu << "}";
    return std::cout ? 0 : 5;
}
'''.replace('__ORIGINAL_SETUP__', setup)
(OUT / 'writer.cpp').write_text(cpp)
compiler = '/usr/bin/clang++'
flags = ['-std=c++17', '-O3', '-ffast-math', '-fno-finite-math-only', '-lz']
compilation = subprocess.run([compiler, *flags, str(OUT / 'writer.cpp'), '-o', str(OUT / 'writer')], capture_output=True, text=True, timeout=30, check=True)
records = {name: [] for name in ('original_tiny_boolean_writes_bytewise_crc', 'buffered_booleans_same_crc', 'buffered_booleans_native_zlib_crc')}
expected_digest = None
started = time.perf_counter()
for repeat in range(3):
    for mode, name in enumerate(records):
        before = time.perf_counter()
        process = subprocess.Popen([str(OUT / 'writer'), str(mode), str(OUT / 'input.bin')], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        digest = hashlib.sha256()
        checksum = 0
        tail = b''
        size = 0
        while chunk := process.stdout.read(1024 * 1024):
            size += len(chunk)
            digest.update(chunk)
            joined = tail + chunk
            checksum = zlib.crc32(joined[:-4], checksum)
            tail = joined[-4:]
        stderr = process.stderr.read().decode()
        returncode = process.wait(timeout=5)
        elapsed = time.perf_counter() - before
        assert returncode == 0, stderr
        assert size == rows * neurons * 59 + 3 * rows * 8 + 4
        assert len(tail) == 4 and struct.unpack('<I', tail)[0] == checksum
        actual_digest = digest.hexdigest()
        if expected_digest is None:
            expected_digest = actual_digest
        assert actual_digest == expected_digest
        sample = {'wall_s': elapsed, 'output_bytes': size, 'output_sha256': actual_digest, 'stream_checksum_independently_matches': True, **json.loads(stderr)}
        records[name].append(sample)
        print(json.dumps({'phase': 'measured', 'mode': name, 'repeat': repeat, **sample}), flush=True)
record = {
    'checkpoint': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'scope': 'Bounded serialization diagnostic. Synthetic 32-row phase payload repeats actual retained native reference endpoint arrays. It is not a physical trajectory or complete observer frame/model replay.',
    'decision_confidence_percent': 95,
    'neurons': neurons, 'rows': rows,
    'all_nine_outputs_and_checksums_match_exactly': True,
    'measurements': {name: {'samples': samples, 'median_wall_s': statistics.median(s['wall_s'] for s in samples), 'median_producer_cpu_s': statistics.median(s['producer_cpu_s'] for s in samples)} for name, samples in records.items()},
    'elapsed_s': time.perf_counter() - started,
    'compiler': subprocess.check_output([compiler, '--version'], text=True),
    'flags': flags, 'compiler_stderr': compilation.stderr,
    'system_zlib_version': zlib.ZLIB_RUNTIME_VERSION,
    'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'cpp_sha256': hashlib.sha256((OUT / 'writer.cpp').read_bytes()).hexdigest(),
    'input_sha256': hashlib.sha256((OUT / 'input.bin').read_bytes()).hexdigest(),
    'reference_artifact_sha256': hashlib.sha256(endpoint.read_bytes()).hexdigest(),
    'brian_observer_source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
    'limits': 'The original obs_write and checksum setup are extracted unchanged from current source. Timings include a pipe consumer hashing and independently checking every byte; no full producer/consumer attribution. Both variants are standalone diagnostic probes, not production changes, complete frame-parser tests or new capture-mode qualification.',
    'application_changed': False, 'new_full_case_or_matrix_run': False, 'p9_resumed': False,
}
with (OUT / 'result.json').open('x') as stream:
    json.dump(record, stream, indent=2, allow_nan=False)
    stream.write('\n')
signal.alarm(0)
print(json.dumps({'completed': True, 'elapsed_s': record['elapsed_s'], 'result': str(OUT / 'result.json')}), flush=True)
