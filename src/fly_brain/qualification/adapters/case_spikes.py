from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from fly_brain.comparison.models import FlyWireSpikeSteps, SpikeSteps
from fly_brain.qualification.spike_comparison_ports import (
    CoordinateValidator,
    ReferenceClockConverter,
)
from fly_brain.simulation.identifiers import FlyWireIds64, NeuronRows64
from fly_brain.simulation.models import Connectome

from .observer_evidence import array_record


def load(
    connectome: Connectome,
    steps: int,
    paired: Path,
    cpu: Path,
    *,
    validate: CoordinateValidator,
    convert_clock: ReferenceClockConverter,
) -> tuple[dict[str, FlyWireSpikeSteps], dict[str, object]]:
    spikes: dict[str, FlyWireSpikeSteps] = {}
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
                coordinates = convert_clock(times, steps)
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
            validate(
                SpikeSteps(NeuronRows64(indices), coordinates),
                len(connectome.neuron_ids),
                steps,
            )
            spikes[engine] = SpikeSteps(
                FlyWireIds64(connectome.neuron_ids[indices]), coordinates
            )
    return spikes, native
