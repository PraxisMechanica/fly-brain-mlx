import numpy as np
import pytest

from fly_brain.qualification.adapters.torch_observer import capture
from fly_brain.qualification.adapters.torch_setup import native_float, prepare
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference]


@pytest.mark.parametrize('index', range(5))
def test_native_snapshot_owns_and_hashes_every_actual_tensor(index: int) -> None:
    case = fixture()
    state = prepare(case.connectome, case.targets, (), 4).state_init()
    saved = capture(state, -1)
    names = tuple(saved.fields)
    assert all(
        saved.fields[name].tobytes() == native_float(value).tobytes()
        for name, value in zip(names, state, strict=True)
    )
    previous = saved.fields[names[index]].tobytes()
    state[index].add_(1)
    changed = capture(state, 0)
    assert changed.native_sha256 != saved.native_sha256
    assert saved.fields[names[index]].tobytes() == previous
    assert all(value.dtype == np.float32 for value in saved.fields.values())


@pytest.mark.parametrize('index', range(5))
def test_observer_rejects_nonfinite_actual_reference_state(index: int) -> None:
    case = fixture()
    state = prepare(case.connectome, case.targets, (), 1).state_init()
    state[index].fill_(float('nan'))
    with pytest.raises(ValueError, match='Invalid native CPU reference field'):
        capture(state, 0)
