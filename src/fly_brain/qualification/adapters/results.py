import json

from fly_brain.qualification.models import QualificationRequest, QualificationResult


def write_result(request: QualificationRequest, result: QualificationResult) -> None:
    report: dict[str, object] = {
        'command': result.command,
        'exit_code': result.exit_code,
        'MLX_ENABLE_TF32': '0',
        'accepted': result.accepted,
    }
    if result.counts is not None:
        report.update(
            tests=result.counts.tests,
            failures=result.counts.failures,
            errors=result.counts.errors,
            skipped=result.counts.skipped,
        )
    with (request.output / 'result.json').open('x') as destination:
        json.dump(report, destination, indent=2)
        destination.write('\n')
