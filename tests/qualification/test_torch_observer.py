import numpy as np
import pytest
import torch
from numpy.typing import NDArray

from fly_brain.qualification.adapters.torch_observer import capture, observe
from fly_brain.qualification.adapters.torch_setup import (
    native_float,
    prepare,
    replay_inputs,
)
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference]


@pytest.mark.parametrize('index', range(5))
def test_native_snapshot_owns_and_hashes_every_actual_tensor(index: int) -> None:
    case = fixture()
    state = prepare(case.connectome, case.targets, (), 4).state_init()
    saved = capture(state, -1)
    names = tuple(saved.fields)
    assert all(
        saved.fields[name].tobytes() == native_float(value).tobytes()
        for name, value in zip(names, state, strict=True)
    )
    previous = saved.fields[names[index]].tobytes()
    state[index].add_(1)
    changed = capture(state, 0)
    assert changed.native_sha256 != saved.native_sha256
    assert saved.fields[names[index]].tobytes() == previous
    assert all(value.dtype == np.float32 for value in saved.fields.values())


@pytest.mark.parametrize('index', range(5))
def test_observer_rejects_nonfinite_actual_reference_state(index: int) -> None:
    case = fixture()
    state = prepare(case.connectome, case.targets, (), 1).state_init()
    state[index].fill_(float('nan'))
    with pytest.raises(ValueError, match='Invalid native CPU reference field'):
        capture(state, 0)


@pytest.mark.parametrize('empty', (False, True))
@pytest.mark.parametrize('trials', (1, 4))
def test_streamed_observer_preserves_all_ordinary_state_and_buffer_bytes(
    empty: bool, trials: int
) -> None:
    case = fixture(empty)
    events = case.events[:trials]
    model = prepare(case.connectome, case.targets, (3,), trials)
    state = model.state_init()
    expected = [tuple(native_float(value).copy() for value in state)]
    with torch.no_grad():
        for step in range(events.shape[1]):
            counts = replay_inputs(events[:, step, :], case.targets, 6)
            state = model.forward(counts, *state)
            expected.append(tuple(native_float(value).copy() for value in state))
    gradients = torch.is_grad_enabled()
    snapshots = observe(model, events, case.targets)
    for step, (snapshot, ordinary) in enumerate(zip(snapshots, expected, strict=True)):
        assert snapshot.step == step - 1
        assert torch.is_grad_enabled() == gradients
        assert all(
            actual.tobytes() == value.tobytes()
            for actual, value in zip(snapshot.fields.values(), ordinary, strict=True)
        )


@pytest.mark.parametrize('empty', (False, True))
def test_cpu_state_and_buffer_repeat_and_match_independent_trials(empty: bool) -> None:
    case = fixture(empty)

    def run(events: NDArray[np.uint8]):
        model = prepare(case.connectome, case.targets, (3,), events.shape[0])
        return list(observe(model, events, case.targets))

    batch, repeated = run(case.events), run(case.events)
    assert tuple(row.native_sha256 for row in batch) == tuple(
        row.native_sha256 for row in repeated
    )
    for trial in range(4):
        independent = run(case.events[trial : trial + 1])
        for one, many in zip(independent, batch, strict=True):
            assert one.step == many.step
            assert one.native_sha256 == (many.native_sha256[trial],)
            assert all(
                value.tobytes() == many.fields[name][trial : trial + 1].tobytes()
                for name, value in one.fields.items()
            )


@pytest.mark.parametrize(
    'events',
    (
        np.zeros((1, 2), dtype=np.uint8),
        np.zeros((4, 1, 3), dtype=np.uint8),
        np.zeros((1, 0, 3), dtype=np.uint8),
        np.zeros((1, 2, 2), dtype=np.uint8),
        np.zeros((1, 2, 3), dtype=np.int32),
        np.full((1, 2, 3), 2, dtype=np.uint8),
    ),
)
def test_observer_rejects_invalid_replay_before_yielding_state(
    events: NDArray[np.uint8],
) -> None:
    case = fixture()
    model = prepare(case.connectome, case.targets, (), 1)
    with pytest.raises(ValueError, match='canonical trial-by-step channels'):
        next(observe(model, events, case.targets))
