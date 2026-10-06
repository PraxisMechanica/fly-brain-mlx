import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, fields
from pathlib import Path
from types import ModuleType
from typing import TypeAlias, cast

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.infrastructure.seeded_random import permutation, uniforms
from fly_brain.qualification.fan_in import FanInCases
from fly_brain.qualification.fan_in_service import prepare_cases
from fly_brain.qualification.input_patterns import threshold_uniforms
from fly_brain.simulation import models
from fly_brain.simulation.experiments import EXPERIMENTS, P9_IDS, SUGAR_IDS
from fly_brain.simulation.models import Connectome, Experiment, ExperimentName, Stimulus
from fly_brain.simulation.stimuli import trial_events
from fly_brain.simulation.stimulus_service import schedule

pytestmark = pytest.mark.unit
BASE = '54aea507158774760f8c57e077b1411dc52cdb1e'
ROOT = Path(__file__).resolve().parents[2]
Generate: TypeAlias = Callable[
    [Connectome, Experiment, int, tuple[int, ...], int], Stimulus
]
Cases: TypeAlias = Callable[
    [int, NDArray[np.int32], NDArray[np.int32], NDArray[np.float64]], FanInCases
]


@dataclass(frozen=True)
class Original:
    generate: Generate
    cases: Cases


@pytest.fixture
def original(monkeypatch: pytest.MonkeyPatch) -> Original:
    package = ModuleType('tests._rng_original')
    package.__path__ = []
    monkeypatch.setitem(sys.modules, package.__name__, package)
    monkeypatch.setitem(sys.modules, package.__name__ + '.models', models)
    loaded: dict[str, ModuleType] = {}
    for name, owner in (
        ('input_patterns', 'qualification'),
        ('fan_in', 'qualification'),
        ('stimuli', 'simulation'),
    ):
        module = ModuleType(package.__name__ + '.' + name)
        module.__package__ = package.__name__
        monkeypatch.setitem(sys.modules, module.__name__, module)
        path = f'src/fly_brain/{owner}/{name}.py'
        source = subprocess.check_output(
            ['git', 'show', BASE + ':' + path], cwd=ROOT, text=True
        )
        exec(compile(source, BASE + ':' + path, 'exec'), module.__dict__)
        loaded[name] = module
    return Original(
        cast(Generate, loaded['stimuli'].__dict__['generate']),
        cast(Cases, loaded['fan_in'].__dict__['build_cases']),
    )


def connectome() -> Connectome:
    return Connectome(
        np.array(P9_IDS + SUGAR_IDS[::-1], dtype=np.int64),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )


def same(left: object, right: object) -> None:
    if isinstance(left, np.ndarray):
        assert isinstance(right, np.ndarray)
        a, b = cast(NDArray[np.generic], left), cast(NDArray[np.generic], right)
        assert (a.dtype.str, a.shape, a.tobytes(), a.flags.writeable) == (
            b.dtype.str,
            b.shape,
            b.tobytes(),
            b.flags.writeable,
        )
    else:
        assert left == right


@pytest.mark.parametrize('name', tuple(EXPERIMENTS))
@pytest.mark.parametrize('seed', (0, 20261004, 91))
@pytest.mark.parametrize('trials', ((0,), (2, 0, 4), (0, 0)))
def test_every_stimulus_field_matches_the_exact_original_source(
    original: Original, name: ExperimentName, seed: int, trials: tuple[int, ...]
) -> None:
    network, experiment = connectome(), EXPERIMENTS[name]
    old = original.generate(network, experiment, 137, trials, seed)
    new = schedule(network, experiment, 137, trials, seed, draw_uniforms=uniforms)
    for field in fields(Stimulus):
        same(getattr(old, field.name), getattr(new, field.name))


@pytest.mark.parametrize(
    'counts,sources',
    (
        ((), ()),
        ((2405, 466), (0, 1)),
        ((2405, -2404, -1, 0, 7, 7), (7, 3, 7, 2, 5, 3)),
    ),
)
@pytest.mark.parametrize('target', (3, 19, 11645))
def test_every_case_field_matches_original_masks_permutation_and_arithmetic(
    original: Original, counts: tuple[int, ...], sources: tuple[int, ...], target: int
) -> None:
    c, s = np.array(counts, dtype=np.int32), np.array(sources, dtype=np.int32)
    weights = c.astype(np.float64) * 0.275
    old = original.cases(target, s, c, weights)
    new = prepare_cases(
        target, s, c, weights, draw_uniforms=uniforms, permute=permutation
    )
    for field in fields(FanInCases):
        same(getattr(old, field.name), getattr(new, field.name))


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
        (2, 0, 4),
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

    schedule(connectome(), EXPERIMENTS['silent'], 17, (4,), 0, draw_uniforms=draw)
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
        schedule(connectome(), EXPERIMENTS['sugar'], 5, (0,), 31, draw_uniforms=draw)


def test_wrong_seed_reused_generator_and_substitute_permutation_lose_original_bytes(
    original: Original,
) -> None:
    expected = original.generate(connectome(), EXPERIMENTS['p9'], 1000, (3,), 20261004)

    def wrong_seed(
        seed: tuple[int, int, int], size: tuple[int, int]
    ) -> NDArray[np.float64]:
        return uniforms((seed[0] + 1, seed[1], seed[2]), size)

    changed = schedule(
        connectome(), EXPERIMENTS['p9'], 1000, (3,), 20261004, draw_uniforms=wrong_seed
    )
    assert changed.sha256 != expected.sha256
    c, s = (
        np.array([2405, -2404, -1, 7, 3, 0], dtype=np.int32),
        np.arange(6, dtype=np.int32),
    )
    old = original.cases(19, s, c, c * 0.275)
    shared = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence([20261004, 783, 19, 0, 0]))
    )

    def reuse(seed: tuple[int, int, int, int, int], size: int) -> NDArray[np.float64]:
        return shared.random(size)

    reused = prepare_cases(
        19, s, c, c * 0.275, draw_uniforms=reuse, permute=permutation
    )
    assert reused.masks.tobytes() != old.masks.tobytes()

    def ordered(seed: tuple[int, int, int], size: int) -> NDArray[np.int64]:
        return np.arange(size, dtype=np.int64)

    changed_order = prepare_cases(
        19, s, c, c * 0.275, draw_uniforms=uniforms, permute=ordered
    )
    assert changed_order.orders.tobytes() != old.orders.tobytes()


def test_duplicate_zero_rate_channels_keep_draw_shape_and_strict_threshold() -> None:
    identifier = P9_IDS[0]
    experiment = Experiment('p9', 2, 2, (identifier, identifier), (0.0, 1000.0))
    values = np.array([[0.0, 0.1], [0.5, np.nextafter(0.1, 0.0)]], dtype=np.float64)
    before = values.tobytes()
    calls: list[object] = []

    def draw(seed: tuple[int, int, int], size: tuple[int, int]) -> NDArray[np.float64]:
        calls.append((seed, size))
        return values

    result = schedule(connectome(), experiment, 2, (4,), 31, draw_uniforms=draw)
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
