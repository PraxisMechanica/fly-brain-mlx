import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PhaseDigest:
    begin: int
    rows: int
    native: tuple[str, ...]
    queues: tuple[str, ...]
    due: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class PhaseDifference:
    trial: int
    begin: int
    rows: int
    field: Literal['native', 'queues', 'due']


def require_phase_coverage(
    blocks: Sequence[PhaseDigest], steps: int, trials: int
) -> None:
    if steps < 1 or trials not in (1, 4):
        raise ValueError(
            'Phase coverage requires a positive horizon and one/four trials'
        )
    expected = [(begin, min(32, steps - begin)) for begin in range(0, steps, 32)]
    if [(block.begin, block.rows) for block in blocks] != expected:
        raise ValueError('Phase evidence must cover every prescribed block exactly')
    for block in blocks:
        if (
            len(block.native) != trials
            or len(block.queues) != trials
            or len(block.due) != block.rows
            or any(len(row) != trials for row in block.due)
            or any(
                re.fullmatch('[0-9a-f]{64}', digest) is None
                for digest in (
                    *block.native,
                    *block.queues,
                    *(digest for row in block.due for digest in row),
                )
            )
        ):
            raise ValueError('Phase evidence requires every native/queue/due digest')


def phase_difference(
    batch: Sequence[PhaseDigest],
    singletons: Mapping[int, Sequence[PhaseDigest]],
    steps: int,
) -> PhaseDifference | None:
    if set(singletons) != {0, 1, 2, 3}:
        raise ValueError(
            'Batch comparison requires independent trials zero through three'
        )
    require_phase_coverage(batch, steps, 4)
    for single in singletons.values():
        require_phase_coverage(single, steps, 1)
    for position, many in enumerate(batch):
        for trial in range(4):
            one = singletons[trial][position]
            if many.native[trial] != one.native[0]:
                return PhaseDifference(trial, many.begin, many.rows, 'native')
            if many.queues[trial] != one.queues[0]:
                return PhaseDifference(trial, many.begin, many.rows, 'queues')
            if tuple(row[trial] for row in many.due) != tuple(
                row[0] for row in one.due
            ):
                return PhaseDifference(trial, many.begin, many.rows, 'due')
    return None
