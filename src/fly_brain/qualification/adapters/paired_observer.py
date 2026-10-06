import hashlib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import numpy as np

from fly_brain.qualification.causality import CausalAudit, advance_audit

from .observer_stream import FinalSnapshot, PhaseBlock, StepSnapshot
from .reference_queues import ReferenceQueues

if TYPE_CHECKING:
    from fly_brain.simulation.observations import HostArray

    from .mlx_observer import MLXBlock


@dataclass(frozen=True)
class PairedBlock:
    reference: PhaseBlock
    mlx: 'MLXBlock'
    snapshots: tuple[StepSnapshot, ...]
    native_sha256: tuple[str, str]


def phase_hash(fields: Mapping[str, 'HostArray']) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(fields.items()):
        digest.update(str((name, value.dtype.str, value.shape)).encode())
        digest.update(value.tobytes(order='C'))
    return digest.hexdigest()


def read_block(
    reference: Iterator[StepSnapshot | PhaseBlock | FinalSnapshot],
    actual: 'MLXBlock',
    ledger: ReferenceQueues,
) -> PairedBlock:
    begin = ledger.step
    snapshots: list[StepSnapshot] = []
    while isinstance(frame := next(reference, None), StepSnapshot):
        ledger.check(frame)
        snapshots.append(frame)
        if len(snapshots) > 32:
            raise ValueError('Paired observation exceeds the block bound')
    if not isinstance(frame, PhaseBlock) or (
        frame.begin != begin
        or actual.begin != begin
        or frame.rows != actual.rows
        or frame.rows != len(snapshots)
        or not 1 <= frame.rows <= 32
    ):
        raise ValueError('Paired phase blocks have different coverage')
    if (
        not actual.queue_sha256
        or actual.checks.shape != (frame.rows, len(actual.queue_sha256), 30)
        or not actual.checks.all()
    ):
        raise ValueError('An actual MLX state or queue failed its independent ledger')
    return PairedBlock(
        frame,
        actual,
        tuple(snapshots),
        (phase_hash(frame.fields), phase_hash(actual.fields)),
    )


def finish_reference(
    reference: Iterator[StepSnapshot | PhaseBlock | FinalSnapshot],
    ledger: ReferenceQueues,
) -> FinalSnapshot:
    final = next(reference, None)
    if not isinstance(final, FinalSnapshot) or final.step.step != ledger.step:
        raise ValueError('Paired observations are missing the reference final state')
    ledger.check(final)
    if next(reference, None) is not None:
        raise ValueError('Paired observations contain extra reference frames')
    return final


def pair_blocks(
    reference: Iterator[StepSnapshot | PhaseBlock | FinalSnapshot],
    mlx: Iterator['MLXBlock'],
    ledger: ReferenceQueues,
) -> Iterator[PairedBlock | FinalSnapshot]:
    for actual in mlx:
        yield read_block(reference, actual, ledger)
    yield finish_reference(reference, ledger)


def trial_block(block: 'MLXBlock', trial: int) -> 'MLXBlock':
    return replace(
        block,
        fields={
            name: value[:, trial : trial + 1] for name, value in block.fields.items()
        },
        checks=block.checks[:, trial : trial + 1],
        queue_sha256=(block.queue_sha256[trial],),
        final_queue=None
        if block.final_queue is None
        else block.final_queue[:, trial : trial + 1],
        due_edges=tuple((row[trial],) for row in block.due_edges),
        due_sha256=tuple((row[trial],) for row in block.due_sha256),
    )


def audit_block(block: PairedBlock, audit: CausalAudit) -> CausalAudit:
    reference, mlx = block.reference.fields, block.mlx.fields
    neurons = reference['pre_v'].shape[1]
    if mlx['pre_v'].shape != (block.reference.rows, 1, neurons):
        raise ValueError('Each paired causal audit requires one independent trial')
    names = tuple(
        phase + '_' + field
        for phase in ('pre', 'before', 'end')
        for field in ('v', 'g')
    )
    for phase in ('pre', 'before', 'end'):
        expected = (
            np.arange(
                block.reference.begin, block.reference.begin + block.reference.rows
            )
            * 0.0001
        )
        if not np.allclose(reference[phase + '_t'], expected, rtol=0, atol=1e-12):
            raise ValueError('Reference phase clocks differ from the paired steps')
    if not np.isfinite(reference['end_lastspike']).all():
        raise ValueError('Reference last-spike clocks must remain finite')
    for row, snapshot in enumerate(block.snapshots):
        spikes = np.zeros(neurons, dtype=np.bool_)
        spikes[snapshot.spikes] = True
        actual_spikes = np.asarray(mlx['spikes'][row, 0], dtype=np.bool_)
        if audit.first_spike_step is None:
            delivered = next(
                (
                    path.delivered
                    for path in snapshot.pathways
                    if len(path.queues[0].slots) == 19
                ),
                np.empty(0, dtype=np.int32),
            )
            if not np.array_equal(np.sort(delivered), block.mlx.due_edges[row][0]):
                raise ValueError('Common-history actual due-edge identities differ')
            phases = (
                ('pre',)
                if np.any(spikes != actual_spikes)
                else ('pre', 'before', 'end')
            )
            for phase in phases:
                if not np.array_equal(
                    reference[phase + '_not_refractory'][row],
                    mlx[phase + '_not_refractory'][row, 0],
                ):
                    raise ValueError('Common-history refractory observations differ')
            if np.array_equal(spikes, actual_spikes) and not np.array_equal(
                np.rint(reference['end_lastspike'][row] / 0.0001),
                mlx['end_last_spike_step'][row, 0],
            ):
                raise ValueError('Common-history last-spike clocks differ')
        audit = advance_audit(
            audit,
            snapshot.step,
            {
                name: np.asarray(reference[name][row], dtype=np.float64) * 1000
                for name in names
            },
            {name: np.asarray(mlx[name][row, 0], dtype=np.float32) for name in names},
            spikes,
            actual_spikes,
        )
    return audit
