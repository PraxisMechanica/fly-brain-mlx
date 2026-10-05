from collections.abc import Mapping
from typing import Literal, cast

import numpy as np
from numpy.typing import NDArray

from fly_brain.comparison.acceptance import validate_coordinates
from fly_brain.comparison.models import SpikeSteps

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


def trial_spikes(
    arrays: NativeArrays, trials: int, neurons: int, steps: int
) -> tuple[SpikeSteps, ...]:
    if steps < 1 or neurons < 1 or trials not in (1, 4):
        raise ValueError('Spike evidence requires valid trial/network dimensions')
    indices, times = arrays['spike_neurons'], arrays['spike_steps']
    positions = arrays.get('spike_trials')
    if positions is None:
        if trials != 1:
            raise ValueError('Batch spike evidence requires actual trial coordinates')
        positions = np.zeros(times.size, dtype=np.int64)
    positions = cast(NDArray[np.int64], positions)
    if (
        positions.dtype != np.int64
        or positions.ndim != 1
        or indices.ndim != 1
        or times.ndim != 1
        or positions.shape != times.shape
        or indices.shape != times.shape
        or np.any(positions < 0)
        or np.any(positions >= trials)
    ):
        raise ValueError('Spike trial coordinates must be aligned native int64')
    result: list[SpikeSteps] = []
    for trial in range(trials):
        selected = positions == trial
        spikes = SpikeSteps(
            cast(NDArray[np.int64], indices[selected]),
            cast(NDArray[np.int64], times[selected]),
        )
        validate_coordinates(spikes, neurons, steps)
        order = np.lexsort((spikes.neurons, spikes.steps))
        result.append(SpikeSteps(spikes.neurons[order], spikes.steps[order]))
    return tuple(result)


def compare_final_trial(
    batch: NativeArrays,
    singleton: NativeArrays,
    engine: Engine,
    trial: int,
    neurons: int,
    edges: int,
    channels: int,
    steps: int,
) -> tuple[str, ...]:
    if not 0 <= trial < 4:
        raise ValueError('Final comparison requires an actual batch trial')
    require_fields(batch, engine, 4, neurons, edges, channels)
    require_fields(singleton, engine, 1, neurons, edges, channels)
    many = trial_spikes(batch, 4, neurons, steps)[trial]
    one = trial_spikes(singleton, 1, neurons, steps)[0]
    if (many.neurons.tobytes(), many.steps.tobytes()) != (
        one.neurons.tobytes(),
        one.steps.tobytes(),
    ):
        raise ValueError(f'Same-engine batch spike raster differs: trial {trial}')
    differences: list[str] = []
    for name, expected in singleton.items():
        if name.startswith('spike_'):
            continue
        if engine == 'mlx' and name == 'queue':
            actual, expected = batch[name][:, trial], expected[:, 0]
        elif engine == 'mlx':
            actual = batch[name][trial]
        else:
            actual, expected = batch[name][trial], expected[0]
        if actual.tobytes() == expected.tobytes():
            continue
        if actual.dtype.kind in 'biu' or name in ('spikes', 'refrac'):
            raise ValueError(
                f'Same-engine discrete batch state differs: {trial}/{name}'
            )
        differences.append(name)
    return tuple(sorted(differences))
