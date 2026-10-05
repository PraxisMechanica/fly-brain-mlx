from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .brian_jobs import BrianJob, ResultArrays
from .brian_reference import default_parameters
from .observer_stream import FinalSnapshot


def verify(
    job: BrianJob,
    directory: Path,
    final: FinalSnapshot,
    native: ResultArrays,
    spike_neurons: list[int],
    spike_times: list[float],
    edges: int,
    expected_weights: NDArray[np.float64] | None = None,
) -> None:
    expected = {
        **final.fields,
        'spike_i': np.asarray(spike_neurons, dtype=np.int32),
        'spike_t': np.asarray(spike_times, dtype=np.float64),
        'clock_step': np.asarray([final.step.clock_step], dtype=np.int64),
        'clock_t': np.asarray([final.step.time_s], dtype=np.float64),
    }
    if 'source_cursor' in job.files:
        expected['source_cursor'] = np.asarray(
            [final.step.source_cursor], dtype=np.int32
        )
    if set(native) != set(expected):
        raise ValueError('Reference native fields differ from the complete tape')
    for name, value in expected.items():
        actual = native[name]
        if (actual.dtype, actual.shape, actual.tobytes()) != (
            value.dtype,
            value.shape,
            value.tobytes(),
        ):
            raise ValueError(f'Reference native output differs from tape: {name}')
    if edges:
        weights = np.fromfile(directory / job.files['weights'], dtype=np.float64)
        if weights.shape != (edges,) or not np.isfinite(weights).all():
            raise ValueError('Reference native weights are incomplete or nonfinite')
        if (
            expected_weights is not None
            and weights.tobytes() != expected_weights.tobytes()
        ):
            raise ValueError('Reference native weights differ from original inputs')


def weights(
    counts: NDArray[np.int32], silenced_sources: NDArray[np.bool_]
) -> NDArray[np.float64]:
    values = counts.astype(np.float64) * float(default_parameters()['w_syn'])
    values[silenced_sources] = 0
    return values
