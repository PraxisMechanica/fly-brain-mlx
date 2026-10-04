from pathlib import Path

import pytest
from pydantic import ValidationError

from fly_brain.qualification.models import (
    QualificationRequest,
    QualificationResult,
)
from fly_brain.qualification.models import (
    TestCounts as Counts,
)
from fly_brain.qualification.schemas import QualificationOptions
from fly_brain.qualification.service import qualify

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    'exit_code,counts,accepted',
    [
        (0, Counts(61, 0, 0, 0), True),
        (1, Counts(61, 0, 0, 0), False),
        (0, Counts(61, 1, 0, 0), False),
        (0, Counts(61, 0, 1, 0), False),
        (0, Counts(61, 0, 0, 1), False),
        (0, Counts(0, 0, 0, 0), False),
        (0, None, False),
    ],
)
def test_qualification_requires_tests_and_no_skips_or_failures(
    exit_code: int, counts: Counts | None, accepted: bool
) -> None:
    result = QualificationResult(('pytest',), exit_code, counts)
    assert result.accepted is accepted


def test_service_passes_the_same_request_and_result_to_its_collaborators() -> None:
    request = QualificationRequest(Path('/project'), Path('/evidence'))
    result = QualificationResult(('pytest',), 0, Counts(61, 0, 0, 0))
    calls: list[object] = []

    def runner(value: QualificationRequest) -> QualificationResult:
        calls.append(value)
        return result

    def writer(value: QualificationRequest, observed: QualificationResult) -> None:
        calls.append((value, observed))

    assert qualify(request, runner, writer) is result
    assert calls == [request, (request, result)]


def test_independent_options_do_not_share_output_configuration(tmp_path: Path) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    first = QualificationOptions(project=tmp_path, output=tmp_path / 'first')
    second = QualificationOptions(project=tmp_path, output=tmp_path / 'second')
    assert first.to_request().output != second.to_request().output
    assert not first.output.exists() and not second.output.exists()


def test_existing_evidence_is_preserved_when_output_is_rejected(tmp_path: Path) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    evidence = tmp_path / 'existing'
    evidence.mkdir()
    marker = evidence / 'retained.txt'
    marker.write_text('preserve')
    with pytest.raises(ValidationError, match='new directory'):
        QualificationOptions(project=tmp_path, output=evidence)
    assert marker.read_text() == 'preserve'
