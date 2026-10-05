from dataclasses import dataclass

from fly_brain.simulation.models import ExperimentName

from .matrix import required_cases
from .models import ParityCase


@dataclass(frozen=True)
class GroupCoverage:
    experiment: ExperimentName
    steps: int
    expected: tuple[int, ...]
    included: tuple[int, ...]
    missing: tuple[int, ...]
    invalid: tuple[int, ...]
    failed: tuple[int, ...]


def coverage(
    included: tuple[ParityCase, ...],
    invalid: tuple[ParityCase, ...] = (),
    failed: tuple[ParityCase, ...] = (),
) -> tuple[GroupCoverage, ...]:
    required = required_cases()
    available = (*included, *invalid)
    if len(set(available)) != len(available) or len(set(failed)) != len(failed):
        raise ValueError('Duplicate case identities cannot enter matrix summaries')
    if set(available) - set(required) or set(failed) - set(included):
        raise ValueError('Coverage requires prescribed cases and included failures')
    groups: dict[tuple[ExperimentName, int], list[ParityCase]] = {}
    for case in required:
        groups.setdefault((case.experiment, case.steps), []).append(case)
    return tuple(
        GroupCoverage(
            experiment,
            steps,
            tuple(case.trial for case in expected),
            tuple(case.trial for case in expected if case in included),
            tuple(case.trial for case in expected if case not in available),
            tuple(case.trial for case in expected if case in invalid),
            tuple(case.trial for case in expected if case in failed),
        )
        for (experiment, steps), expected in groups.items()
    )
