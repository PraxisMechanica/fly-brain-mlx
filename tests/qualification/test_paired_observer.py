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
    phase_hash,
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
    'fault', ('missing', 'begin', 'rows', 'queue', 'checks', 'final', 'extra')
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
    if fault == 'checks':
        blocks[0] = replace(blocks[0], checks=np.empty((32, 1, 0), dtype=np.bool_))
    if fault == 'final':
        reference.pop()
    if fault == 'extra':
        reference.append(reference[-1])
    case = fixture()
    ledger = ReferenceQueues(case.connectome.sources, 6, case.events[0])
    with pytest.raises(ValueError, match='coverage|ledger|final|extra'):
        tuple(pair_blocks(iter(reference), iter(blocks), ledger))


@pytest.mark.parametrize(
    ('engine', 'field', 'value', 'reason'),
    (
        ('reference', 'pre_t', 0.0001, 'phase clocks'),
        ('reference', 'end_lastspike', np.nan, 'remain finite'),
        ('mlx', 'pre_not_refractory', False, 'refractory'),
        ('mlx', 'end_not_refractory', False, 'refractory'),
        ('mlx', 'end_last_spike_step', 9, 'last-spike clocks'),
        ('mlx', 'pre_v', np.nan, 'must be finite'),
    ),
)
def test_changed_actual_causal_fields_fail_without_a_parity_score(
    paired: tuple[PairedBlock | FinalSnapshot, ...],
    engine: str,
    field: str,
    value: float | bool,
    reason: str,
) -> None:
    block = paired[0]
    assert isinstance(block, PairedBlock)
    if engine == 'reference':
        fields = dict(block.reference.fields)
        fields[field] = fields[field].copy()
        fields[field][0] = value
        block = replace(block, reference=replace(block.reference, fields=fields))
    else:
        fields_mlx = dict(block.mlx.fields)
        fields_mlx[field] = fields_mlx[field].copy()
        fields_mlx[field][0, 0, 0] = value
        block = replace(block, mlx=replace(block.mlx, fields=fields_mlx))
    with pytest.raises(ValueError, match=reason):
        audit_block(block, CausalAudit())


@pytest.mark.parametrize('change', ('dtype', 'shape', 'units'))
def test_native_hash_identifies_precision_shape_and_unconverted_units(
    change: str,
) -> None:
    raw = np.array([-0.052, -0.045], dtype=np.float64)
    changed = (
        raw.astype(np.float32)
        if change == 'dtype'
        else raw.reshape(1, 2)
        if change == 'shape'
        else raw * 1000
    )
    assert phase_hash({'v': raw}) != phase_hash({'v': changed})
