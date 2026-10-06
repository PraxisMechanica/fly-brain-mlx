from .metrics import compare_metrics, prepare_metrics
from .models import ComparisonRequest, ComparisonResult, SpikeReader


def compare(request: ComparisonRequest, reader: SpikeReader) -> ComparisonResult:
    first = prepare_metrics(
        reader(request.first, request.duration_s), request.duration_s, request.trials
    )
    second = prepare_metrics(
        reader(request.second, request.duration_s), request.duration_s, request.trials
    )
    return compare_metrics(request, first, second)
