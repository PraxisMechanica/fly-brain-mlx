from typing import cast

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.infrastructure.seeded_random import permutation, uniforms
from fly_brain.qualification.fan_in_service import prepare_cases
from fly_brain.qualification.input_patterns import threshold_uniforms
from fly_brain.simulation.experiments import EXPERIMENTS, P9_IDS, SUGAR_IDS
from fly_brain.simulation.identifiers import (
    FlyWireIds64,
    NeuronRows32,
    TrialId,
)
from fly_brain.simulation.models import Connectome, Experiment
from fly_brain.simulation.stimuli import trial_events
from fly_brain.simulation.stimulus_service import schedule

pytestmark = pytest.mark.unit


def connectome() -> Connectome:
    return Connectome(
        FlyWireIds64(np.array(P9_IDS + SUGAR_IDS[::-1], dtype=np.int64)),
        NeuronRows32(np.array([], dtype=np.int32)),
        NeuronRows32(np.array([], dtype=np.int32)),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )


def test_trial_request_order_and_immediate_preparation_survive_shared_buffers() -> None:
    calls: list[tuple[tuple[int, int, int], tuple[int, int]]] = []
    buffer = np.empty((5, 21), dtype=np.float64)

    def draw(seed: tuple[int, int, int], size: tuple[int, int]) -> NDArray[np.float64]:
        calls.append((seed, size))
        buffer.fill(0.0 if seed[2] == 2 else 0.75)
        return buffer

    result = schedule(
        connectome(),
        EXPERIMENTS['sugar-silenced'],
        5,
        (TrialId(2), TrialId(0), TrialId(4)),
        31,
        draw_uniforms=draw,
    )
    assert calls == [((31, 0, trial), (5, 21)) for trial in (2, 0, 4)]
    assert result.events[0].all() and not result.events[1:].any()
    deferred = [draw((31, 0, trial), (5, 21)) for trial in (2, 0, 4)]
    assert not (deferred[0] < 0.02).any()


def test_mask_request_order_and_independent_permutation_survive_shared_buffers() -> (
    None
):
    calls: list[object] = []
    buffer = np.empty(2, dtype=np.float64)

    def draw(seed: tuple[int, int, int, int, int], size: int) -> NDArray[np.float64]:
        calls.append((seed, size))
        buffer.fill(0.0 if seed[4] % 2 == 0 else 0.75)
        return buffer

    def permute(seed: tuple[int, int, int], size: int) -> NDArray[np.int64]:
        calls.append((seed, size))
        return np.arange(size, dtype=np.int64)[::-1]

    source = np.array([7, 3, 7], dtype=np.int32)
    counts = np.array([1, 2, 3], dtype=np.int32)
    cases = prepare_cases(
        19, source, counts, counts * 0.275, draw_uniforms=draw, permute=permute
    )
    assert calls == [
        ((20261004, 783, 19, index, replicate), 2)
        for index in range(4)
        for replicate in range(16)
    ] + [((20261004, 784, 19), 3)]
    assert cases.masks[6::2].all() and not cases.masks[7::2].any()
    np.testing.assert_array_equal(cases.orders[2], [2, 1, 0])


def test_empty_inputs_still_issue_the_original_draw_and_permutation_calls() -> None:
    calls: list[object] = []

    def draw(seed: tuple[int, ...], size: int | tuple[int, int]) -> NDArray[np.float64]:
        calls.append((seed, size))
        return uniforms(seed, size)

    def permute(seed: tuple[int, ...], size: int) -> NDArray[np.int64]:
        calls.append((seed, size))
        return permutation(seed, size)

    schedule(
        connectome(), EXPERIMENTS['silent'], 17, (TrialId(4),), 0, draw_uniforms=draw
    )
    prepare_cases(
        3,
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
        draw_uniforms=draw,
        permute=permute,
    )
    assert calls[0] == ((0, 5, 4), (17, 0)) and len(calls) == 66
    assert calls[-1] == ((20261004, 784, 3), 0)


def test_wrong_native_sample_shape_is_rejected_before_it_can_broadcast() -> None:
    def draw(seed: tuple[int, int, int], size: tuple[int, int]) -> NDArray[np.float64]:
        return np.zeros((1, size[1]), dtype=np.float64)

    with pytest.raises(ValueError, match='shape'):
        schedule(
            connectome(), EXPERIMENTS['sugar'], 5, (TrialId(0),), 31, draw_uniforms=draw
        )


def test_wrong_seed_reused_generator_and_substitute_permutation_change_inputs() -> None:
    expected = schedule(
        connectome(),
        EXPERIMENTS['p9'],
        1000,
        (TrialId(3),),
        20261004,
        draw_uniforms=uniforms,
    )

    def wrong_seed(
        seed: tuple[int, int, int], size: tuple[int, int]
    ) -> NDArray[np.float64]:
        return uniforms((seed[0] + 1, seed[1], seed[2]), size)

    changed = schedule(
        connectome(),
        EXPERIMENTS['p9'],
        1000,
        (TrialId(3),),
        20261004,
        draw_uniforms=wrong_seed,
    )
    assert changed.sha256 != expected.sha256
    c, s = (
        np.array([2405, -2404, -1, 7, 3, 0], dtype=np.int32),
        np.arange(6, dtype=np.int32),
    )
    expected_cases = prepare_cases(
        19, s, c, c * 0.275, draw_uniforms=uniforms, permute=permutation
    )
    shared = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence([20261004, 783, 19, 0, 0]))
    )

    def reuse(seed: tuple[int, int, int, int, int], size: int) -> NDArray[np.float64]:
        return shared.random(size)

    reused = prepare_cases(
        19, s, c, c * 0.275, draw_uniforms=reuse, permute=permutation
    )
    assert reused.masks.tobytes() != expected_cases.masks.tobytes()

    def ordered(seed: tuple[int, int, int], size: int) -> NDArray[np.int64]:
        return np.arange(size, dtype=np.int64)

    changed_order = prepare_cases(
        19, s, c, c * 0.275, draw_uniforms=uniforms, permute=ordered
    )
    assert changed_order.orders.tobytes() != expected_cases.orders.tobytes()


def test_duplicate_zero_rate_channels_keep_draw_shape_and_strict_threshold() -> None:
    identifier = P9_IDS[0]
    experiment = Experiment('p9', 2, 2, (identifier, identifier), (0.0, 1000.0))
    values = np.array([[0.0, 0.1], [0.5, np.nextafter(0.1, 0.0)]], dtype=np.float64)
    before = values.tobytes()
    calls: list[object] = []

    def draw(seed: tuple[int, int, int], size: tuple[int, int]) -> NDArray[np.float64]:
        calls.append((seed, size))
        return values

    result = schedule(
        connectome(), experiment, 2, (TrialId(4),), 31, draw_uniforms=draw
    )
    assert calls == [((31, 2, 4), (2, 2))] and result.targets == (0, 0)
    np.testing.assert_array_equal(result.events, [[[0, 0], [0, 1]]])
    assert values.tobytes() == before
    assert not np.shares_memory(result.events, values)


@pytest.mark.parametrize('dtype', (np.float32, np.int64))
def test_uniform_values_cannot_change_native_precision(dtype: type[np.generic]) -> None:
    with pytest.raises(ValueError, match='float64'):
        trial_events((100.0,), cast(NDArray[np.float64], np.zeros((2, 1), dtype=dtype)))
    with pytest.raises(ValueError, match='float64'):
        threshold_uniforms(cast(NDArray[np.float64], np.zeros(2, dtype=dtype)), 0.1)
