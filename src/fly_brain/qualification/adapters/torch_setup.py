from typing import cast

import numpy as np
import torch
import torch.nn as nn
from numpy.typing import NDArray

from fly_brain.simulation.mapping import silence_sources
from fly_brain.simulation.models import Connectome

from .torch_reference import TorchModel, model_parameters


def tensor(values: NDArray[np.float32 | np.int32 | np.int64]) -> torch.Tensor:
    return torch.from_numpy(values)  # pyright: ignore[reportUnknownMemberType]


def native_float(value: torch.Tensor) -> NDArray[np.float32]:
    if value.device.type != 'cpu' or value.dtype != torch.float32:
        raise ValueError('Reference tensor must retain native CPU float32')
    return cast(NDArray[np.float32], value.detach().numpy())  # pyright: ignore[reportUnknownMemberType]


class Replay(nn.Module):
    def __init__(self, scale: float) -> None:
        super().__init__()
        self.scale = scale

    def forward(
        self, counts: torch.Tensor, generator: torch.Generator | None = None
    ) -> torch.Tensor:
        return counts * self.scale


def prepare(
    connectome: Connectome,
    targets: tuple[int, ...],
    silenced: tuple[int, ...],
    trials: int,
) -> TorchModel:
    if torch.get_default_dtype() != torch.float32:
        raise RuntimeError('The pinned PyTorch comparator requires default float32')
    connectome = silence_sources(connectome, silenced)
    neurons = len(connectome.neuron_ids)
    weights = torch.sparse_coo_tensor(  # pyright: ignore[reportUnknownMemberType]
        tensor(np.stack((connectome.destinations, connectome.sources))),
        tensor(connectome.counts.astype(np.float32)),
        (neurons, neurons),
        dtype=torch.float32,
        device='cpu',
    ).to_sparse_csr()
    params = model_parameters()
    model = TorchModel(
        trials, neurons, 0.1, params, weights, list(targets), device='cpu'
    )
    model.add_module('poisson', Replay(params['scalePoisson']))
    return model


def replay_inputs(
    events: NDArray[np.uint8], targets: tuple[int, ...], neurons: int
) -> torch.Tensor:
    if (
        events.ndim != 2
        or events.shape[1] != len(targets)
        or events.dtype != np.uint8
        or np.any(events > 1)
    ):
        raise ValueError('PyTorch replay requires matching canonical uint8 channels')
    counts = np.zeros((len(events), neurons), dtype=np.float32)
    for channel, target in enumerate(targets):
        counts[:, target] += events[:, channel]
    return tensor(counts)
