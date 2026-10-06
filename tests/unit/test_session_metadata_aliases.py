from collections.abc import Callable

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.qualification.session_expectations import expect_step, initial_ledger
from fly_brain.simulation.observations import (
    NativeComparison,
    ObservationInitialState,
    PhysicalQueueObservation,
    ReductionRow,
)
from tests.unit.test_session_expectations import connectome, observation
from tests.unit.test_session_observer_faults import Session

pytestmark = pytest.mark.unit


def assert_canonical_metadata_survives(
    reader: Callable[[], NDArray[np.generic]],
) -> None:
    alias = reader()
    expected = alias.dtype, alias.shape, alias.tobytes()
    for name, metadata in (('shape', (alias.size,)), ('dtype', np.dtype(np.uint8))):
        setattr(alias, name, metadata)
    fresh = reader()
    assert (fresh.dtype, fresh.shape, fresh.tobytes()) == expected
    assert isinstance(fresh.base, bytes)
    with pytest.raises(ValueError):
        fresh.setflags(write=True)
    assert np.shares_memory(alias, fresh) or fresh.size == 0


def test_byte_backing_alone_does_not_freeze_array_metadata() -> None:
    canonical = np.frombuffer(
        np.arange(4, dtype=np.int32).tobytes(), dtype=np.int32
    ).reshape(2, 2)
    with pytest.raises(AssertionError):
        assert_canonical_metadata_survives(lambda: canonical)


def test_phase_due_configuration_operand_and_comparison_aliases_cannot_change_canonical_metadata() -> (
    None
):
    network = connectome()
    actual = observation(1, (-52, -52))
    state, operands = expect_step(
        initial_ledger(network, (), 1, None),
        actual,
        np.zeros((1, 0), dtype=np.bool_),
        network,
        (),
    )
    comparison = NativeComparison(
        1, (0,), np.ones((1, 8), dtype=np.bool_), np.ones((1, 19), dtype=np.bool_)
    )
    configuration = Session('').configuration
    initial = ObservationInitialState(
        np.zeros((1, 2), dtype=np.float64),
        np.zeros((1, 2), dtype=np.float64),
        np.zeros((1, 2), dtype=np.int32),
    )
    readers: tuple[Callable[[], NDArray[np.generic]], ...] = (
        lambda: actual.fields['pre_v'],
        lambda: actual.fields['spikes'],
        lambda: actual.due_edges[0],
        lambda: configuration.sources,
        lambda: configuration.refractory_steps,
        lambda: configuration.initial_last_spike_step,
        lambda: initial.voltage_mv,
        lambda: operands.sources,
        lambda: operands.spikes,
        lambda: operands.last_spike_step,
        lambda: operands.pending_sources,
        lambda: comparison.gates_equal,
        lambda: comparison.queue_equal,
        lambda: state.last_spike_step,
        lambda: state.history[0],
    )
    for reader in readers:
        assert_canonical_metadata_survives(reader)


def test_physical_queue_block_and_reduction_row_views_preserve_canonical_dtype_shape_and_hashes() -> (
    None
):
    actual = observation(1, (-52, -52))
    queue = PhysicalQueueObservation(1, (0,), np.zeros((19, 1, 3), dtype=np.bool_))
    block = SessionBlock(
        0,
        1,
        (0,),
        {name: np.stack([value]) for name, value in actual.fields.items()},
        np.ones((1, 1, 30), dtype=np.bool_),
        queue.sha256,
        queue.slot_sha256,
        queue.queue,
        (actual.due_edges,),
        (actual.due_sha256,),
    )
    row = ReductionRow(
        0,
        np.array([0, -1], dtype=np.int32),
        np.array([0.0, -0.0], dtype=np.float32),
        np.array([True, False], dtype=np.bool_),
    )
    original_hashes = queue.sha256, queue.slot_sha256

    def final_queue() -> NDArray[np.bool_]:
        value = block.final_queue
        assert value is not None
        return value

    for reader in (
        lambda: queue.queue,
        lambda: block.fields['pre_v'],
        lambda: block.checks,
        lambda: block.due_edges[0][0],
        final_queue,
        lambda: row.edges,
        lambda: row.counts,
        lambda: row.occupied,
    ):
        assert_canonical_metadata_survives(reader)
    assert original_hashes == (queue.sha256, queue.slot_sha256)
