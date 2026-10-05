from contextlib import closing
from dataclasses import replace

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import build, run
from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import observe
from fly_brain.qualification.adapters.observer_stream import (
    FinalSnapshot,
    PhaseBlock,
    StepSnapshot,
)
from fly_brain.qualification.adapters.paired_observer import (
    PairedBlock,
    audit_block,
    pair_blocks,
)
from fly_brain.qualification.adapters.reference_queues import ReferenceQueues
from fly_brain.qualification.causality import CausalAudit
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.bucketed import prepare
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


@pytest.fixture(scope='module')
def paired(
    precision: str, tmp_path_factory: pytest.TempPathFactory
) -> tuple[PairedBlock | FinalSnapshot, ...]:
    tmp_path = tmp_path_factory.mktemp('paired-observer')
    case = fixture()
    events = case.events[:1]
    job = build(case.connectome, case.targets, (3,), events[0], tmp_path / 'build')
    execution = prepare(case.connectome, case.targets, (3,), precision)
    mlx = observe(
        execution,
        core.initial_state(execution.network),
        events,
        EventLedger(case.connectome, case.targets, 1),
    )
    ledger = ReferenceQueues(case.connectome.sources, 6, events[0])
    with closing(run(job, tmp_path / 'results')) as reference:
        return tuple(pair_blocks(reference, mlx, ledger))


def test_live_engines_pair_every_phase_and_final_partial_block(
    paired: tuple[PairedBlock | FinalSnapshot, ...],
) -> None:
    frames = paired
    blocks = [frame for frame in frames if isinstance(frame, PairedBlock)]
    assert [(block.reference.begin, block.reference.rows) for block in blocks] == [
        (0, 32),
        (32, 32),
        (64, 32),
        (96, 5),
    ]
    assert isinstance(frames[-1], FinalSnapshot) and frames[-1].step.step == 101
    audit = CausalAudit()
    for block in blocks:
        assert len(block.snapshots) == block.reference.rows
        assert block.reference.fields['pre_v'].dtype == np.float64
        assert block.mlx.fields['pre_v'].dtype == np.float32
        assert all(len(digest) == 64 for digest in block.native_sha256)
        audit_block(block, audit)
    assert audit.step == 101
    assert audit.first_spike_step is None and audit.first_budget_violation is None


@pytest.mark.parametrize(
    'fault', ('missing', 'begin', 'rows', 'queue', 'final', 'extra')
)
def test_incomplete_or_invalid_paired_evidence_cannot_pass(
    paired: tuple[PairedBlock | FinalSnapshot, ...], fault: str
) -> None:
    reference: list[StepSnapshot | PhaseBlock | FinalSnapshot] = []
    blocks = [frame.mlx for frame in paired if isinstance(frame, PairedBlock)]
    for frame in paired:
        if isinstance(frame, PairedBlock):
            reference.extend(frame.snapshots)
            reference.append(frame.reference)
        else:
            reference.append(frame)
    if fault == 'missing':
        blocks.pop()
    if fault == 'begin':
        blocks[0] = replace(blocks[0], begin=1)
    if fault == 'rows':
        blocks[0] = replace(blocks[0], rows=31)
    if fault == 'queue':
        flags = blocks[0].checks.copy()
        flags[0, 0, 29] = False
        blocks[0] = replace(blocks[0], checks=flags)
    if fault == 'final':
        reference.pop()
    if fault == 'extra':
        reference.append(reference[-1])
    case = fixture()
    ledger = ReferenceQueues(case.connectome.sources, 6, case.events[0])
    with pytest.raises(ValueError, match='coverage|ledger|final|extra'):
        tuple(pair_blocks(iter(reference), iter(blocks), ledger))
