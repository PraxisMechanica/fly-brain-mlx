from collections.abc import Mapping, Sequence
from functools import partial
from typing import Literal

import numpy as np
import pytest
import torch
from numpy.typing import NDArray

from fly_brain import bootstrap
from fly_brain.qualification.adapters import torch_setup
from fly_brain.qualification.adapters.torch_reference import TorchModel
from fly_brain.qualification.reference_parameters import model_parameters
from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.models import Connectome
from fly_brain.simulation.module import build_connectome_silencer
from tests.support.observation_fixtures import fixture

pytestmark = [pytest.mark.integration, pytest.mark.reference]


def test_setup_consumes_returned_connectome_in_original_constructor_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = fixture()
    selectors = (NeuronRow(3),)
    events: list[str] = []
    values = model_parameters()
    original_tensor, original_model, original_replay = (
        torch_setup.tensor,
        torch_setup.TorchModel,
        torch_setup.Replay,
    )

    def silence(connectome: Connectome, silenced: tuple[NeuronRow, ...]) -> Connectome:
        assert connectome is case.connectome and silenced is selectors
        events.append('silence')
        return build_connectome_silencer()(connectome, silenced)

    def tensor(array: NDArray[np.int32 | np.float32]) -> torch.Tensor:
        events.append('tensor:' + str(array.dtype))
        return original_tensor(array)

    def parameters(source: Mapping[str, float]) -> dict[str, float]:
        events.append('parameters')
        return dict(source)

    def model(
        batch: int,
        size: int,
        dt: float,
        params: Mapping[str, float],
        weights: torch.Tensor,
        exc_indices: Sequence[int],
        device: Literal['cpu'],
    ) -> TorchModel:
        events.append('model')
        assert (params is values, params, weights.layout) == (
            False,
            values,
            torch.sparse_csr,
        )
        return original_model(batch, size, dt, params, weights, exc_indices, device)

    def replay(scale: float) -> torch_setup.Replay:
        events.append('replay')
        return original_replay(scale)

    monkeypatch.setattr(torch_setup, 'tensor', tensor)
    monkeypatch.setattr(torch_setup, 'dict', parameters, raising=False)
    monkeypatch.setattr(torch_setup, 'TorchModel', model)
    monkeypatch.setattr(torch_setup, 'Replay', replay)
    actual = torch_setup.prepare(
        case.connectome,
        case.targets,
        selectors,
        1,
        reference_parameters=values,
        silence=silence,
    )
    constructed = tuple(events)
    expected = np.zeros((6, 6), dtype=np.float32)
    for source, target, count in zip(
        case.connectome.sources,
        case.connectome.destinations,
        case.connectome.counts,
        strict=True,
    ):
        expected[target, source] += count if source != 3 else 0
    assert (
        constructed,
        torch_setup.native_float(actual.weights.to_dense()).tobytes(),
        isinstance(actual.poisson, original_replay),
    ) == (
        ('silence', 'tensor:int32', 'tensor:float32', 'parameters', 'model', 'replay'),
        expected.tobytes(),
        True,
    )


def test_precision_guard_precedes_callback_and_callback_error_precedes_construction() -> (
    None
):
    case = fixture()
    calls: list[tuple[NeuronRow, ...]] = []
    error = ValueError('injected silencing failure')

    def fail(connectome: Connectome, silenced: tuple[NeuronRow, ...]) -> Connectome:
        calls.append(silenced)
        raise error

    previous = torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.float64)
        with pytest.raises(RuntimeError, match='default float32'):
            torch_setup.prepare(
                case.connectome,
                (),
                (NeuronRow(99),),
                1,
                reference_parameters={},
                silence=fail,
            )
        assert calls == []
        torch.set_default_dtype(torch.float32)
        with pytest.raises(ValueError) as failure:
            torch_setup.prepare(
                case.connectome,
                (),
                (NeuronRow(99),),
                1,
                reference_parameters={},
                silence=fail,
            )
        assert failure.value is error and calls == [(NeuronRow(99),)]
    finally:
        torch.set_default_dtype(previous)


def test_actual_bootstrap_supplies_owned_silencing_without_running_it() -> None:
    threads = torch.get_num_threads()
    try:
        command = bootstrap.parity_case()
    finally:
        torch.set_num_threads(threads)
    assert isinstance(command, partial)
    use_case = command.keywords['use_case']
    assert isinstance(use_case, partial)
    execute = use_case.keywords['execute']
    assert isinstance(execute, partial)
    assert execute.keywords['silence'] is build_connectome_silencer()
