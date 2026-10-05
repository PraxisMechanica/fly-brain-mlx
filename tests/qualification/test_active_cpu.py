from itertools import product

import numpy as np
import pytest
import torch

from fly_brain.qualification.adapters.active_cpu import ActiveSources, step
from fly_brain.qualification.adapters.torch_observer import capture, observe
from fly_brain.qualification.adapters.torch_setup import (
    native_float,
    prepare,
    replay_inputs,
    tensor,
)
from fly_brain.simulation.models import Connectome
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference]


@pytest.mark.parametrize('silenced', [(), (0,)])
def test_every_binary_mask_preserves_scaled_cancellation_duplicate_and_zero_bytes(
    silenced: tuple[int, ...],
) -> None:
    sources = np.array([0, 0, 0, 1, 1, 1, 2, 2, 3], dtype=np.int32)
    destinations = np.array([1, 1, 2, 2, 2, 1, 1, 3, 0], dtype=np.int32)
    counts = np.array([3, -3, -2, 3, 2, -1, 1, 0, -4], dtype=np.int32)
    connectome = Connectome(
        np.arange(5, dtype=np.int64), sources, destinations, counts, counts * 0.275
    )
    model = prepare(connectome, (), silenced, 4)
    active = ActiveSources.from_model(model)
    masks = np.asarray(list(product((0, 1), repeat=5)), dtype=np.float32)
    for batch in masks.reshape(-1, 4, 5):
        spikes = tensor(batch)
        original = torch.matmul(spikes, model.weights.transpose(0, 1))
        actual = active(spikes)
        assert native_float(actual).tobytes() == native_float(original).tobytes()
        assert (
            native_float(model.scale * actual).tobytes()
            == native_float(model.scale * original).tobytes()
        )
        for row in range(4):
            assert (
                native_float(active(spikes[row : row + 1])).tobytes()
                == native_float(original[row : row + 1]).tobytes()
            )


@pytest.mark.parametrize('empty', [False, True])
@pytest.mark.parametrize('trials', [1, 4])
def test_active_fresh_trajectories_repeat_every_original_native_state_and_delay_byte(
    empty: bool,
    trials: int,
) -> None:
    case = fixture(empty)
    events = case.events[:trials]
    model = prepare(case.connectome, case.targets, (3,), trials)
    original = list(observe(model, events, case.targets))
    candidate = step(model)
    for _ in range(2):
        actual = list(observe(model, events, case.targets, candidate))
        assert [row.native_sha256 for row in actual] == [
            row.native_sha256 for row in original
        ]
        for left, right in zip(original, actual, strict=True):
            for name in left.fields:
                assert left.fields[name].tobytes() == right.fields[name].tobytes()


@pytest.mark.parametrize('value', [0.5, 2, -1, float('nan'), float('inf')])
def test_active_propagation_rejects_nonbinary_recurrent_values(value: float) -> None:
    case = fixture()
    model = prepare(case.connectome, case.targets, (), 1)
    active = ActiveSources.from_model(model)
    with pytest.raises(ValueError, match='binary recurrent'):
        active(torch.full((1, 6), value, dtype=torch.float32))


@pytest.mark.parametrize('value', [0.5, float(2**24), float('nan')])
def test_active_setup_rejects_weights_outside_exact_integer_envelope(
    value: float,
) -> None:
    case = fixture()
    model = prepare(case.connectome, case.targets, (), 1)
    model.weights.values()[0] = value
    with pytest.raises(ValueError, match='exact integer envelope'):
        ActiveSources.from_model(model)


@pytest.mark.parametrize('empty', [False, True])
def test_active_chunked_ordinary_state_matches_observer_and_independent_trials(
    empty: bool,
) -> None:
    case = fixture(empty)
    model = prepare(case.connectome, case.targets, (3,), 4)
    expected = list(observe(model, case.events, case.targets, step(model)))
    advance = step(model)
    with torch.no_grad():
        state = model.state_init()
        begin = 0
        for size in (1, 17, 1, 18, 32, 32):
            for index in range(begin, begin + size):
                counts = replay_inputs(case.events[:, index], case.targets, 6)
                state = advance(counts, *state)
                assert (
                    capture(state, index).native_sha256
                    == expected[index + 1].native_sha256
                )
            begin += size
    assert begin == case.events.shape[1]
    for trial in range(4):
        singleton = prepare(case.connectome, case.targets, (3,), 1)
        actual = observe(
            singleton, case.events[trial : trial + 1], case.targets, step(singleton)
        )
        for batch, single in zip(expected, actual, strict=True):
            assert single.native_sha256 == (batch.native_sha256[trial],)
