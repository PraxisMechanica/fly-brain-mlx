from pathlib import Path

import numpy as np
import pytest

from fly_brain.comparison.models import Spikes
from fly_brain.simulation.identifiers import (
    FlyWireIds64,
    NeuronRows64,
    TrialIds16,
    TrialIds64,
)
from fly_brain.simulation.models import SpikeEvents
from tests.quality.support import PROJECT
from tests.unit.test_identifier_type_contracts import typed
from tools.code_quality.json_values import object_value

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('readonly', (False, True))
@pytest.mark.parametrize('empty', (False, True))
def test_event_and_file_contracts_preserve_exact_borrowed_array_values(
    readonly: bool, empty: bool
) -> None:
    raw64 = np.arange(12, dtype=np.int64)[::2]
    raw16 = np.arange(12, dtype=np.int16)[::2]
    times = np.arange(12, dtype=np.float64)[::2]
    if empty:
        raw64, raw16, times = raw64[:0], raw16[:0], times[:0]
    for value in (raw64, raw16, times):
        value.setflags(write=not readonly)
    originals = (raw64, raw64, raw64, raw16, raw64, times)
    before = tuple(
        (
            True,
            type(value),
            value.dtype.str,
            value.shape,
            value.strides,
            value.tobytes(),
            value.flags.writeable,
        )
        for value in originals
    )
    events = SpikeEvents(TrialIds64(raw64), NeuronRows64(raw64), raw64)
    spikes = Spikes(TrialIds16(raw16), FlyWireIds64(raw64), times)
    arrays = (
        events.trials,
        events.neurons,
        events.steps,
        spikes.trials,
        spikes.neuron_ids,
        spikes.time_s,
    )
    assert (
        tuple(
            (
                value is original,
                type(value),
                value.dtype.str,
                value.shape,
                value.strides,
                value.tobytes(),
                value.flags.writeable,
            )
            for value, original in zip(arrays, originals, strict=True)
        )
        == before
    )


@pytest.mark.checker
@pytest.mark.parametrize(
    'record,bad,good',
    (
        (
            'Events',
            'Events(events.neurons, events.neurons, events.steps)',
            'Events(events.trials, events.neurons, events.steps)',
        ),
        (
            'Events',
            'Events(raw64, events.neurons, events.steps)',
            'Events(events.trials, events.neurons, events.steps)',
        ),
        (
            'Events',
            'Events(events.trials, events.trials, events.steps)',
            'Events(events.trials, events.neurons, events.steps)',
        ),
        (
            'Events',
            'Events(events.trials, raw64, events.steps)',
            'Events(events.trials, events.neurons, events.steps)',
        ),
        (
            'Series',
            'Series(events.trials, series.neuron_ids, series.time_s)',
            'Series(series.trials, series.neuron_ids, series.time_s)',
        ),
        (
            'Series',
            'Series(raw16, series.neuron_ids, series.time_s)',
            'Series(series.trials, series.neuron_ids, series.time_s)',
        ),
        (
            'Series',
            'Series(series.trials, events.neurons, series.time_s)',
            'Series(series.trials, series.neuron_ids, series.time_s)',
        ),
        (
            'Series',
            'Series(series.trials, raw64, series.time_s)',
            'Series(series.trials, series.neuron_ids, series.time_s)',
        ),
    ),
)
def test_actual_record_forwarding_rejects_wrong_spaces_and_raw_arrays(
    tmp_path: Path, record: str, bad: str, good: str
) -> None:
    source = (
        'import numpy as np\n'
        'from numpy.typing import NDArray\n'
        'from fly_brain.simulation.models import SpikeEvents as Events\n'
        'from fly_brain.comparison.models import Spikes as Series\n'
        'def forward(events: Events, series: Series, '
        'raw64: NDArray[np.int64], raw16: NDArray[np.int16])'
        f' -> {record}:\n    return {bad}\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    start = object_value(object_value(diagnostic['range'])['start'])
    assert (len(found), diagnostic['rule'], diagnostic['file'], start['line']) == (
        1,
        'reportArgumentType',
        str(tmp_path / 'consumer.py'),
        5,
    )
    assert typed(tmp_path, source.replace(bad, good)) == []


@pytest.mark.checker
def test_erasing_actual_event_trial_brand_loses_same_dtype_space_rejection(
    tmp_path: Path,
) -> None:
    original = (PROJECT / 'src/fly_brain/simulation/models.py').read_text()
    native = original.replace(
        'from .identifiers import (', 'from fly_brain.simulation.identifiers import ('
    )
    path = tmp_path / 'local_models.py'
    path.write_text(native)
    source = (
        'from local_models import SpikeEvents as Events\n'
        'def forward(events: Events) -> Events:\n'
        '    return Events(events.neurons, events.neurons, events.steps)\n'
    )
    found = typed(tmp_path, source)
    assert len(found) == 1
    assert object_value(found[0])['rule'] == 'reportArgumentType'
    assert native.count('    trials: TrialIds64\n') == 1
    path.write_text(
        native.replace(
            '    trials: TrialIds64\n', '    trials: NDArray[np.int64]\n'
        ).replace('    TrialIds64,\n', '')
    )
    assert typed(tmp_path, source) == []
