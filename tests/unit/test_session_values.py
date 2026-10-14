import hashlib
import inspect

import numpy as np
import pytest

from fly_brain.qualification.session_expectations import expect_step, initial_ledger
from fly_brain.simulation.identifiers import TrialId
from fly_brain.simulation.observations import (
    HostSnapshot,
    NativeComparison,
    NativeObservation,
    ObservationOperands,
    PhysicalQueueObservation,
)
from tests.unit.test_session_expectations import connectome, observation

pytestmark = pytest.mark.unit


def test_actual_phase_bits_and_due_identities_are_detached_and_immutable() -> None:
    fields = dict(observation(1, (-52, -52)).fields)
    bits = (
        np.array([0x80000000, 0x7FC01234], dtype=np.uint32)
        .view(np.float32)
        .reshape(1, 2)
    )
    edges = np.array([2, 0], dtype=np.int32)
    fields['pre_v'] = bits
    actual = NativeObservation(1, (TrialId(0),), fields, (edges,), ('digest',))
    before = bits.tobytes(), edges.tobytes()
    bits[:] = 0
    edges[:] = 1
    assert actual.fields['pre_v'].tobytes() == before[0]
    assert actual.due_edges[0].tobytes() == before[1]
    for value in (*actual.fields.values(), *actual.due_edges):
        with pytest.raises(ValueError):
            value.setflags(write=True)


@pytest.mark.parametrize('field', ('pre_v', 'spikes', 'accepted_inputs'))
def test_actual_phase_snapshots_reject_missing_native_fields(field: str) -> None:
    actual = observation(1, (-52, -52))
    fields = dict(actual.fields)
    fields.pop(field)
    with pytest.raises(ValueError, match='every actual phase'):
        NativeObservation(
            actual.completed_steps,
            actual.trial_indices,
            fields,
            actual.due_edges,
            actual.due_sha256,
        )


def test_actual_snapshot_rejects_changed_native_dtype() -> None:
    actual = observation(1, (-52, -52))
    fields = dict(actual.fields)
    fields['pre_v'] = fields['pre_v'].astype(np.float64)
    with pytest.raises(ValueError, match='dtype or phase'):
        NativeObservation(
            actual.completed_steps,
            actual.trial_indices,
            fields,
            actual.due_edges,
            actual.due_sha256,
        )


@pytest.mark.parametrize('columns', (0, 7, 9))
def test_native_comparisons_require_all_eight_supplied_gates(columns: int) -> None:
    with pytest.raises(ValueError, match='every supplied gate'):
        NativeComparison(
            1,
            (TrialId(0),),
            np.ones((1, columns), dtype=np.bool_),
            np.ones((1, 19), dtype=np.bool_),
        )


def test_queue_and_comparison_operands_keep_detached_read_only_ownership() -> None:
    network = connectome()
    _, operands = expect_step(
        initial_ledger(network, (), 1, None),
        observation(1, (-52, -52)),
        np.zeros((1, 0), dtype=np.bool_),
        network,
        (),
    )
    queue = np.ones((19, 1, 3), dtype=np.bool_)
    actual = PhysicalQueueObservation(1, (TrialId(0),), queue)
    original = actual.queue.tobytes()
    queue[:] = False
    assert actual.queue.tobytes() == original
    assert len(actual.sha256) == 1 and len(actual.slot_sha256[0]) == 19
    for value in (
        actual.queue,
        operands.sources,
        operands.destinations,
        operands.spikes,
        operands.receiving,
        operands.pending_sources,
    ):
        with pytest.raises(ValueError):
            value.setflags(write=True)


def test_comparison_construction_rejects_omitted_policy_factors() -> None:
    parameters = inspect.signature(ObservationOperands).parameters
    for name in (
        'due_sources',
        'accepted_destinations',
        'discarded_destinations',
        'pending_sources',
    ):
        assert parameters[name].default is inspect.Parameter.empty


def test_snapshot_reuses_complete_immutable_bytes_and_detaches_other_buffers() -> None:
    mutable = np.arange(12, dtype=np.int32)
    frozen = HostSnapshot.capture(mutable)
    repeated = HostSnapshot.capture(frozen.array)
    assert repeated.payload is frozen.payload
    fragment = HostSnapshot.capture(frozen.array[1:])
    assert fragment.payload == mutable[1:].tobytes()
    assert fragment.payload is not frozen.payload
    alias = mutable.view()
    alias.setflags(write=False)
    detached = HostSnapshot.capture(alias)
    mutable[:] = -1
    assert np.array_equal(detached.array, np.arange(12, dtype=np.int32))


def test_independent_graph_maps_are_frozen_once_and_shared_across_steps() -> None:
    network = connectome()
    state = initial_ledger(network, (), 1, None)
    sources, destinations = state.sources.base, state.destinations.base
    for step in range(2):
        state, operands = expect_step(
            state,
            observation(step + 1, (-52, -52)),
            np.zeros((1, 0), dtype=np.bool_),
            network,
            (),
        )
        assert state.sources.base is operands.sources.base is sources
        assert state.destinations.base is operands.destinations.base is destinations


@pytest.mark.parametrize('trials', (1, 4))
def test_queue_hashes_keep_canonical_native_slot_and_trial_byte_order(
    trials: int,
) -> None:
    queue = np.arange(19 * trials * 7).reshape(19, trials, 7) % 3 == 0
    actual = PhysicalQueueObservation(32, tuple(map(TrialId, range(trials))), queue)
    assert actual.sha256 == tuple(
        hashlib.sha256(queue[:, trial].tobytes(order='C')).hexdigest()
        for trial in range(trials)
    )
    assert actual.slot_sha256 == tuple(
        tuple(
            hashlib.sha256(queue[slot, trial].tobytes()).hexdigest()
            for slot in range(19)
        )
        for trial in range(trials)
    )
