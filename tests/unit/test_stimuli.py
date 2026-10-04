import numpy as np
import pytest

from fly_brain.simulation.experiments import EXPERIMENTS, P9_IDS, SUGAR_IDS
from fly_brain.simulation.models import Connectome
from fly_brain.simulation.stimuli import generate, neuron_indices

pytestmark = pytest.mark.unit


def connectome() -> Connectome:
    return Connectome(
        np.array(P9_IDS + SUGAR_IDS[::-1], dtype=np.int64),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )


def test_stimuli_preserve_original_channel_order_in_unsorted_neuron_data() -> None:
    stimulus = generate(connectome(), EXPERIMENTS['two-class'], 100, (0,))
    assert stimulus.targets == tuple(range(22, 1, -1)) + (0, 1)
    assert stimulus.rates_hz == (200.0,) * 21 + (100.0,) * 2
    assert not stimulus.events.flags.writeable


def test_each_trial_has_the_same_schedule_alone_or_in_a_batch_and_shorter_prefix() -> (
    None
):
    full = generate(connectome(), EXPERIMENTS['sugar'], 10000, (0, 1, 2, 3))
    alone = generate(connectome(), EXPERIMENTS['sugar'], 1000, (2,))
    np.testing.assert_array_equal(alone.events[0], full.events[2, :1000])
    repeated = generate(connectome(), EXPERIMENTS['sugar'], 10000, (0, 1, 2, 3))
    assert full.sha256 == repeated.sha256


def test_silencing_reuses_the_sugar_events_without_changing_generator_identity() -> (
    None
):
    original = generate(connectome(), EXPERIMENTS['sugar'], 1000, (0,))
    silenced = generate(connectome(), EXPERIMENTS['sugar-silenced'], 1000, (0,))
    assert original.sha256 == silenced.sha256
    assert EXPERIMENTS['sugar-silenced'].silenced_ids == SUGAR_IDS


def test_frozen_generator_draws_row_major_float64_uniforms_for_every_channel() -> None:
    stimulus = generate(connectome(), EXPERIMENTS['p9'], 1000, (3,))
    generator = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence([20261004, 1, 3]))
    )
    expected = (generator.random((1000, 2)) < 0.01).astype(np.uint8)
    np.testing.assert_array_equal(stimulus.events[0], expected)


def test_silent_control_has_a_real_empty_channel_dimension() -> None:
    stimulus = generate(connectome(), EXPERIMENTS['silent'], 1000, (0,))
    assert stimulus.events.shape == (1, 1000, 0)
    assert stimulus.targets == () and stimulus.rates_hz == ()


def test_unknown_experiment_neuron_fails_before_execution() -> None:
    with pytest.raises(ValueError, match='absent from pinned data'):
        neuron_indices(connectome(), (999,))
