from pathlib import Path

import numpy as np
import pytest
import torch
from numpy.typing import NDArray

from fly_brain.qualification.adapters.torch_observer import (
    TorchSnapshot,
    capture,
    observe,
)
from fly_brain.qualification.adapters.torch_setup import (
    native_float,
    prepare,
    replay_inputs,
)
from fly_brain.qualification.reference_parameters import model_parameters
from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.module import build_connectome_silencer
from tests.quality.support import PROJECT
from tests.support.observation_fixtures import fixture
from tests.unit.test_identifier_type_contracts import typed
from tools.architecture.compiler import JsonValue, object_value

pytestmark = pytest.mark.unit
SETUP = 'fly_brain.qualification.adapters.torch_setup'
OBSERVER = 'fly_brain.qualification.adapters.torch_observer'
ArrayState = tuple[np.dtype[np.generic], tuple[int, ...], tuple[int, ...], bool, bytes]


def consumer(space: str, setup: str = SETUP, observer: str = OBSERVER) -> str:
    return (
        f'import {setup} as setup\n'
        f'import {observer} as observer\n'
        'from fly_brain.simulation import identifiers as ids\n'
        'from fly_brain.simulation.models import Connectome\n'
        'from fly_brain.qualification.ports import ConnectomeSilencer\n'
        'from fly_brain.qualification.adapters.torch_reference import TorchModel\n'
        'import numpy as np\n'
        'from numpy.typing import NDArray\n'
        'def forward(connectome: Connectome, model: TorchModel, '
        'single: NDArray[np.uint8], batch: NDArray[np.uint8], '
        f'silence: ConnectomeSilencer, wrong: {space}, row: ids.NeuronRow) -> None:\n'
        '    setup.prepare(connectome, (wrong,), (), 1, reference_parameters={}, silence=silence)\n'
        '    setup.replay_inputs(single, (wrong,), 6)\n'
        '    observer.observe(model, batch, (wrong,))\n'
    )


def location(entry: JsonValue) -> tuple[JsonValue, JsonValue, JsonValue]:
    value = object_value(entry)
    start = object_value(object_value(value['range'])['start'])
    return value['rule'], value['file'], start['line']


def array_state(value: NDArray[np.generic]) -> ArrayState:
    return (
        value.dtype,
        value.shape,
        value.strides,
        value.flags.writeable,
        value.tobytes(),
    )


def record(
    snapshot: TorchSnapshot,
) -> tuple[int, tuple[str, ...], tuple[str, ...], tuple[ArrayState, ...]]:
    return (
        snapshot.step,
        tuple(snapshot.fields),
        snapshot.native_sha256,
        tuple(map(array_state, snapshot.fields.values())),
    )


@pytest.mark.parametrize('space', ('int', 'ids.FlyWireNeuronId', 'ids.TrialId'))
def test_each_torch_target_contract_rejects_plain_flywire_and_trial_rows(
    tmp_path: Path, space: str
) -> None:
    assert tuple(map(location, typed(tmp_path, consumer(space)))) == tuple(
        zip(
            ('reportArgumentType',) * 3,
            (str(tmp_path / 'consumer.py'),) * 3,
            range(9, 12),
            strict=True,
        )
    )


def test_owned_rows_repair_all_three_actual_calls(tmp_path: Path) -> None:
    assert typed(tmp_path, consumer('ids.NeuronRow')) == []


@pytest.mark.parametrize(
    'module,function,line,setup,observer',
    (
        ('torch_setup', 'prepare', 9, 'local_targets', OBSERVER),
        ('torch_setup', 'replay_inputs', 10, 'local_targets', OBSERVER),
        ('torch_observer', 'observe', 11, SETUP, 'local_targets'),
    ),
)
def test_erasing_one_annotation_loses_only_that_target_rejection(
    tmp_path: Path,
    module: str,
    function: str,
    line: int,
    setup: str,
    observer: str,
) -> None:
    original = (
        PROJECT / f'src/fly_brain/qualification/adapters/{module}.py'
    ).read_text()
    local = original.replace('from .', 'from fly_brain.qualification.adapters.')
    path = tmp_path / 'local_targets.py'
    path.write_text(local)
    source = consumer('int', setup, observer)
    strong = tuple(map(location, typed(tmp_path, source)))
    marker = 'def ' + function + '('
    prefix, fragment = local.split(marker, 1)
    signature, body = fragment.split(') ->', 1)
    annotation = 'targets: tuple[NeuronRow, ...]'
    weakened = (
        prefix
        + marker
        + signature.replace(annotation, 'targets: tuple[int, ...]')
        + ') ->'
        + body
    )
    path.write_text(weakened)
    assert (
        signature.count(annotation),
        weakened != local,
        strong,
        tuple(map(location, typed(tmp_path, source))),
    ) == (
        1,
        True,
        tuple(
            zip(
                ('reportArgumentType',) * 3,
                (str(tmp_path / 'consumer.py'),) * 3,
                range(9, 12),
                strict=True,
            )
        ),
        tuple(
            ('reportArgumentType', str(tmp_path / 'consumer.py'), index)
            for index in range(9, 12)
            if index != line
        ),
    )


