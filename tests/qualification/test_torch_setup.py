import numpy as np
import pytest
import torch

from fly_brain.qualification.adapters.torch_reference import (
    TorchModel,
    model_parameters,
)
from fly_brain.qualification.adapters.torch_setup import (
    native_float,
    prepare,
    replay_inputs,
)
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference]


def test_sparse_cpu_setup_preserves_orientation_outgoing_silencing_and_activation() -> (
    None
):
    case = fixture()
    model = prepare(case.connectome, case.targets, (3,), 1)
    expected = np.zeros((6, 6), dtype=np.float32)
    for source, target, count in zip(
        case.connectome.sources,
        case.connectome.destinations,
        case.connectome.counts,
        strict=True,
    ):
        expected[target, source] += count if source != 3 else 0
    assert np.array_equal(native_float(model.weights.to_dense()), expected)
    assert (
        model.weights.layout == torch.sparse_csr and model.weights.device.type == 'cpu'
    )
    assert native_float(model.state_init()[4]).tolist() == [[0, 0, 22, 22, 22, 22]]


def test_replay_preserves_overlapping_channels_as_counts_at_original_input_slot() -> (
    None
):
    actual = replay_inputs(
        np.array([[1, 1, 0], [0, 1, 1]], dtype=np.uint8), (0, 0, 2), 3
    )
    assert actual.dtype == torch.float32 and native_float(actual).tolist() == [
        [2, 0, 0],
        [1, 0, 1],
    ]


@pytest.mark.parametrize('trials', (1, 4))
def test_replay_matches_guaranteed_native_poisson_for_all_five_returned_tensors(
    trials: int,
) -> None:
    case = fixture()
    targets = (0, 2)
    replay = prepare(case.connectome, targets, (), trials)
    native = TorchModel(
        trials, 6, 0.1, model_parameters(), replay.weights, list(targets), device='cpu'
    )
    actual, expected = replay.state_init(), native.state_init()
    rates = torch.zeros(trials, 6)
    rates[:, list(targets)] = 10000
    counts = replay_inputs(np.ones((trials, 2), dtype=np.uint8), targets, 6)
    with torch.no_grad():
        for _ in range(25):
            actual = replay.forward(counts, *actual)
            expected = native.forward(rates, *expected)
            assert all(
                native_float(first).tobytes() == native_float(second).tobytes()
                for first, second in zip(actual, expected, strict=True)
            )
