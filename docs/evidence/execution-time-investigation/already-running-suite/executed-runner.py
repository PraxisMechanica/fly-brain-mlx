import contextlib
import hashlib
import json
import os
import runpy
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import mlx.core as mx
import pytest

from fly_brain.simulation.backend import core

ROOT = Path('/Users/ocasta/Code/fly-brain')
PROTOTYPE = (
    ROOT
    / 'docs/evidence/milestone-4/timing-remediation/native-local/executed-prototype.py'
)


def main() -> None:
    assert __debug__ and os.environ['MLX_ENABLE_TF32'] == '0'
    assert mx.metal.is_available()
    mx.disable_compile()
    proof = json.loads(PROTOTYPE.with_name('verification.json').read_text())
    prototype_sha = hashlib.sha256(PROTOTYPE.read_bytes()).hexdigest()
    assert prototype_sha == proof['bound_artifact_sha256']['executed-prototype.py']
    assert proof['native_prototype_and_separate_fresh_process_repeat_passed'] is True
    candidate = runpy.run_path(str(PROTOTYPE))['integrate']
    original = core.integrate
    source_hashes = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((ROOT / 'src/fly_brain').rglob('*.py'))
    }
    output = Path(sys.argv[1]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    guarded_tests = []

    class Guard:
        def pytest_runtest_call(self, item):
            assert core.integrate is candidate
            guarded_tests.append(item.nodeid)

    arguments = [
        '-q',
        'tests/qualification',
        '--disable-warnings',
        '--artifact-output',
        str(output),
        f'--junitxml={output / "tests.xml"}',
    ]
    with (output / 'qualification.log').open('x') as log:
        with (
            contextlib.redirect_stdout(log),
            contextlib.redirect_stderr(log),
            patch.object(core, 'integrate', candidate),
        ):
            exit_code = pytest.main(arguments, plugins=[Guard()])
    assert core.integrate is original
    for name, digest in source_hashes.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    suites = tuple(ET.parse(output / 'tests.xml').getroot().iter('testsuite'))
    counts = {
        key: sum(int(suite.get(key, '0')) for suite in suites)
        for key in ('tests', 'failures', 'errors', 'skipped')
    }
    record = {
        'scope': 'Complete unchanged scientific suite using the exact prospectively reviewed candidate only in this process; production and live P9 sources remain unchanged.',
        'parent_checkpoint': subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], text=True
        ).strip(),
        'command': arguments,
        'exit_code': int(exit_code),
        'counts': counts,
        'prototype_sha256': prototype_sha,
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'source_sha256': source_hashes,
        'all_application_sources_preserved': True,
        'candidate_binding_test_nodes': guarded_tests,
        'production_changed': False,
        'full_case_accepted': False,
        'MLX_ENABLE_TF32': os.environ['MLX_ENABLE_TF32'],
        'compilation': 'disabled',
        'device': mx.device_info(),
    }
    with (output / 'result.json').open('x') as destination:
        destination.write(json.dumps(record, indent=2, allow_nan=False) + '\n')
    print(
        json.dumps(
            {
                key: record[key]
                for key in (
                    'exit_code',
                    'counts',
                    'prototype_sha256',
                    'all_application_sources_preserved',
                    'full_case_accepted',
                )
            },
            indent=2,
        ),
        flush=True,
    )
    assert exit_code == 0 and counts['tests'] == len(guarded_tests)
    assert counts['failures'] == counts['errors'] == counts['skipped'] == 0


if __name__ == '__main__':
    main()
