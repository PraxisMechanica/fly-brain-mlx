from fly_brain.qualification.models import (
    QualificationRequest,
    QualificationResult,
    ResultWriter,
    TestRunner,
)


def qualify(
    request: QualificationRequest, runner: TestRunner, writer: ResultWriter
) -> QualificationResult:
    result = runner(request)
    writer(request, result)
    return result
