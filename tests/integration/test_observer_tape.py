import gzip
import io
from pathlib import Path

import pytest

from fly_brain.qualification.adapters.observer_stream import read_frames
from fly_brain.qualification.adapters.observer_tape import record, replay
from tests.unit.test_observer_stream import queued_stream

pytestmark = pytest.mark.integration


def test_recording_preserves_complete_wire_bytes_and_repeat_archive(
    tmp_path: Path,
) -> None:
    shape, parts = queued_stream()
    original = b''.join(parts)
    paths = (tmp_path / 'first.gz', tmp_path / 'repeat.gz')
    for path in paths:
        with record(io.BytesIO(original), path) as source:
            frames = tuple(read_frames(source, shape))
        assert len(frames) == 4
        assert gzip.decompress(path.read_bytes()) == original
        assert len(tuple(replay(path, shape))) == len(frames)
    assert paths[0].read_bytes() == paths[1].read_bytes()


@pytest.mark.parametrize('fault', ['truncated', 'checksum', 'trailing'])
def test_replay_rejects_an_incomplete_or_changed_actual_stream(
    tmp_path: Path, fault: str
) -> None:
    shape, parts = queued_stream()
    original = bytearray(b''.join(parts))
    if fault == 'truncated':
        original = original[:-20]
    elif fault == 'checksum':
        original[-6] ^= 1
    else:
        original.extend(b'unexpected')
    path = tmp_path / 'fault.gz'
    with record(io.BytesIO(original), path) as source:
        source.read()
    with pytest.raises(ValueError):
        tuple(replay(path, shape))
