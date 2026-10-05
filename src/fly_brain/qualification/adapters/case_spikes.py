from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from fly_brain.comparison.acceptance import (
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.comparison.models import SpikeSteps
from fly_brain.simulation.models import Connectome

from .observer_evidence import array_record


def load(
    connectome: Connectome, steps: int, paired: Path, cpu: Path
) -> tuple[dict[str, SpikeSteps], dict[str, object]]:
    spikes: dict[str, SpikeSteps] = {}
    native: dict[str, object] = {}
    paths = (
        ('brian', paired / 'reference-native.npz'),
        ('mlx', paired / 'mlx-native.npz'),
        ('torch', cpu / 'native.npz'),
    )
    for engine, path in paths:
        with np.load(path, allow_pickle=False) as archive:
            names = (
                ('spike_i', 'spike_t')
                if engine == 'brian'
                else ('spike_neurons', 'spike_steps')
            )
            neurons, times = (archive[name] for name in names)
            native[engine] = {
                'file': str(path),
                'arrays': {name: array_record(archive[name]) for name in names},
            }
            if engine == 'brian':
                if neurons.dtype != np.int32:
                    raise ValueError('Reference spike neurons must retain native int32')
                indices = neurons.astype(np.int64)
                coordinates = steps_from_reference_clock(times, steps)
            else:
                indices = cast(NDArray[np.int64], neurons)
                coordinates = cast(NDArray[np.int64], times)
            if engine == 'torch':
                trials = archive['spike_trials']
                if (
                    trials.dtype != np.int64
                    or trials.shape != indices.shape
                    or np.any(trials != 0)
                ):
                    raise ValueError(
                        'Each CPU case requires aligned single-trial int64 coordinates'
                    )
                native[engine] = {
                    'file': str(path),
                    'arrays': {
                        name: array_record(archive[name])
                        for name in (*names, 'spike_trials')
                    },
                }
            validate_coordinates(
                SpikeSteps(indices, coordinates), len(connectome.neuron_ids), steps
            )
            spikes[engine] = SpikeSteps(connectome.neuron_ids[indices], coordinates)
    return spikes, native
