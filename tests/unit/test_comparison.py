from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from fly_brain.comparison.metrics import count_timing_matches, pearson_or_none
from fly_brain.comparison.models import ComparisonRequest, Spikes
from fly_brain.comparison.schemas import ComparisonOptions
from fly_brain.comparison.service import compare

pytestmark = pytest.mark.unit


def test_timing_matches_never_reuse_an_event() -> None:
    matches, differences = count_timing_matches(
        np.array([0.0, 0.001]), np.array([0.0005]), 0.001
    )
    assert (matches, differences) == (1, [0.0005])


def test_timing_matches_include_the_exact_tolerance_boundary() -> None:
    assert count_timing_matches(np.array([0.0]), np.array([0.001]), 0.001)[0] == 1


def test_timing_matches_do_not_cross_trials() -> None:
    first = Spikes(np.array([0], dtype=np.int16), np.array([10]), np.array([0.0]))
    second = Spikes(np.array([1], dtype=np.int16), np.array([10]), np.array([0.0]))
    request = ComparisonRequest(Path('a'), Path('b'), 1.0, 2, 1.0, 'a', 'b')
    inputs = {request.first: first, request.second: second}
    result = compare(request, lambda path, duration: inputs[path])
    assert result.summary['timing_matches'] == 0
    assert result.rates[0]['rate_a_hz'] == 0.5


def test_rate_correlation_reports_an_undefined_constant_vector() -> None:
    assert pearson_or_none(np.array([1.0, 1.0]), np.array([1.0, 2.0])) is None


@pytest.mark.parametrize('duration', [0.0, -1.0, np.inf, np.nan])
def test_boundary_rejects_an_invalid_duration(tmp_path: Path, duration: float) -> None:
    spikes = tmp_path / 'spikes.parquet'
    spikes.touch()
    with pytest.raises(ValidationError):
        ComparisonOptions(
            first=spikes,
            second=spikes,
            duration_s=duration,
            trials=1,
            tolerance_ms=0.1,
            first_label='a',
            second_label='b',
        )


def test_comparison_prepares_first_spikes_before_reader_reuses_its_buffer() -> None:
    ids = np.array([10], dtype=np.int64)
    times = np.array([0.01], dtype=np.float64)
    shared = Spikes(np.array([0], dtype=np.int16), ids, times)
    first, second = Path('first'), Path('second')
    request = ComparisonRequest(first, second, 1.0, 1, 1.0, 'first', 'second')

    def reader(path: Path, duration_s: float) -> Spikes:
        assert duration_s == request.duration_s
        if path == second:
            ids[0] = 20
            times[0] = 0.02
        return shared

    result = compare(request, reader)
    assert result.summary['active_shared'] == 0
    assert [
        (row['flywire_id'], row['rate_a_hz'], row['rate_b_hz']) for row in result.rates
    ] == [(10, 1.0, 0.0), (20, 0.0, 1.0)]
