import hashlib
from dataclasses import replace

import numpy as np
import pytest

from fly_brain.qualification.session_expectations import (
    CHECK_NAMES,
    expect_step,
    initial_ledger,
    observation_checks,
)
from fly_brain.simulation.models import Connectome
from fly_brain.simulation.observations import (
    PHASE_DTYPES,
    NativeComparison,
    NativeObservation,
)

pytestmark = pytest.mark.unit


def connectome() -> Connectome:
    counts = np.array([2, 0, -1], dtype=np.int32)
    return Connectome(
        np.arange(2, dtype=np.int64),
        np.array([0, 0, 1], dtype=np.int32),
        np.array([1, 1, 0], dtype=np.int32),
        counts,
        counts.astype(np.float64) * 0.275,
    )


def observation(
    step: int, voltage: tuple[float, ...], claim: bool = False, channels: int = 0
) -> NativeObservation:
    shape = (1, len(voltage))
    fields = {
        name: np.full(shape, False if dtype == np.bool_ else 0, dtype=dtype)
        for name, dtype in PHASE_DTYPES.items()
    }
    fields['pre_v'] = np.asarray([voltage], dtype=np.float32)
    fields['pre_not_refractory'] = np.ones(shape, dtype=np.bool_)
    fields['spikes'] = np.full(shape, claim, dtype=np.bool_)
    fields['before_not_refractory'] = np.ones(shape, dtype=np.bool_)
    fields['end_not_refractory'] = np.ones(shape, dtype=np.bool_)
    fields['end_last_spike_step'] = np.full(shape, -100000000, dtype=np.int32)
    fields['accepted_inputs'] = np.zeros((1, channels), dtype=np.bool_)
    return NativeObservation(
        step,
        (0,),
        fields,
        (np.array([], dtype=np.int32),),
        (hashlib.sha256(np.zeros(3, dtype=np.bool_).tobytes()).hexdigest(),),
    )


def test_corrupt_candidate_spike_claims_never_drive_qualification_history() -> None:
    network = connectome()
    state = initial_ledger(network, (), 1, None)
    original_last = state.last_spike_step.tobytes()
    events = np.zeros((1, 0), dtype=np.bool_)
    first = observation(1, (-44, -52))
    state, operands = expect_step(state, first, events, network, ())
    assert operands.spikes.tolist() == [[True, False]]
    assert operands.receiving.tolist() == [[False, True]]
    assert state.last_spike_step.tolist() == [[0, -100000000]]
    assert state.history[0].tolist() == [[True, False]]
    claim_only = NativeComparison(
        1, (0,), np.ones((1, 8), dtype=np.bool_), np.ones((1, 19), dtype=np.bool_)
    )
    flags = observation_checks(first, claim_only, operands)
    assert not flags[0, CHECK_NAMES.index('threshold')]
    assert not flags[0, CHECK_NAMES.index('receiving')]
    assert not flags[0, CHECK_NAMES.index('last_spike_step')]
    for step in range(1, 19):
        actual = observation(step + 1, (-52, -52), claim=True)
        state, operands = expect_step(state, actual, events, network, ())
        assert not operands.spikes.any()
    assert operands.due_sources.tolist() == [[True, False]]
    assert state.last_spike_step.tolist() == [[0, -100000000]]
    assert state.history[1].tolist() == [[False, False]]
    assert (
        initial_ledger(network, (), 1, None).last_spike_step.tobytes() == original_last
    )


@pytest.mark.parametrize('offset,expected', ((-1, False), (0, False), (1, True)))
def test_qualification_threshold_uses_exact_neighboring_float32_values(
    offset: int, expected: bool
) -> None:
    threshold = np.float32(-45)
    value = (
        threshold
        if offset == 0
        else np.nextafter(threshold, np.float32(-np.inf if offset < 0 else np.inf))
    )
    network = connectome()
    actual = observation(1, (float(value), -52), channels=1)
    state, operands = expect_step(
        initial_ledger(network, (0,), 1, None),
        actual,
        np.zeros((1, 1), dtype=np.bool_),
        network,
        (0,),
    )
    assert bool(operands.spikes[0, 0]) == expected
    assert bool(state.history[0][0, 0]) == expected


@pytest.mark.parametrize('step', (0, 2, 19))
def test_qualification_rejects_missing_or_reordered_native_frames(step: int) -> None:
    network = connectome()
    with pytest.raises(ValueError, match='step or clock'):
        expect_step(
            initial_ledger(network, (), 1, None),
            observation(step, (-52, -52)),
            np.zeros((1, 0), dtype=np.bool_),
            network,
            (),
        )


def test_native_comparison_cannot_hide_corrupt_due_identities_or_digest() -> None:
    network = connectome()
    actual = observation(1, (-52, -52))
    _, operands = expect_step(
        initial_ledger(network, (), 1, None),
        actual,
        np.zeros((1, 0), dtype=np.bool_),
        network,
        (),
    )
    comparison = NativeComparison(
        1, (0,), np.ones((1, 8), dtype=np.bool_), np.ones((1, 19), dtype=np.bool_)
    )
    for changed in (
        replace(actual, due_edges=(np.array([0], dtype=np.int32),)),
        replace(actual, due_sha256=('0' * 64,)),
    ):
        flags = observation_checks(changed, comparison, operands)
        assert not flags[0, CHECK_NAMES.index('due')]


@pytest.mark.parametrize('phase', ('pre', 'before', 'end'))
def test_qualification_rejects_nonfinite_values_in_each_actual_phase(
    phase: str,
) -> None:
    network = connectome()
    actual = observation(1, (-52, -52))
    fields = dict(actual.fields)
    fields[phase + '_g'] = np.full((1, 2), np.nan, dtype=np.float32)
    actual = replace(actual, fields=fields)
    _, operands = expect_step(
        initial_ledger(network, (), 1, None),
        actual,
        np.zeros((1, 0), dtype=np.bool_),
        network,
        (),
    )
    comparison = NativeComparison(
        1, (0,), np.ones((1, 8), dtype=np.bool_), np.ones((1, 19), dtype=np.bool_)
    )
    assert not observation_checks(actual, comparison, operands)[
        0, CHECK_NAMES.index('finite_' + phase)
    ]
