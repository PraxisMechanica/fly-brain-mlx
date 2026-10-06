import json
from pathlib import Path

from .models import ComparisonRequest
from .ports import ComparisonReport


def comparison(
    request: ComparisonRequest, output: Path, use_case: ComparisonReport
) -> int:
    result = use_case(request, output)
    print(json.dumps(result.summary, indent=2))
    return 0
