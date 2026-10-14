import json
from copy import deepcopy

import pytest

from tools.code_quality.diagnostics import project_metric_exit


@pytest.mark.parametrize(
    'rule,metric,before,after',
    (
        ('CQ001', 'code_health', 40.0, 39.99),
        ('CQ002', 'cyclomatic_complexity', 20, 21),
        ('CQ003', 'maintainability_index', 40.0, 39.99),
    ),
)
def test_known_numerical_regressions_are_advisory_without_changing_native_facts(
    rule: str, metric: str, before: float, after: float
) -> None:
    payload: dict[str, object] = {
        'status': 'regression',
        'passed': False,
        'before': {'measured': before},
        'after': {'measured': after},
        'findings': {
            'total': 1,
            'by_rule': {rule: 1},
            'examples': [
                {
                    'rule': rule,
                    'path': 'calculation.py',
                    'metric': metric,
                    'before': before,
                    'after': after,
                }
            ],
            'omitted': 0,
        },
    }
    original = deepcopy(payload)
    assert project_metric_exit(payload, 1) == 0
    assert payload == original


@pytest.mark.parametrize(
    'findings',
    (
        '{}',
        '{"total":0,"by_rule":{},"examples":[],"omitted":0}',
        '{"total":1,"by_rule":{"CQ999":1},"examples":[],"omitted":1}',
        '{"total":true,"by_rule":{"CQ001":1},"examples":[],"omitted":1}',
        '{"total":1,"by_rule":{"CQ001":1},"examples":"invalid","omitted":0}',
    ),
)
def test_unexplained_unknown_or_malformed_regressions_remain_blocking(
    findings: str,
) -> None:
    payload: dict[str, object] = {
        'status': 'regression',
        'passed': False,
        'findings': json.loads(findings),
    }
    with pytest.raises(ValueError, match='Metric regression'):
        project_metric_exit(payload, 1)


def test_native_analysis_errors_remain_blocking_without_changing_the_reason() -> None:
    payload: dict[str, object] = {
        'status': 'analysis_error',
        'passed': False,
        'error': {'message': 'Required source could not be parsed'},
    }
    original = deepcopy(payload)
    assert project_metric_exit(payload, 2) == 2
    assert payload == original
