import struct
import zlib
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

MAGIC = b'FBQOBS01'
PHASE_FIELDS = (
    ('pre', ('v', 'g', 'not_refractory')),
    ('before', ('v', 'g', 'not_refractory')),
    ('end', ('v', 'g', 'lastspike', 'not_refractory')),
)
ObservationArray = NDArray[np.float64 | np.bool_]


class ByteSource(Protocol):
    def read(self, size: int = -1, /) -> bytes: ...


@dataclass(frozen=True)
class StreamShape:
    neurons: int
    steps: int
    channels: int
    pathway_edges: tuple[int, ...]
    block_size: int


@dataclass(frozen=True)
class QueueSnapshot:
    offset: int
    slots: tuple[NDArray[np.int32], ...]


@dataclass(frozen=True)
class PathwaySnapshot:
    queues: tuple[QueueSnapshot, ...]
    delivered: NDArray[np.int32]


@dataclass(frozen=True)
class StepSnapshot:
    step: int
    clock_step: int
    time_s: float
    source_cursor: int
    spikes: NDArray[np.int32]
    source_spikes: NDArray[np.int32]
    pathways: tuple[PathwaySnapshot, ...]


@dataclass(frozen=True)
class PhaseBlock:
    begin: int
    rows: int
    fields: dict[str, ObservationArray]


@dataclass(frozen=True)
class FinalSnapshot:
    step: StepSnapshot
    fields: dict[str, ObservationArray]


class Reader:
    def __init__(self, source: ByteSource, shape: StreamShape) -> None:
        self.source = source
        self.shape = shape
        self.crc = 0

    def take(self, size: int) -> bytes:
        chunks: list[bytes] = []
        remaining = size
        while remaining:
            part = self.source.read(min(remaining, 1024 * 1024))
            if not part:
                raise ValueError('Incomplete observer frame')
            chunks.append(part)
            remaining -= len(part)
        data = b''.join(chunks)
        self.crc = zlib.crc32(data, self.crc)
        return data

    def integer(self, code: str = 'Q') -> int:
        return int(struct.unpack('<' + code, self.take(struct.calcsize(code)))[0])

    def integer_vector(self, maximum: int) -> NDArray[np.int32]:
        size = self.integer()
        if size > maximum:
            raise ValueError('Observer vector exceeds its model bound')
        return np.frombuffer(self.take(size * 4), dtype='<i4')

    def field(self, size: int, name: str) -> ObservationArray:
        if name == 'not_refractory':
            values = np.frombuffer(self.take(size), dtype=np.uint8)
            if np.any(values > 1):
                raise ValueError('Observer Boolean field is not canonical')
            return values.astype(np.bool_)
        return np.frombuffer(self.take(size * 8), dtype='<f8')

    def snapshot(self, expected_step: int) -> StepSnapshot:
        step, clock_step = self.integer(), self.integer()
        time_s = float(struct.unpack('<d', self.take(8))[0])
        cursor = self.integer('i')
        if step != expected_step or clock_step != expected_step:
            raise ValueError('Observer step or clock is out of order')
        if not np.isfinite(time_s) or abs(time_s - step * 0.0001) > 1e-12:
            raise ValueError('Observer clock time is invalid')
        if not -1 <= cursor <= self.shape.steps * self.shape.channels:
            raise ValueError('Observer source cursor is invalid')
        spikes = self.integer_vector(self.shape.neurons)
        source_spikes = self.integer_vector(self.shape.channels)
        pathways: list[PathwaySnapshot] = []
        for edges in self.shape.pathway_edges:
            threads = self.integer()
            if threads != 1:
                raise ValueError('The pinned reference requires one queue thread')
            queues: list[QueueSnapshot] = []
            for _ in range(threads):
                offset, slots = self.integer('i'), self.integer()
                if not 1 <= slots <= 19 or not 0 <= offset < slots:
                    raise ValueError('Observer queue geometry is invalid')
                queues.append(
                    QueueSnapshot(
                        offset, tuple(self.integer_vector(edges) for _ in range(slots))
                    )
                )
            pathways.append(PathwaySnapshot(tuple(queues), self.integer_vector(edges)))
        return StepSnapshot(
            step, clock_step, time_s, cursor, spikes, source_spikes, tuple(pathways)
        )

    def finish_frame(self) -> None:
        expected = self.crc
        checksum = self.integer('I')
        if checksum != expected:
            raise ValueError('Observer frame checksum differs')
        self.crc = 0


def read_frames(
    source: ByteSource, shape: StreamShape
) -> Iterator[StepSnapshot | PhaseBlock | FinalSnapshot]:
    reader = Reader(source, shape)
    if reader.take(len(MAGIC)) != MAGIC:
        raise ValueError('Observer stream signature differs')
    header = tuple(reader.integer() for _ in range(5))
    if header != (
        shape.neurons,
        shape.steps,
        shape.channels,
        len(shape.pathway_edges),
        shape.block_size,
    ):
        raise ValueError('Observer stream dimensions differ')
    reader.finish_frame()
    seen_steps = seen_rows = 0
    while True:
        tag = reader.integer()
        if tag == 1:
            if seen_steps >= shape.steps:
                raise ValueError('Unexpected extra observer step')
            snapshot = reader.snapshot(seen_steps)
            reader.finish_frame()
            seen_steps += 1
            yield snapshot
        elif tag == 2:
            begin, rows = reader.integer(), reader.integer()
            if not (
                shape.block_size
                and begin == seen_rows
                and 0 < rows <= shape.block_size
                and begin + rows == seen_steps
            ):
                raise ValueError('Observer phase block is incomplete or out of order')
            fields: dict[str, ObservationArray] = {}
            for phase, names in PHASE_FIELDS:
                fields[phase + '_t'] = reader.field(rows, 't')
                for name in names:
                    fields[phase + '_' + name] = reader.field(
                        rows * shape.neurons, name
                    ).reshape(rows, shape.neurons)
            reader.finish_frame()
            seen_rows += rows
            yield PhaseBlock(begin, rows, fields)
        elif tag == 3:
            if seen_steps != shape.steps or seen_rows != (
                shape.steps if shape.block_size else 0
            ):
                raise ValueError(
                    'Observer final frame is missing preceding observations'
                )
            final_step = reader.snapshot(shape.steps)
            final_fields = {
                name: reader.field(shape.neurons, name)
                for name in ('v', 'g', 'lastspike', 'not_refractory')
            }
            reader.finish_frame()
            if source.read(1):
                raise ValueError('Observer stream has trailing data')
            yield FinalSnapshot(final_step, final_fields)
            return
        else:
            raise ValueError('Unknown observer frame type')
