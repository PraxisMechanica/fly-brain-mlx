import io
import struct
import zlib

import numpy as np
import pytest

from fly_brain.qualification.adapters.observer_stream import (
    MAGIC,
    PHASE_FIELDS,
    FinalSnapshot,
    PhaseBlock,
    StepSnapshot,
    StreamShape,
    read_frames,
)

pytestmark = pytest.mark.unit


def framed(body: bytes) -> bytes:
    return body + struct.pack('<I', zlib.crc32(body))


def snapshot(step: int) -> bytes:
    return struct.pack('<QQdiQQ', step, step, step * 0.0001, -1, 0, 0)


def stream() -> tuple[StreamShape, tuple[bytes, ...]]:
    shape = StreamShape(2, 2, 0, (), 2)
    header = framed(MAGIC + struct.pack('<QQQQQ', 2, 2, 0, 0, 2))
    steps = tuple(framed(struct.pack('<Q', 1) + snapshot(step)) for step in range(2))
    body = struct.pack('<QQQ', 2, 0, 2)
    for _, names in PHASE_FIELDS:
        body += np.array([0, 0.0001], dtype='<f8').tobytes()
        for name in names:
            body += np.ones(
                4, dtype=np.uint8 if name == 'not_refractory' else '<f8'
            ).tobytes()
    phase = framed(body)
    final = framed(
        struct.pack('<Q', 3)
        + snapshot(2)
        + np.ones(6, dtype='<f8').tobytes()
        + b'\x01\x01'
    )
    return shape, (header, *steps, phase, final)


def test_complete_frames_preserve_all_intermediate_states_and_final_state() -> None:
    shape, parts = stream()
    result = list(read_frames(io.BytesIO(b''.join(parts)), shape))
    assert [type(frame) for frame in result] == [
        StepSnapshot,
        StepSnapshot,
        PhaseBlock,
        FinalSnapshot,
    ]
    assert isinstance(result[2], PhaseBlock) and result[2].fields['before_v'].shape == (
        2,
        2,
    )


@pytest.mark.parametrize('cut', [1, 4, 20, 100])
def test_truncated_transport_cannot_be_accepted_as_complete(cut: int) -> None:
    shape, parts = stream()
    with pytest.raises(ValueError, match='Incomplete'):
        list(read_frames(io.BytesIO(b''.join(parts)[:-cut]), shape))


def test_omitted_step_is_detected_before_a_final_result() -> None:
    shape, parts = stream()
    with pytest.raises(ValueError, match='out of order'):
        list(read_frames(io.BytesIO(parts[0] + b''.join(parts[2:])), shape))


def test_reordered_steps_are_detected() -> None:
    shape, parts = stream()
    with pytest.raises(ValueError, match='out of order'):
        list(
            read_frames(
                io.BytesIO(parts[0] + parts[2] + parts[1] + b''.join(parts[3:])), shape
            )
        )


def test_missing_final_partial_observation_block_is_rejected() -> None:
    shape, parts = stream()
    with pytest.raises(ValueError, match='missing preceding'):
        list(read_frames(io.BytesIO(b''.join(parts[:3]) + parts[-1]), shape))


def test_changed_state_byte_between_endpoints_fails_checksum() -> None:
    shape, parts = stream()
    modified = bytearray(parts[3])
    modified[60] ^= 1
    with pytest.raises(ValueError, match='checksum'):
        list(read_frames(io.BytesIO(b''.join(parts[:3]) + modified + parts[-1]), shape))


def test_trailing_frames_cannot_be_silently_ignored() -> None:
    shape, parts = stream()
    with pytest.raises(ValueError, match='trailing'):
        list(read_frames(io.BytesIO(b''.join(parts) + b'bad'), shape))


def test_declared_dimensions_must_match_the_expected_model() -> None:
    _, parts = stream()
    with pytest.raises(ValueError, match='dimensions'):
        list(read_frames(io.BytesIO(b''.join(parts)), StreamShape(3, 2, 0, (), 2)))


class ShortReads(io.BytesIO):
    def read(self, size: int | None = -1) -> bytes:
        return super().read(min(size, 3) if size is not None and size > 0 else size)


def test_pipe_reads_may_split_a_frame_without_losing_bytes() -> None:
    shape, parts = stream()
    result = list(read_frames(ShortReads(b''.join(parts)), shape))
    assert isinstance(result[-1], FinalSnapshot)


def queued_stream() -> tuple[StreamShape, tuple[bytes, ...]]:
    _, parts = stream()
    shape = StreamShape(2, 2, 0, (3,), 2)
    queue = struct.pack('<QiQ', 1, 0, 19)
    queue += struct.pack('<Q', 0) * 18
    queue += struct.pack('<QiiQ', 2, 0, 2, 0)
    header = framed(MAGIC + struct.pack('<QQQQQ', 2, 2, 0, 1, 2))
    steps = tuple(
        framed(struct.pack('<Q', 1) + snapshot(step) + queue) for step in range(2)
    )
    final = framed(
        struct.pack('<Q', 3)
        + snapshot(2)
        + queue
        + np.ones(6, dtype='<f8').tobytes()
        + b'\x01\x01'
    )
    return shape, (header, *steps, parts[3], final)


def test_physical_queue_offset_slots_and_ordered_edges_are_preserved() -> None:
    shape, parts = queued_stream()
    result = list(read_frames(io.BytesIO(b''.join(parts)), shape))
    assert isinstance(result[0], StepSnapshot)
    queue = result[0].pathways[0].queues[0]
    assert queue.offset == 0 and queue.slots[18].tolist() == [0, 2]


def test_changed_queue_entry_fails_checksum() -> None:
    shape, parts = queued_stream()
    modified = bytearray(parts[1])
    modified[-20] ^= 1
    with pytest.raises(ValueError, match='checksum'):
        list(read_frames(io.BytesIO(parts[0] + modified + b''.join(parts[2:])), shape))
