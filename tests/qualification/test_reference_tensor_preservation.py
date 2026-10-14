import hashlib
import json
from types import MappingProxyType, ModuleType

import pytest
import torch

from fly_brain.qualification import reference_parameters
from fly_brain.qualification.adapters import torch_setup
from fly_brain.qualification.adapters.torch_reference import TensorState
from tests.support.observation_fixtures import fixture
from tests.support.reference_baseline import original as original

pytestmark = [pytest.mark.integration, pytest.mark.reference]


def snapshot(state: TensorState) -> tuple[tuple[str, tuple[int, ...], bytes], ...]:
    return tuple(
        (
            str(value.dtype),
            tuple(value.shape),
            torch_setup.native_float(value).tobytes(),
        )
        for value in state
    )


@pytest.mark.parametrize(
    'empty,duplicates', ((False, False), (False, True), (True, False))
)
@pytest.mark.parametrize('trials', (1, 4))
@pytest.mark.parametrize('silenced', ((), (3,)))
def test_initial_and_every_chunked_native_tensor_byte_matches_independent_old_source(
    original: tuple[ModuleType, ModuleType],
    empty: bool,
    duplicates: bool,
    trials: int,
    silenced: tuple[int, ...],
) -> None:
    _, previous = original
    case = fixture(empty)
    targets, events = case.targets, case.events[:trials]
    if not empty and not duplicates:
        targets = (targets[0], targets[2])
        events = events[:, :, (0, 2)]
    old = previous.prepare(case.connectome, targets, silenced, trials)
    new = torch_setup.prepare(
        case.connectome,
        targets,
        silenced,
        trials,
        reference_parameters=MappingProxyType(reference_parameters.model_parameters()),
    )
    old_state, new_state = old.state_init(), new.state_init()
    assert snapshot(old_state) == snapshot(new_state)
    digest = hashlib.sha256()
    begin = 0
    with torch.no_grad():
        for size in (1, 17, 1, 18, 32, 32):
            for index in range(begin, begin + size):
                before = previous.replay_inputs(events[:, index], targets, 6)
                after = torch_setup.replay_inputs(events[:, index], targets, 6)
                assert (
                    torch_setup.native_float(before).tobytes()
                    == torch_setup.native_float(after).tobytes()
                )
                old_state = old.forward(before, *old_state)
                new_state = new.forward(after, *new_state)
                expected, actual = snapshot(old_state), snapshot(new_state)
                assert expected == actual, (empty, duplicates, trials, silenced, index)
                for dtype, shape, payload in actual:
                    digest.update(repr((dtype, shape)).encode())
                    digest.update(payload)
            begin += size
    assert begin == events.shape[1] == 101
    print(
        json.dumps(
            {
                'empty': empty,
                'duplicates': duplicates,
                'trials': trials,
                'silenced': silenced,
                'tensor_pairs': 510,
                'trajectory': digest.hexdigest(),
            }
        )
    )


@pytest.mark.parametrize('index', range(5))
def test_native_byte_control_detects_each_changed_initial_tensor(
    original: tuple[ModuleType, ModuleType],
    index: int,
) -> None:
    _, previous = original
    case = fixture()
    old = previous.prepare(case.connectome, case.targets, (), 1).state_init()
    new = torch_setup.prepare(
        case.connectome,
        case.targets,
        (),
        1,
        reference_parameters=reference_parameters.model_parameters(),
    ).state_init()
    assert snapshot(old) == snapshot(new)
    new[index].add_(1)
    assert snapshot(old) != snapshot(new)
