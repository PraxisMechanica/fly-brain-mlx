import os
import subprocess
import sys
import xml.etree.ElementTree as ET

from fly_brain.qualification.models import (
    QualificationRequest,
    QualificationResult,
    TestCounts,
)


def run_tests(request: QualificationRequest) -> QualificationResult:
    request.output.mkdir(parents=True, exist_ok=False)
    command = (
        sys.executable,
        '-m',
        'pytest',
        '-q',
        'tests/qualification',
        '--disable-warnings',
        '--artifact-output',
        str(request.output),
        f'--junitxml={request.output / "tests.xml"}',
    )
    environment = dict(os.environ, MLX_ENABLE_TF32='0')
    with (request.output / 'qualification.log').open('x') as log:
        process = subprocess.run(
            command,
            cwd=request.project,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    report = request.output / 'tests.xml'
    counts = None
    if report.exists():
        suites = tuple(ET.parse(report).getroot().iter('testsuite'))
        values = tuple(
            sum(int(suite.get(key, '0')) for suite in suites)
            for key in ('tests', 'failures', 'errors', 'skipped')
        )
        counts = TestCounts(*values)
    return QualificationResult(command, process.returncode, counts)
