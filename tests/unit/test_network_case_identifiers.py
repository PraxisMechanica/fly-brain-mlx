import json
from dataclasses import fields
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.models import NetworkCase
from tests.quality.support import PROJECT
from tests.unit.test_identifier_type_contracts import typed
from tools.architecture.compiler import JsonValue, object_value

pytestmark = pytest.mark.unit


def consumer(space: str, module: str = 'fly_brain.simulation.models') -> str:
    return (
        f'from {module} import NetworkCase\n'
        'from fly_brain.simulation import identifiers as ids\n'
        f'def forward(wrong: {space}, row: ids.NeuronRow) -> None:\n'
        '    NetworkCase(3001, sources=(wrong,))\n'
        '    NetworkCase(3001, destinations=(wrong,))\n'
        '    NetworkCase(3001, targets=(wrong,))\n'
        '    NetworkCase(3001, silenced=(wrong,))\n'
    )


def location(entry: JsonValue) -> tuple[JsonValue, JsonValue, JsonValue]:
    value = object_value(entry)
    start = object_value(object_value(value['range'])['start'])
    return value['rule'], value['file'], start['line']


def state(
    value: NDArray[np.generic],
) -> tuple[np.dtype[np.generic], tuple[int, ...], tuple[int, ...], bool, bytes]:
    return (
        value.dtype,
        value.shape,
        value.strides,
        value.flags.writeable,
        value.tobytes(),
    )


@pytest.mark.checker
@pytest.mark.parametrize('space', ('int', 'ids.FlyWireNeuronId', 'ids.TrialId'))
def test_each_actual_selector_rejects_plain_flywire_and_trial_tuples(
    tmp_path: Path, space: str
) -> None:
    assert tuple(map(location, typed(tmp_path, consumer(space)))) == tuple(
        zip(
            ('reportArgumentType',) * 4,
            (str(tmp_path / 'consumer.py'),) * 4,
            range(3, 7),
            strict=True,
        )
    )


@pytest.mark.checker
def test_neuron_rows_repair_all_four_constructor_fields(tmp_path: Path) -> None:
    assert typed(tmp_path, consumer('ids.NeuronRow')) == []


@pytest.mark.checker
@pytest.mark.parametrize(
    'field,line',
    (('sources', 3), ('destinations', 4), ('targets', 5), ('silenced', 6)),
)
def test_erasing_one_selector_loses_only_its_plain_tuple_rejection(
    tmp_path: Path, field: str, line: int
) -> None:
    original = (PROJECT / 'src/fly_brain/simulation/models.py').read_text()
    local = original.replace(
        'from .identifiers import', 'from fly_brain.simulation.identifiers import'
    )
    path = tmp_path / 'local_models.py'
    path.write_text(local)
    source = consumer('int', 'local_models')
    strong = tuple(map(location, typed(tmp_path, source)))
    prefix, body = local.split('class NetworkCase:', 1)
    case, suffix = body.split('\n\n@dataclass(frozen=True)\nclass InputPin:', 1)
    annotation = f'{field}: tuple[NeuronRow, ...]'
    weakened_case = case.replace(annotation, f'{field}: tuple[int, ...]')
    weakened = (
        prefix
        + 'class NetworkCase:'
        + weakened_case
        + '\n\n@dataclass(frozen=True)\nclass InputPin:'
        + suffix
    )
    path.write_text(weakened)
    assert (
        case.count('tuple[NeuronRow, ...]'),
        case.count(annotation),
        weakened_case.count('tuple[NeuronRow, ...]'),
        weakened != local,
        strong,
        tuple(map(location, typed(tmp_path, source))),
    ) == (
        4,
        1,
        3,
        True,
        tuple(
            zip(
                ('reportArgumentType',) * 4,
                (str(tmp_path / 'consumer.py'),) * 4,
                range(3, 7),
                strict=True,
            )
        ),
        tuple(
            ('reportArgumentType', str(tmp_path / 'consumer.py'), index)
            for index in range(3, 7)
            if index != line
        ),
    )


@pytest.mark.parametrize('empty', (False, True))
@pytest.mark.parametrize('readonly', (False, True))
def test_case_keeps_passed_objects_defaults_order_and_exact_host_projections(
    empty: bool, readonly: bool
) -> None:
    raw = int('3000')
    row = NeuronRow(raw)
    rows = () if empty else (NeuronRow(0), row, NeuronRow(0))
    raw_rows = () if empty else (0, raw, 0)
    weights = (0.275, 0.0, -0.275)
    voltage = np.full(6002, -52, dtype=np.float64)[::2]
    synaptic = np.zeros(6002, dtype=np.float64)[::2]
    last = np.full(6002, -100000000, dtype=np.int64)[::2]
    arrays = (voltage, synaptic, last)
    for value in arrays:
        value.setflags(write=not readonly)
    before = tuple(map(state, arrays))
    case = NetworkCase(3001, rows, rows, weights, rows, rows, voltage, synaptic, last)
    selectors = (case.sources, case.destinations, case.targets, case.silenced)
    default = NetworkCase(1)
    assert (
        row is raw,
        type(row),
        tuple(map(id, selectors)),
        case.weights is weights,
        case.voltage is voltage,
        case.synaptic is synaptic,
        case.last_spike is last,
        tuple(map(state, arrays)),
        tuple(state(np.asarray(value)) for value in selectors),
        tuple(state(np.asarray(value, dtype=np.int32)) for value in selectors),
        (default.sources, default.destinations, default.targets, default.silenced),
        (default.neurons, default.voltage, default.synaptic, default.last_spike),
        tuple(field.name for field in fields(case)),
        json.dumps(selectors),
    ) == (
        True,
        int,
        (id(rows),) * 4,
        True,
        True,
        True,
        True,
        before,
        (state(np.asarray(raw_rows)),) * 4,
        (state(np.asarray(raw_rows, dtype=np.int32)),) * 4,
        ((),) * 4,
        (1, -52, 0, -100000000),
        (
            'neurons',
            'sources',
            'destinations',
            'weights',
            'targets',
            'silenced',
            'voltage',
            'synaptic',
            'last_spike',
        ),
        json.dumps((raw_rows,) * 4),
    )
