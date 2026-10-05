from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.case_spikes import load
from fly_brain.qualification.adapters.observer_evidence import array_record
from fly_brain.simulation.models import Connectome

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault',
    (
        'none',
        'reference-dtype',
        'clock',
        'bounds',
        'mlx-dtype',
        'trial',
        'trial-shape',
        'duplicate',
    ),
)
def test_native_coordinates_are_validated_before_pinned_identifier_mapping(
    tmp_path: Path, fault: str
) -> None:
    connectome = Connectome(
        np.array([17, 23, 42], dtype=np.int64),
        np.empty(0, dtype=np.int32),
        np.empty(0, dtype=np.int32),
        np.empty(0, dtype=np.int32),
        np.empty(0, dtype=np.float64),
    )
    paired, cpu = tmp_path / 'paired', tmp_path / 'cpu'
    paired.mkdir()
    cpu.mkdir()
    reference: dict[str, NDArray[np.generic]] = {
        'spike_i': np.array([1], dtype=np.int32),
        'spike_t': np.array([0.0001], dtype=np.float64),
    }
    mlx: dict[str, NDArray[np.generic]] = {
        'spike_neurons': np.array([1], dtype=np.int64),
        'spike_steps': np.array([1], dtype=np.int64),
    }
    torch = {**mlx, 'spike_trials': np.array([0], dtype=np.int64)}
    if fault == 'reference-dtype':
        reference['spike_i'] = reference['spike_i'].astype(np.float64)
    if fault == 'clock':
        reference['spike_t'] = np.array([0.00015], dtype=np.float64)
    if fault == 'bounds':
        mlx['spike_neurons'] = np.array([3], dtype=np.int64)
    if fault == 'mlx-dtype':
        mlx['spike_steps'] = mlx['spike_steps'].astype(np.int32)
    if fault == 'trial':
        torch['spike_trials'] = np.array([1], dtype=np.int64)
    if fault == 'trial-shape':
        torch['spike_trials'] = np.empty(0, dtype=np.int64)
    if fault == 'duplicate':
        mlx = {name: np.repeat(value, 2) for name, value in mlx.items()}
    for path, arrays in (
        (paired / 'reference-native.npz', reference),
        (paired / 'mlx-native.npz', mlx),
        (cpu / 'native.npz', torch),
    ):
        with path.open('xb') as archive:
            np.savez_compressed(archive, **arrays)
    if fault != 'none':
        with pytest.raises(ValueError):
            load(connectome, 3, paired, cpu)
        return
    spikes, native = load(connectome, 3, paired, cpu)
    assert all(
        value.neurons.tolist() == [23] and value.steps.tolist() == [1]
        for value in spikes.values()
    )
    for engine, path, arrays in (
        ('brian', paired / 'reference-native.npz', reference),
        ('mlx', paired / 'mlx-native.npz', mlx),
        ('torch', cpu / 'native.npz', torch),
    ):
        assert native[engine] == {
            'file': str(path),
            'arrays': {name: array_record(value) for name, value in arrays.items()},
        }
