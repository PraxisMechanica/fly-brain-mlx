import hashlib
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .observer_stream import FinalSnapshot, PhaseBlock, StepSnapshot
from .reference_queues import ReferenceQueues

if TYPE_CHECKING:
    from fly_brain.simulation.backend.arrays import HostArray

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


def pair_blocks(
    reference: Iterator[StepSnapshot | PhaseBlock | FinalSnapshot],
    mlx: Iterator['MLXBlock'],
    ledger: ReferenceQueues,
) -> Iterator[PairedBlock | FinalSnapshot]:
    begin = 0
    for actual in mlx:
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
        if not actual.checks.all():
            raise ValueError(
                'An actual MLX state or queue failed its independent ledger'
            )
        yield PairedBlock(
            frame,
            actual,
            tuple(snapshots),
            (phase_hash(frame.fields), phase_hash(actual.fields)),
        )
        begin += frame.rows
    final = next(reference, None)
    if not isinstance(final, FinalSnapshot) or final.step.step != begin:
        raise ValueError('Paired observations are missing the reference final state')
    ledger.check(final)
    if next(reference, None) is not None:
        raise ValueError('Paired observations contain extra reference frames')
    yield final
