import gzip
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .observer_stream import (
    ByteSource,
    FinalSnapshot,
    PhaseBlock,
    StepSnapshot,
    StreamShape,
    read_frames,
)


class ByteSink(Protocol):
    def write(self, data: bytes, /) -> int: ...


@dataclass
class RecordingSource:
    source: ByteSource
    destination: ByteSink

    def read(self, size: int = -1, /) -> bytes:
        data = self.source.read(size)
        self.destination.write(data)
        return data


@contextmanager
def record(source: ByteSource, path: Path) -> Generator[RecordingSource, None, None]:
    with (
        path.open('xb') as destination,
        gzip.GzipFile(
            filename='', mode='wb', fileobj=destination, compresslevel=1, mtime=0
        ) as compressed,
    ):
        yield RecordingSource(source, compressed)


def replay(
    path: Path, shape: StreamShape
) -> Iterator[StepSnapshot | PhaseBlock | FinalSnapshot]:
    with gzip.open(path, 'rb') as source:
        yield from read_frames(source, shape)
