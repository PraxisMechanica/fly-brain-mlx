import json
from pathlib import Path

from .models import ParityCase, QualificationRequest
from .ports import DiagnosticUseCase, ParityUseCase, QualificationUseCase


def qualification(request: QualificationRequest, use_case: QualificationUseCase) -> int:
    result = use_case(request)
    print(
        json.dumps(
            {'accepted': result.accepted, 'exit_code': result.exit_code}, indent=2
        )
    )
    return 0 if result.accepted else 1


def diagnostic(request: QualificationRequest, use_case: DiagnosticUseCase) -> int:
    report = use_case(request)
    print(json.dumps(report, indent=2))
    return 0 if report.get('accepted', True) else 1


def parity_case(
    project: Path, output: Path, case: ParityCase, use_case: ParityUseCase
) -> int:
    report = use_case(project, output, case)
    print(
        json.dumps(
            {
                'case': report['case'],
                'case_accepted': report['case_accepted'],
                'scientific_review_required': report['scientific_review_required'],
                'report': str(output / 'case.json'),
            },
            indent=2,
        )
    )
    return 0 if report['case_accepted'] else 1