@pytest.mark.parametrize('empty', (False, True))
@pytest.mark.parametrize('trials', (1, 4))
def test_observed_cpu_preserves_all_five_ordinary_tensors_hashes_and_input_aliases(
    empty: bool, trials: int
) -> None:
    case = fixture(empty)
    targets = case.targets
    events = case.events[:trials, :25]
    events.setflags(write=False)
    before = (id(targets), tuple(map(id, targets)), id(events), array_state(events))
    model = prepare(
        case.connectome,
        targets,
        (),
        trials,
        reference_parameters=model_parameters(),
        silence=build_connectome_silencer(),
    )
    state = model.state_init()
    expected = [record(capture(state, -1))]
    with torch.no_grad():
        for step in range(events.shape[1]):
            counts = replay_inputs(events[:, step], targets, 6)
            state = model.forward(counts, *state)
            expected.append(record(capture(state, step)))
    gradients = torch.is_grad_enabled()
    actual = tuple(
        (record(snapshot), torch.is_grad_enabled())
        for snapshot in observe(model, events, targets)
    )
    assert (
        actual,
        (id(targets), tuple(map(id, targets)), id(events), array_state(events)),
        model.weights.dtype,
        model.weights.device.type,
        model.weights.layout,
        expected[0][1],
    ) == (
        tuple((snapshot, gradients) for snapshot in expected),
        before,
        torch.float32,
        'cpu',
        torch.sparse_csr,
        ('g', 'delay_buffer', 'spikes', 'v', 'refrac'),
    )


@pytest.mark.parametrize('empty', (False, True))
def test_owned_target_scalars_keep_exact_overlap_empty_counts_and_host_layout(
    empty: bool,
) -> None:
    raw = () if empty else (0, 0, 2)
    targets = tuple(map(NeuronRow, raw))
    events = (
        np.empty((2, 0), dtype=np.uint8)
        if empty
        else np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
    )
    before = array_state(events)
    expected = (
        np.zeros((2, 3), dtype=np.float32)
        if empty
        else np.array([[2, 0, 0], [1, 0, 1]], dtype=np.float32)
    )
    actual = replay_inputs(events, targets, 3)
    assert (
        tuple(map(id, targets)),
        tuple(map(type, targets)),
        array_state(events),
        array_state(native_float(actual)),
        actual.dtype,
        actual.device.type,
        actual.layout,
    ) == (
        tuple(map(id, raw)),
        (int,) * len(raw),
        before,
        array_state(expected),
        torch.float32,
        'cpu',
        torch.strided,
    )


@pytest.mark.parametrize(
    'events',
    (
        np.array([[2, 0, 0]], dtype=np.uint8),
        np.array([[1, 0, 0]], dtype=np.int32),
        np.array([[1]], dtype=np.uint8),
        np.array([1, 0, 0], dtype=np.uint8),
    ),
)
def test_both_cpu_target_consumers_reject_bad_inputs_before_the_first_yield(
    events: NDArray[np.uint8],
) -> None:
    case = fixture()
    model = prepare(
        case.connectome,
        case.targets,
        (),
        1,
        reference_parameters=model_parameters(),
        silence=build_connectome_silencer(),
    )
    with pytest.raises(ValueError, match='matching canonical uint8 channels'):
        replay_inputs(events, case.targets, 6)
    with pytest.raises(ValueError, match='canonical trial-by-step channels'):
        next(observe(model, events[np.newaxis], case.targets))
