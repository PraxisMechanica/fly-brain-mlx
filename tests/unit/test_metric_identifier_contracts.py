from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.comparison.metrics import prepare_metrics
from fly_brain.comparison.models import Metrics, Spikes
from fly_brain.simulation.identifiers import (
    FlyWireIds64,
    FlyWireNeuronId,
    TrialId,
    TrialIds16,
)
from tests.quality.support import PROJECT
from tests.unit.test_identifier_type_contracts import typed
from tools.architecture.compiler import object_value

pytestmark = pytest.mark.unit


def array_state(
    value: NDArray[np.int16] | NDArray[np.int64] | NDArray[np.float64],
) -> tuple[
    np.dtype[np.int16] | np.dtype[np.int64] | np.dtype[np.float64],
    tuple[int, ...],
    tuple[int, ...],
    bool,
    bytes,
]:
    return (
        value.dtype,
        value.shape,
        value.strides,
        value.flags.writeable,
        value.tobytes(),
    )


@pytest.mark.parametrize('readonly', (False, True))
def test_metrics_keep_requested_labels_exact_ids_order_and_borrowed_inputs(
    readonly: bool,
) -> None:
    large = 300000000000000001
    neurons = np.repeat(np.array([large, large, 2, 2, 3, 2], dtype=np.int64), 2)[::2]
    trials = np.repeat(np.array([4, 2, 4, 2, 2, 4], dtype=np.int16), 2)[::2]
    times = np.repeat(np.array([0.004, 0.003, 0.002, 0.001, 0.0, 0.002]), 2)[::2]
    arrays = (neurons, trials, times)
    for value in arrays:
        value.setflags(write=not readonly)
    before = tuple(map(array_state, arrays))
    spikes = Spikes(TrialIds16(trials), FlyWireIds64(neurons), times)
    result = prepare_metrics(spikes, 2.0, 2)
    expected = ([0.004], [0.003], [0.002, 0.002], [0.001], [0.0])
    assert (
        result.rates,
        result.active,
        result.spikes,
        list(result.groups),
        tuple(
            (value.dtype, value.shape, value.tobytes())
            for value in result.groups.values()
        ),
    ) == (
        {2: 0.75, 3: 0.25, large: 0.5},
        {2, 3, large},
        6,
        [(4, large), (2, large), (4, 2), (2, 2), (2, 3)],
        tuple(
            (np.dtype(np.float64), (len(value),), np.array(value).tobytes())
            for value in expected
        ),
    )
    assert (
        spikes.neuron_ids is neurons,
        spikes.trials is trials,
        spikes.time_s is times,
        tuple(map(array_state, arrays)),
    ) == (
        True,
        True,
        True,
        before,
    )


def test_metrics_preserve_owned_scalar_and_container_identity() -> None:
    raw = int('300000000000000001')
    label = int('4000')
    neuron = FlyWireNeuronId(raw)
    trial = TrialId(label)
    key = (trial, neuron)
    times = np.array([0.001, 0.002])
    rates = {neuron: 1.0}
    active = {neuron}
    groups = {key: times}
    result = Metrics(rates, active, groups, 2)
    assert (
        neuron is raw,
        trial is label,
        result.rates is rates,
        result.active is active,
        result.groups is groups,
        next(iter(result.rates)) is neuron,
        next(iter(result.active)) is neuron,
        next(iter(result.groups)) is key,
        result.groups[key] is times,
    ) == (True,) * 9


@pytest.mark.checker
@pytest.mark.parametrize(
    'bad,good',
    (
        ('{raw: 0.5}', '{identity: 0.5}'),
        ('{row: 0.5}', '{identity: 0.5}'),
        ('{trial: 0.5}', '{identity: 0.5}'),
        ('{raw}', '{identity}'),
        ('{row}', '{identity}'),
        ('{(raw, identity): times}', '{(trial, identity): times}'),
        ('{(row, identity): times}', '{(trial, identity): times}'),
        ('{(trial, raw): times}', '{(trial, identity): times}'),
        ('{(trial, row): times}', '{(trial, identity): times}'),
        ('{(identity, trial): times}', '{(trial, identity): times}'),
    ),
)
def test_actual_metrics_constructor_rejects_plain_foreign_and_swapped_keys(
    tmp_path: Path, bad: str, good: str
) -> None:
    call = 'Metrics({identity: 0.5}, {identity}, {(trial, identity): times}, 1)'
    source = (
        'import numpy as np\n'
        'from numpy.typing import NDArray\n'
        'from fly_brain.comparison.models import Metrics\n'
        'from fly_brain.simulation.identifiers import '
        'FlyWireNeuronId as Id, TrialId as Trial, NeuronRow as Row\n'
        'def forward(identity: Id, trial: Trial, row: Row, raw: int, '
        'times: NDArray[np.float64]) -> Metrics:\n'
        f'    return {call.replace(good, bad)}\n'
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
def test_erasing_metrics_key_contracts_loses_actual_foreign_space_rejection(
    tmp_path: Path,
) -> None:
    original = (PROJECT / 'src/fly_brain/comparison/models.py').read_text()
    path = tmp_path / 'local_models.py'
    path.write_text(original)
    source = (
        'import numpy as np\n'
        'from numpy.typing import NDArray\n'
        'from local_models import Metrics\n'
        'from fly_brain.simulation.identifiers import NeuronRow as Row, TrialId as Trial\n'
        'def forward(row: Row, trial: Trial, times: NDArray[np.float64]) -> Metrics:\n'
        '    return Metrics({row: 0.5}, {row}, {(trial, row): times}, 1)\n'
    )
    found = typed(tmp_path, source)
    assert len(found) == 3
    assert (
        tuple(object_value(value)['rule'] for value in found)
        == ('reportArgumentType',) * 3
    )
    weakened = (
        original.replace('dict[FlyWireNeuronId, float]', 'dict[int, float]')
        .replace('set[FlyWireNeuronId]', 'set[int]')
        .replace('tuple[TrialId, FlyWireNeuronId]', 'tuple[int, int]')
        .replace('    FlyWireNeuronId,\n', '')
        .replace('    TrialId,\n', '')
    )
    assert weakened != original
    path.write_text(weakened)
    assert typed(tmp_path, source) == []
