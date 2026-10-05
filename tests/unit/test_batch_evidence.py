from dataclasses import replace
from typing import Literal

import pytest

from fly_brain.qualification.batch_evidence import (
    PhaseDifference,
    PhaseDigest,
    phase_difference,
    require_phase_coverage,
)

pytestmark = pytest.mark.unit


def batch(steps: int = 35) -> tuple[PhaseDigest, ...]:
    hashes = tuple(str(trial + 1) * 64 for trial in range(4))
    return tuple(
        PhaseDigest(
            begin,
            min(32, steps - begin),
            hashes,
            hashes,
            (hashes,) * min(32, steps - begin),
        )
        for begin in range(0, steps, 32)
    )


def singles(blocks: tuple[PhaseDigest, ...]) -> dict[int, tuple[PhaseDigest, ...]]:
    return {
        trial: tuple(
            PhaseDigest(
                b.begin,
                b.rows,
                (b.native[trial],),
                (b.queues[trial],),
                tuple((row[trial],) for row in b.due),
            )
            for b in blocks
        )
        for trial in range(4)
    }


@pytest.mark.parametrize('steps', (35, 1000, 10000, 100000))
def test_exact_digest_comparison_requires_the_complete_actual_horizon(
    steps: int,
) -> None:
    blocks = batch(steps)
    assert phase_difference(blocks, singles(blocks), steps) is None
    with pytest.raises(ValueError, match='every prescribed block'):
        phase_difference(blocks[:-1], singles(blocks[:-1]), steps)


@pytest.mark.parametrize('field', ('native', 'queues', 'due'))
def test_a_changed_digest_returns_an_unresolved_block_not_a_tolerance_pass(
    field: Literal['native', 'queues', 'due'],
) -> None:
    blocks = batch()
    one = singles(blocks)
    changed = list(blocks)
    values = list(getattr(changed[-1], field))
    if field == 'due':
        values[1] = (*values[1][:3], 'f' * 64)
    else:
        values[3] = 'f' * 64
    changed[-1] = replace(changed[-1], **{field: tuple(values)})
    assert phase_difference(changed, one, 35) == PhaseDifference(3, 32, 3, field)


@pytest.mark.parametrize(
    'fault', ('native', 'queues', 'due', 'due_trial', 'hash', 'duplicate', 'rows')
)
def test_incomplete_or_malformed_phase_evidence_cannot_pass(fault: str) -> None:
    blocks = list(batch())
    if fault in ('native', 'queues', 'due'):
        blocks[-1] = replace(blocks[-1], **{fault: ()})
    elif fault == 'due_trial':
        blocks[-1] = replace(blocks[-1], due=((),) * 3)
    elif fault == 'hash':
        blocks[-1] = replace(blocks[-1], native=('invalid',) * 4)
    elif fault == 'duplicate':
        blocks[-1] = blocks[0]
    else:
        blocks[-1] = replace(blocks[-1], rows=2)
    with pytest.raises(
        ValueError, match='every prescribed block|every native/queue/due'
    ):
        require_phase_coverage(blocks, 35, 4)


@pytest.mark.parametrize('missing', range(4))
def test_all_four_independent_trial_identities_are_required(missing: int) -> None:
    blocks = batch()
    one = singles(blocks)
    del one[missing]
    with pytest.raises(ValueError, match='zero through three'):
        phase_difference(blocks, one, 35)
