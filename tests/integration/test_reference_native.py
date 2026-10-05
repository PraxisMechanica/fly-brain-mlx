from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters.brian_jobs import BrianJob, ResultArrays
from fly_brain.qualification.adapters.observer_stream import (
    FinalSnapshot,
    ObservationArray,
    StepSnapshot,
    StreamShape,
)
from fly_brain.qualification.adapters.reference_native import verify, weights

pytestmark = pytest.mark.integration


@pytest.fixture
def native(tmp_path: Path) -> tuple[BrianJob, FinalSnapshot, ResultArrays]:
    fields: dict[str, ObservationArray] = {
        name: np.asarray([1, 2], dtype=np.float64) for name in ('v', 'g', 'lastspike')
    }
    fields['not_refractory'] = np.asarray([True, False])
    final = FinalSnapshot(
        StepSnapshot(
            2, 2, 0.0002, 1, np.asarray([0], dtype=np.int32), np.empty(0, np.int32), ()
        ),
        fields,
    )
    result: ResultArrays = {
        **fields,
        'spike_i': np.asarray([1, 0], dtype=np.int32),
        'spike_t': np.asarray([0, 0.0001], dtype=np.float64),
        'clock_step': np.asarray([2], dtype=np.int64),
        'clock_t': np.asarray([0.0002], dtype=np.float64),
        'source_cursor': np.asarray([1], dtype=np.int32),
    }
    np.asarray([0.1, 0.2], dtype=np.float64).tofile(tmp_path / 'weights')
    return (
        BrianJob(
            tmp_path,
            StreamShape(2, 2, 1, (2, 1), 2),
            True,
            {'source_cursor': 'cursor', 'weights': 'weights'},
        ),
        final,
        result,
    )


@pytest.mark.parametrize(
    'field', ['spike_i', 'spike_t', 'clock_step', 'clock_t', 'source_cursor']
)
def test_repeated_native_disagreement_with_tape_fails(
    tmp_path: Path, native: tuple[BrianJob, FinalSnapshot, ResultArrays], field: str
) -> None:
    job, final, values = native
    changed = {name: value.copy() for name, value in values.items()}
    changed[field][0] += 1
    with pytest.raises(ValueError, match='differs from tape'):
        verify(job, tmp_path, final, changed, [1, 0], [0, 0.0001], 2)


@pytest.mark.parametrize('fault', ['dtype', 'shape', 'weight-size', 'weight-value'])
def test_native_geometry_precision_and_weights_are_required(
    tmp_path: Path, native: tuple[BrianJob, FinalSnapshot, ResultArrays], fault: str
) -> None:
    job, final, values = native
    if fault == 'dtype':
        values['clock_step'] = values['clock_step'].astype(np.float64)
    elif fault == 'shape':
        values['clock_step'] = np.asarray([2, 2], dtype=np.int64)
    elif fault == 'weight-size':
        np.asarray([0.1], dtype=np.float64).tofile(tmp_path / 'weights')
    else:
        np.asarray([0.1, np.nan], dtype=np.float64).tofile(tmp_path / 'weights')
    with pytest.raises(ValueError):
        verify(job, tmp_path, final, values, [1, 0], [0, 0.0001], 2)


def test_complete_tape_and_original_silenced_weights_pass(
    tmp_path: Path, native: tuple[BrianJob, FinalSnapshot, ResultArrays]
) -> None:
    job, final, values = native
    expected = weights(np.asarray([360, -1], dtype=np.int32), np.asarray([False, True]))
    expected.tofile(tmp_path / 'weights')
    verify(job, tmp_path, final, values, [1, 0], [0, 0.0001], 2, expected)
    assert expected.tobytes() == np.asarray([360 * (0.275 * 0.001), 0]).tobytes()
