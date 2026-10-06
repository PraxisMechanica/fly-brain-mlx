from pathlib import Path

from fly_brain.qualification.models import (
    ParityCase,
    QualificationRequest,
    QualificationResult,
    ResultWriter,
    TestRunner,
)
from fly_brain.qualification.ports import (
    InputProbe,
    OutputProbe,
    ParityProbe,
    PinnedInputs,
    ProjectProbe,
)


def qualify(
    request: QualificationRequest, runner: TestRunner, writer: ResultWriter
) -> QualificationResult:
    result = runner(request)
    writer(request, result)
    return result


def probe_project(
    request: QualificationRequest, execute: ProjectProbe
) -> dict[str, object]:
    return execute(request.project, request.output)


def probe_output(
    request: QualificationRequest, execute: OutputProbe
) -> dict[str, object]:
    return execute(request.output)


def audit_inputs(
    request: QualificationRequest, load: PinnedInputs, execute: InputProbe
) -> dict[str, object]:
    connectome, pin = load(request.project)
    return execute(connectome, pin, request.output)


def parity_case(
    project: Path,
    output: Path,
    case: ParityCase,
    load: PinnedInputs,
    execute: ParityProbe,
) -> dict[str, object]:
    connectome, pin = load(project)
    return execute(connectome, pin, case, output)
