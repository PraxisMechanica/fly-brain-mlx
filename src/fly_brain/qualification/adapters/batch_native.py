from collections.abc import Mapping
from typing import Literal

import numpy as np
from numpy.typing import NDArray

NativeArrays = Mapping[str, NDArray[np.generic]]
Engine = Literal['mlx', 'cpu']


def require_fields(
    arrays: NativeArrays,
    engine: Engine,
    trials: int,
    neurons: int,
    edges: int,
    channels: int,
) -> None:
    if trials not in (1, 4) or neurons < 1 or edges < 0 or channels < 0:
        raise ValueError('Native evidence requires valid trial/network dimensions')
    specifications: dict[str, tuple[str, tuple[int, ...]]] = {}
    if engine == 'mlx':
        shape = (neurons,) if trials == 1 else (trials, neurons)
        inputs = (channels,) if trials == 1 else (trials, channels)
        for name in ('pre_v', 'pre_g', 'before_v', 'before_g', 'end_v', 'end_g'):
            specifications[name] = ('float32', shape)
        for name in (
            'pre_not_refractory',
            'spikes',
            'before_not_refractory',
            'end_not_refractory',
        ):
            specifications[name] = ('bool', shape)
        specifications['end_last_spike_step'] = ('int32', shape)
        specifications['accepted_inputs'] = ('bool', inputs)
        specifications['queue'] = ('bool', (19, trials, edges))
    else:
        for name in ('g', 'spikes', 'v', 'refrac'):
            specifications[name] = ('float32', (trials, neurons))
        specifications['delay_buffer'] = ('float32', (trials, 19, neurons))
    coordinates = ('spike_steps', 'spike_neurons') + (
        ('spike_trials',) if engine == 'cpu' or trials == 4 else ()
    )
    if set(arrays) != set(specifications) | set(coordinates):
        raise ValueError('Native evidence requires every expected field exactly')
    for name in coordinates:
        specifications[name] = ('int64', (arrays['spike_steps'].size,))
    for name, (dtype, shape) in specifications.items():
        value = arrays[name]
        if value.dtype != np.dtype(dtype) or value.shape != shape:
            raise ValueError(f'Native field has wrong precision or dimensions: {name}')
        if not np.isfinite(value).all():
            raise ValueError(f'Native field contains nonfinite values: {name}')
