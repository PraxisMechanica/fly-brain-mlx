import numpy as np
import pytest

from fly_brain.comparison.models import SpikeSteps
from fly_brain.qualification.matrix_diagnostics import CaseRasters, coverage, summarize
from fly_brain.qualification.models import ParityCase

pytestmark = pytest.mark.unit


def test_unobserved_matrix_retains_all_frozen_cases_without_claiming_silence() -> None:
    groups = coverage(())
    assert len(groups) == 12 and sum(len(group.expected) for group in groups) == 52
    assert all(
        group.missing == group.expected and not group.included for group in groups
    )


def test_failed_invalid_and_missing_cases_remain_separate_within_partial_group() -> (
    None
):
    cases = tuple(ParityCase('sugar', 1000, trial) for trial in range(3))
    group = coverage(cases[:2], cases[2:], (cases[1],))[0]
    assert (group.included, group.invalid, group.failed, group.missing) == (
        (0, 1),
        (2,),
        (1,),
        (3, 4),
    )


@pytest.mark.parametrize('invalid', [False, True])
def test_duplicate_case_identity_cannot_select_a_more_favorable_run(
    invalid: bool,
) -> None:
    case = ParityCase('sugar', 1000, 0)
    with pytest.raises(ValueError, match='Duplicate'):
        coverage((case,) if invalid else (case, case), (case,) if invalid else ())


def test_failed_case_requires_a_valid_included_raster() -> None:
    with pytest.raises(ValueError, match='included failures'):
        coverage((), failed=(ParityCase('sugar', 1000, 0),))


def test_unprescribed_case_cannot_expand_the_frozen_matrix() -> None:
    with pytest.raises(ValueError, match='prescribed cases'):
        coverage((ParityCase('silent', 1000, 1),))


def test_partial_group_reports_keep_failure_even_when_pooled_counts_cancel() -> None:
    empty = SpikeSteps(np.asarray([], dtype=np.int64), np.asarray([], dtype=np.int64))
    active = SpikeSteps(
        np.asarray([1], dtype=np.int64), np.asarray([99], dtype=np.int64)
    )
    cases = (
        CaseRasters(ParityCase('sugar', 1000, 1), empty, active, empty),
        CaseRasters(ParityCase('sugar', 1000, 0), active, empty, active),
    )
    group = summarize(cases, failed=tuple(row.case for row in cases))[0]
    assert group.coverage.failed == (0, 1) and group.coverage.missing == (2, 3, 4)
    assert (
        group.metrics is not None
        and group.metrics['mlx'].counts_equal
        and group.metrics['mlx'].timing_f1 == 0
    )
    assert group.pooled_bin_counts == {'brian': (1,), 'mlx': (1,), 'torch': (1,)}


def test_unobserved_groups_have_unavailable_metrics_and_counts() -> None:
    assert all(
        group.metrics is None and group.pooled_bin_counts is None
        for group in summarize(())
    )
