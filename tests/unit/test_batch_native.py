import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.batch_native import (
    Engine,
    compare_final_trial,
    require_fields,
    trial_spikes,
)

pytestmark = pytest.mark.unit


def native(engine: Engine, trials: int) -> dict[str, NDArray[np.generic]]:
    arrays: dict[str, NDArray[np.generic]] = {}
    if engine == 'mlx':
        shape = (6,) if trials == 1 else (trials, 6)
        for name in ('pre_v', 'pre_g', 'before_v', 'before_g', 'end_v', 'end_g'):
            arrays[name] = np.full(shape, -52, dtype=np.float32)
        for name in (
            'pre_not_refractory',
            'spikes',
            'before_not_refractory',
            'end_not_refractory',
        ):
            arrays[name] = np.zeros(shape, dtype=np.bool_)
        arrays['end_last_spike_step'] = np.zeros(shape, dtype=np.int32)
        arrays['accepted_inputs'] = np.zeros(
            (2,) if trials == 1 else (trials, 2), dtype=np.bool_
        )
        arrays['queue'] = np.zeros((19, trials, 3), dtype=np.bool_)
    else:
        for name in ('g', 'spikes', 'v', 'refrac'):
            arrays[name] = np.zeros((trials, 6), dtype=np.float32)
        arrays['delay_buffer'] = np.zeros((trials, 19, 6), dtype=np.float32)
    arrays['spike_steps'] = np.empty(0, dtype=np.int64)
    arrays['spike_neurons'] = np.empty(0, dtype=np.int64)
    if engine == 'cpu' or trials == 4:
        arrays['spike_trials'] = np.empty(0, dtype=np.int64)
    return arrays


@pytest.mark.parametrize('engine', ('mlx', 'cpu'))
@pytest.mark.parametrize('trials', (1, 4))
def test_complete_native_final_geometry_is_required(
    engine: Engine, trials: int
) -> None:
    require_fields(native(engine, trials), engine, trials, 6, 3, 2)


@pytest.mark.parametrize(
    'fault', ('missing', 'extra', 'precision', 'slots', 'finite', 'coordinates')
)
@pytest.mark.parametrize('engine', ('mlx', 'cpu'))
def test_incomplete_native_final_evidence_cannot_pass(
    engine: Engine, fault: str
) -> None:
    arrays = native(engine, 4)
    state = 'end_v' if engine == 'mlx' else 'v'
    queue = 'queue' if engine == 'mlx' else 'delay_buffer'
    if fault == 'missing':
        del arrays[state]
    elif fault == 'extra':
        arrays['unknown'] = np.zeros(1, dtype=np.float32)
    elif fault == 'precision':
        arrays[state] = arrays[state].astype(np.float64)
    elif fault == 'slots':
        arrays[queue] = arrays[queue][:18] if engine == 'mlx' else arrays[queue][:, :18]
    elif fault == 'finite':
        arrays[state].flat[0] = np.nan
    else:
        arrays['spike_trials'] = np.zeros(1, dtype=np.int64)
    with pytest.raises(ValueError):
        require_fields(arrays, engine, 4, 6, 3, 2)


def test_identical_neuron_steps_in_different_trials_keep_their_own_identity() -> None:
    arrays = native('mlx', 4)
    arrays['spike_trials'] = np.array([3, 1, 0, 2], dtype=np.int64)
    arrays['spike_neurons'] = np.array([2, 2, 2, 2], dtype=np.int64)
    arrays['spike_steps'] = np.array([4, 4, 4, 4], dtype=np.int64)
    result = trial_spikes(arrays, 4, 6, 35)
    assert [(row.neurons.tolist(), row.steps.tolist()) for row in result] == [
        ([2], [4])
    ] * 4
    assert trial_spikes(native('mlx', 1), 1, 6, 35)[0].steps.size == 0


@pytest.mark.parametrize(
    'fault', ('neuron', 'step', 'trial', 'duplicate', 'cast', 'missing', 'shape')
)
def test_invalid_batch_spikes_cannot_hide_behind_equal_pooled_counts(
    fault: str,
) -> None:
    arrays = native('mlx', 4)
    arrays.update(
        {
            name: np.array([0], dtype=np.int64)
            for name in ('spike_trials', 'spike_neurons', 'spike_steps')
        }
    )
    if fault == 'neuron':
        arrays['spike_neurons'][0] = 6
    elif fault == 'step':
        arrays['spike_steps'][0] = 35
    elif fault == 'trial':
        arrays['spike_trials'][0] = 4
    elif fault == 'duplicate':
        arrays = {
            name: np.repeat(value, 2) if name.startswith('spike_') else value
            for name, value in arrays.items()
        }
    elif fault == 'cast':
        arrays['spike_steps'] = arrays['spike_steps'].astype(np.int32)
    elif fault == 'missing':
        del arrays['spike_trials']
    else:
        arrays['spike_neurons'] = np.zeros((1, 1), dtype=np.int64)
    with pytest.raises(ValueError):
        trial_spikes(arrays, 4, 6, 35)


@pytest.mark.parametrize('engine', ('mlx', 'cpu'))
def test_final_native_comparison_separates_exact_spikes_from_unresolved_floats(
    engine: Engine,
) -> None:
    batch, singleton = native(engine, 4), native(engine, 1)
    for trial in range(4):
        assert compare_final_trial(batch, singleton, engine, trial, 6, 3, 2, 35) == ()
    state = 'end_v' if engine == 'mlx' else 'v'
    batch[state][3, 2] += np.float32(0.0001)
    assert compare_final_trial(batch, singleton, engine, 3, 6, 3, 2, 35) == (state,)
    assert compare_final_trial(batch, singleton, engine, 2, 6, 3, 2, 35) == ()
    batch['spike_trials'] = np.array([3], dtype=np.int64)
    batch['spike_neurons'] = np.array([2], dtype=np.int64)
    batch['spike_steps'] = np.array([4], dtype=np.int64)
    with pytest.raises(ValueError, match='spike raster differs'):
        compare_final_trial(batch, singleton, engine, 3, 6, 3, 2, 35)


@pytest.mark.parametrize(
    'field', ('queue', 'end_last_spike_step', 'accepted_inputs', 'refrac')
)
def test_same_engine_discrete_final_differences_cannot_use_a_tolerance(
    field: str,
) -> None:
    engine: Engine = 'cpu' if field == 'refrac' else 'mlx'
    batch, singleton = native(engine, 4), native(engine, 1)
    batch[field].flat[-1] = 1
    with pytest.raises(ValueError, match='discrete batch state differs'):
        compare_final_trial(batch, singleton, engine, 3, 6, 3, 2, 35)


def test_cpu_payload_queue_difference_is_unresolved_and_preserves_all_slots() -> None:
    batch, singleton = native('cpu', 4), native('cpu', 1)
    batch['delay_buffer'][3, 18, 5] = np.float32(-0.0)
    assert compare_final_trial(batch, singleton, 'cpu', 3, 6, 3, 2, 35) == (
        'delay_buffer',
    )
