from pathlib import Path

import numpy as np
import pytest

from tools.score_tiered_campaign import compare, eon_metrics, ratio_interval, welch


def test_welch_uses_sample_variance_and_explicit_constant_discrepancies() -> None:
    a = np.array([[0, 1, 0], [2, 1, 0], [4, 1, 0]], dtype=np.float64)
    b = np.array([[1, 2, 0]] * 3, dtype=np.float64)
    result = welch(a, b)
    np.testing.assert_array_equal(result.variance_a, [4, 0, 0])
    assert result.z[0] == pytest.approx(np.sqrt(3) / 2)
    assert result.degrees_freedom[0] == pytest.approx(2)
    assert result.z[1] == -np.inf and result.constant_discrepancy[1]
    assert result.z[2] == 0 and not result.constant_discrepancy[2]


def test_eon_rounding_and_empty_undefined_conventions() -> None:
    a = np.array([[1, 2, 0]], dtype=np.float64)
    b = np.array([[0, 4, 6]], dtype=np.float64)
    result = eon_metrics(a, b)
    assert result['jaccard_raw'] == pytest.approx(1 / 3)
    assert result['jaccard_eon_rounded'] == 0.3333
    assert result['spike_count_ratio_eon_rounded'] == 3.3333
    assert result['shared_active_pearson_raw'] is None
    empty = eon_metrics(np.zeros((1, 3)), np.zeros((1, 3)))
    assert empty['jaccard_raw'] == 0
    assert empty['both_silent_exact_agreement'] is True
    assert empty['spike_count_ratio_raw'] is None


def test_fieller_interval_retains_exact_constant_ratio_and_unbounded_case() -> None:
    assert ratio_interval(np.ones(30), np.full(30, 2.0)) == (2.0, 2.0)
    assert ratio_interval(np.zeros(30), np.ones(30)) is None
    with pytest.raises(ValueError, match='30 samples'):
        ratio_interval(np.ones(10), np.ones(10))


def test_complete_low_rate_support_and_integer_ids_are_preserved(
    tmp_path: Path,
) -> None:
    ids = np.array(
        [720575940624963786, 720575940630233916, 720575940637568838], dtype=np.int64
    )
    a = np.zeros((30, 3))
    b = np.zeros((30, 3))
    a[:, 0] = 1
    b[:, 0] = 2
    result = compare(a, b, ids, tmp_path / 'pair')
    assert result['gross_error_alarm'] is True
    assert result['constant_discrepancies'] == 1
    assert result['per_neuron_support'] == 3
    with np.load(tmp_path / 'pair.npz') as saved:
        np.testing.assert_array_equal(saved['neuron_ids'], ids)
        assert saved['neuron_ids'].dtype == np.int64
        assert saved['z'][1] == 0
    assert str(ids[0]) in (tmp_path / 'pair.csv').read_text()
