import pytest

from tools.code_quality.gate import references

pytestmark = pytest.mark.unit


def test_local_check_uses_the_current_branch() -> None:
    assert references({}) is None


def test_push_checks_all_submitted_commits() -> None:
    assert references({'PRE_COMMIT_FROM_REF': 'base', 'PRE_COMMIT_TO_REF': 'head'}) == (
        'base',
        'head',
    )


def test_ci_range_has_explicit_precedence() -> None:
    assert references(
        {
            'QUALITY_BASE': 'review-base',
            'QUALITY_HEAD': 'review-head',
            'PRE_COMMIT_FROM_REF': 'other-base',
            'PRE_COMMIT_TO_REF': 'other-head',
        }
    ) == ('review-base', 'review-head')


@pytest.mark.parametrize(
    'environment',
    [
        {'QUALITY_BASE': 'base'},
        {'QUALITY_HEAD': 'head'},
        {'PRE_COMMIT_FROM_REF': 'base'},
        {'PRE_COMMIT_TO_REF': 'head'},
        {'QUALITY_BASE': '0' * 40, 'QUALITY_HEAD': 'head'},
        {'QUALITY_BASE': 'base', 'QUALITY_HEAD': '0' * 40},
    ],
)
def test_incomplete_evidence_cannot_pass(environment: dict[str, str]) -> None:
    with pytest.raises(ValueError, match='Incomplete commit range'):
        references(environment)
