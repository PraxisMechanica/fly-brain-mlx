from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import numpy as np
import torch
from numpy.typing import NDArray

from .torch_reference import TensorState, TorchModel
from .torch_setup import native_float, tensor

TorchStep = Callable[
    [
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
        torch.Tensor,
    ],
    TensorState,
]


@dataclass(frozen=True)
class ActiveSources:
    offsets: NDArray[np.int64]
    destinations: NDArray[np.int64]
    counts: NDArray[np.float64]
    neurons: int

    @classmethod
    def from_model(cls, model: TorchModel) -> 'ActiveSources':
        weights = model.weights
        neurons = model.neurons.size
        if weights.layout != torch.sparse_csr or weights.shape != (neurons, neurons):
            raise ValueError(
                'Active-source evaluation requires the prepared CSR matrix'
            )
        counts = native_float(weights.values()).astype(np.float64)
        offsets = cast(NDArray[np.int64], weights.crow_indices().numpy())  # pyright: ignore[reportUnknownMemberType]
        sources = cast(NDArray[np.int64], weights.col_indices().numpy())  # pyright: ignore[reportUnknownMemberType]
        destinations = np.repeat(np.arange(neurons), np.diff(offsets))
        if (
            not np.isfinite(counts).all()
            or np.any(counts != np.rint(counts))
            or np.any(
                np.bincount(destinations, weights=np.abs(counts), minlength=neurons)
                >= 2**24
            )
        ):
            raise ValueError('Active-source weights exceed the exact integer envelope')
        order = np.argsort(sources, kind='stable')
        outgoing = np.bincount(sources, minlength=neurons)
        arrays = (
            np.concatenate((np.zeros(1, dtype=np.int64), np.cumsum(outgoing))),
            destinations[order],
            counts[order],
        )
        for array in arrays:
            array.setflags(write=False)
        return cls(*arrays, neurons)

    def __call__(self, spikes: torch.Tensor) -> torch.Tensor:
        rows = native_float(spikes)
        if (
            rows.ndim != 2
            or rows.shape[1] != self.neurons
            or np.any((rows != 0) & (rows != 1))
        ):
            raise ValueError('Active-source propagation requires binary recurrent rows')
        outputs: list[NDArray[np.float32]] = []
        for row in rows:
            active = np.flatnonzero(row)
            indices = np.concatenate(
                [np.empty(0, dtype=np.int64)]
                + [
                    np.arange(self.offsets[source], self.offsets[source + 1])
                    for source in active
                ]
            )
            outputs.append(
                np.bincount(
                    self.destinations[indices],
                    weights=self.counts[indices],
                    minlength=self.neurons,
                ).astype(np.float32)
            )
        return tensor(np.stack(outputs))


def step(model: TorchModel) -> TorchStep:
    sources = ActiveSources.from_model(model)

    def advance(
        rates: torch.Tensor,
        conductance: torch.Tensor,
        delay_buffer: torch.Tensor,
        spikes: torch.Tensor,
        voltage: torch.Tensor,
        refractory: torch.Tensor,
    ) -> TensorState:
        stimulus = model.scale * model.poisson.forward(rates)
        recurrent = model.scale * sources(spikes)
        return model.neurons.forward(
            recurrent, stimulus, conductance, delay_buffer, spikes, voltage, refractory
        )

    return advance
