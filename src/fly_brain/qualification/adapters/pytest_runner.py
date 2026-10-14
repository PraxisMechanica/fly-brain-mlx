import os
import subprocess
import sys
import xml.etree.ElementTree as ET

from fly_brain.infrastructure.seeded_random import uniforms
from fly_brain.qualification.models import (
    QualificationRequest,
    QualificationResult,
    TestCounts,
)
from fly_brain.simulation.experiments import EXPERIMENTS
from fly_brain.simulation.identifiers import TrialId
from fly_brain.simulation.input_service import load_pinned_inputs
from fly_brain.simulation.inputs import load_connectome
from fly_brain.simulation.stimulus_service import schedule
from fly_brain.simulation.storage import persist_stimulus


def run_tests(request: QualificationRequest) -> QualificationResult:
    request.output.mkdir(parents=True, exist_ok=False)
    connectome, pin = load_pinned_inputs(request.project, lambda: load_connectome)
    experiment = EXPERIMENTS['sugar']
    stimulus = schedule(
        connectome,
        experiment,
        1000,
        tuple(map(TrialId, range(4))),
        20261004,
        draw_uniforms=uniforms,
    )
    persist_stimulus(request.output / 'frozen-stimulus', experiment, pin, stimulus)
    command = (
        sys.executable,
        '-m',
        'pytest',
        '-q',
        'tests/qualification',
        'tests/integration/test_session_proof_artifacts.py',
        '--disable-warnings',
        '--artifact-output',
        str(request.output),
        f'--junitxml={request.output / "tests.xml"}',
        f'--basetemp={request.output / "temporary"}',
    )
    environment = dict(
        os.environ,
        MLX_ENABLE_TF32='0',
        FLY_BRAIN_PINNED_PROJECT=str(request.project),
    )
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
