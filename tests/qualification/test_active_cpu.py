from itertools import product

import numpy as np
import pytest
import torch

from fly_brain.qualification.adapters.active_cpu import ActiveSources, step
from fly_brain.qualification.adapters.torch_observer import observe
from fly_brain.qualification.adapters.torch_setup import native_float, prepare, tensor
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
