import pytest
from pydantic import ValidationError

from tools.code_quality.ci_refs import Commit, Event, PullRequest, select

pytestmark = pytest.mark.unit
HEAD, BASE, PARENT = 'a' * 40, 'b' * 40, 'c' * 40


def test_normal_push_measures_every_submitted_commit() -> None:
    def unexpected(*arguments: str) -> str:
        raise AssertionError(arguments)

    assert select(Event(before=BASE), HEAD, unexpected) == (BASE, HEAD)


def test_pull_request_uses_its_head_and_merge_base() -> None:
    calls: list[tuple[str, ...]] = []

    def execute(*arguments: str) -> str:
        calls.append(arguments)
        return PARENT

    event = Event(
        pull_request=PullRequest(base=Commit(sha=BASE), head=Commit(sha=HEAD))
    )
    assert select(event, BASE, execute) == (PARENT, HEAD)
    assert calls == [('merge-base', BASE, HEAD)]


@pytest.mark.parametrize(
    'event', [Event(), Event(before='0' * 40), Event(before=BASE, forced=True)]
)
def test_new_forced_and_manual_runs_use_main_ancestry(event: Event) -> None:
    calls: list[tuple[str, ...]] = []

    def execute(*arguments: str) -> str:
        calls.append(arguments)
        return BASE

    assert select(event, HEAD, execute) == (BASE, HEAD)
    assert calls == [('merge-base', 'origin/main', HEAD)]


def test_equal_boundary_still_measures_one_actual_commit() -> None:
    def execute(operation: str, option: str, reference: str) -> str:
        assert (operation, option, reference) == ('rev-parse', '--verify', HEAD + '^')
        return PARENT

    assert select(Event(before=HEAD), HEAD, execute) == (PARENT, HEAD)


def test_invalid_event_cannot_become_a_git_option() -> None:
    with pytest.raises(ValidationError):
        Event(before='--untrusted-option')
