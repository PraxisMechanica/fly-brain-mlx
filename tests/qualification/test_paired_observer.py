from contextlib import closing
from dataclasses import replace

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import build, run
from fly_brain.qualification.adapters.causal_capture import CausalCapture
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
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.observation_module import build_observation_sessions
from tests.qualification.test_mlx_observer import fixture
from tests.support.session_block_values import replace_block

pytestmark = [pytest.mark.integration, pytest.mark.reference, pytest.mark.metal]


@pytest.fixture(scope='module')
def paired(
    precision: str, tmp_path_factory: pytest.TempPathFactory
) -> tuple[PairedBlock | FinalSnapshot, ...]:
    tmp_path = tmp_path_factory.mktemp('paired-observer')
    case = fixture()
    events = case.events[:1]
    job = build(case.connectome, case.targets, (3,), events[0], tmp_path / 'build')
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (3,), precision
    )
    mlx = observe_session(
        factory,
        case.connectome,
        case.targets,
        (0,),
        events,
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
        audit = audit_block(block, audit)
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
        blocks[0] = replace_block(blocks[0], begin=1)
    if fault == 'rows':
        blocks[0] = replace_block(blocks[0], rows=31)
    if fault == 'queue':
        flags = blocks[0].checks.copy()
        flags[0, 0, 29] = False
        blocks[0] = replace_block(blocks[0], checks=flags)
    if fault == 'checks':
        blocks[0] = replace_block(
            blocks[0], checks=np.empty((32, 1, 0), dtype=np.bool_)
        )
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
        block = replace(block, mlx=replace_block(block.mlx, fields=fields_mlx))
    with pytest.raises(ValueError, match=reason):
        audit_block(block, CausalAudit())


def test_first_difference_keeps_the_actual_preceding_step_across_blocks(
    paired: tuple[PairedBlock | FinalSnapshot, ...],
) -> None:
    first, second = paired[:2]
    assert isinstance(first, PairedBlock) and isinstance(second, PairedBlock)
    capture = CausalCapture()
    capture.check(first)
    fields = dict(second.mlx.fields)
    fields['spikes'] = fields['spikes'].copy()
    fields['spikes'][0, 0, 2] = True
    capture.check(replace(second, mlx=replace_block(second.mlx, fields=fields)))
    context = capture.spike
    assert context is not None and context.neurons == (2,)
    assert context.current.snapshot.step == 32
    assert context.previous is not None and context.previous.snapshot.step == 31
    assert context.current.reference['pre_v'].dtype == np.float64
    assert context.current.mlx['pre_v'].dtype == np.float32
    assert all(value.base is None for value in context.current.reference.values())
    assert context.current.reference['pre_t'].shape == ()
    assert (
        context.previous.mlx_due_edges.tobytes() == first.mlx.due_edges[-1][0].tobytes()
    )


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


def test_earliest_state_error_keeps_its_raw_context_on_later_blocks(
    paired: tuple[PairedBlock | FinalSnapshot, ...],
) -> None:
    first, second = paired[:2]
    assert isinstance(first, PairedBlock) and isinstance(second, PairedBlock)
    fields = dict(first.mlx.fields)
    fields['pre_v'] = fields['pre_v'].copy()
    fields['pre_v'][7, 0, 2] += 0.02
    fields['pre_v'][9, 0, 3] += 0.03
    capture = CausalCapture()
    capture.check(replace(first, mlx=replace_block(first.mlx, fields=fields)))
    context = capture.budget
    assert context is not None and context.neurons == (2,)
    assert context.current.snapshot.step == 7
    assert context.previous is not None and context.previous.snapshot.step == 6
    assert context.current.mlx['pre_v'].tobytes() == fields['pre_v'][7, 0].tobytes()
    capture.check(second)
    assert capture.budget is context and capture.spike is None


def test_capture_remains_finite_after_spike_history_diverges(
    paired: tuple[PairedBlock | FinalSnapshot, ...],
) -> None:
    block = paired[0]
    assert isinstance(block, PairedBlock)
    fields = dict(block.mlx.fields)
    fields['spikes'] = fields['spikes'].copy()
    fields['spikes'][0, 0, 2] = True
    fields['end_g'] = fields['end_g'].copy()
    fields['end_g'][1, 0, 2] = np.nan
    with pytest.raises(ValueError, match='must be finite'):
        CausalCapture().check(
            replace(block, mlx=replace_block(block.mlx, fields=fields))
        )


def test_complete_common_history_records_no_false_cause(
    paired: tuple[PairedBlock | FinalSnapshot, ...],
) -> None:
    capture = CausalCapture()
    for block in paired:
        if isinstance(block, PairedBlock):
            capture.check(block)
    assert capture.audit.step == 101
    assert capture.budget is None and capture.spike is None


@pytest.mark.parametrize('fault', ('missing', 'extra', 'order'))
def test_changed_actual_due_rows_fail_during_common_history(
    paired: tuple[PairedBlock | FinalSnapshot, ...],
    fault: str,
) -> None:
    block = paired[0]
    assert isinstance(block, PairedBlock)
    row = next(
        index for index, trials in enumerate(block.mlx.due_edges) if len(trials[0]) > 1
    )
    due = list(block.mlx.due_edges)
    original = due[row][0]
    changed = (
        original[1:]
        if fault == 'missing'
        else original[::-1]
        if fault == 'order'
        else np.append(original, np.int32(7))
    )
    due[row] = (changed,)
    block = replace(block, mlx=replace_block(block.mlx, due_edges=tuple(due)))
    with pytest.raises(ValueError, match='actual due-edge identities'):
        audit_block(block, CausalAudit())
