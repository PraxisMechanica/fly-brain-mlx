import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.batch_native import Engine, require_fields

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
