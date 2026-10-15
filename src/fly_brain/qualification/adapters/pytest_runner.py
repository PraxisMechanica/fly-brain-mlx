import os
import signal
import subprocess
import sys
import xml.etree.ElementTree as ET
from time import monotonic

from fly_brain.qualification.models import (
    QualificationRequest,
    QualificationResult,
    TestCounts,
)


def run_tests(request: QualificationRequest) -> QualificationResult:
    started = monotonic()
    request.output.mkdir(parents=True, exist_ok=False)
    command = (
        sys.executable,
        '-m',
        'pytest',
        '-q',
        'tests/qualification',
        '--disable-warnings',
        '--maxfail=1',
        '--artifact-output',
        str(request.output),
        f'--junitxml={request.output / "tests.xml"}',
        f'--basetemp={request.output / "temporary"}',
    )
    environment = dict(os.environ, MLX_ENABLE_TF32='0')
    with (request.output / 'qualification.log').open('x') as log:
        process = subprocess.Popen(
            command,
            cwd=request.project,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            exit_code = process.wait(timeout=max(0, 300 - (monotonic() - started)))
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            log.write(
                'Qualification exceeded the five-minute limit; stopped for diagnosis.\n'
            )
            return QualificationResult(command, 124, None)
    report = request.output / 'tests.xml'
    counts = None
    if report.exists():
        suites = tuple(ET.parse(report).getroot().iter('testsuite'))
        values = tuple(
            sum(int(suite.get(key, '0')) for suite in suites)
            for key in ('tests', 'failures', 'errors', 'skipped')
        )
        counts = TestCounts(*values)
    return QualificationResult(command, exit_code, counts)
