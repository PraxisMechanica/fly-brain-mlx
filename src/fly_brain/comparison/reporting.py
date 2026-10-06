from pathlib import Path

from .models import ComparisonRequest, ComparisonResult
from .ports import ComparisonUseCase, ComparisonWriter


def compare_to_output(
    request: ComparisonRequest,
    output: Path,
    compare: ComparisonUseCase,
    write: ComparisonWriter,
) -> ComparisonResult:
    result = compare(request)
    write(output, result)
    return result
