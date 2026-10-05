from collections import Counter

import pytest

from fly_brain.qualification.matrix import required_cases

pytestmark = pytest.mark.unit


def test_frozen_matrix_preserves_every_required_trial_and_horizon() -> None:
    cases = required_cases()
    actual = {(case.experiment, case.steps, case.trial) for case in cases}
    expected = {
        (experiment, steps, trial)
        for experiment in ('sugar', 'p9', 'sugar-silenced', 'two-class', 'silent')
        for steps in (1000, 10000, 100000)
        for trial in range(5)
        if (steps != 100000 or experiment in ('sugar', 'p9'))
        and (trial == 0 or experiment != 'silent')
    }
    assert actual == expected and len(cases) == len(actual) == 52


def test_matrix_workload_counts_each_trial_before_repeats_and_batch_gates() -> None:
    cases = required_cases()
    assert Counter(case.experiment for case in cases) == {
        'sugar': 15,
        'p9': 15,
        'sugar-silenced': 10,
        'two-class': 10,
        'silent': 2,
    }
    assert sum(case.steps for case in cases) == 1231000
