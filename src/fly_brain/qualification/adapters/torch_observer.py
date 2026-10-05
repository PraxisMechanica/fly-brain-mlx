from collections.abc import Generator
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from .paired_observer import phase_hash
from .torch_reference import TensorState, TorchModel
from .torch_setup import native_float, replay_inputs


@dataclass(frozen=True)
class TorchSnapshot:
    step: int
    fields: dict[str, NDArray[np.float32]]
    native_sha256: tuple[str, ...]


def capture(state: TensorState, step: int) -> TorchSnapshot:
    fields = {
        name: native_float(value).copy()
        for name, value in zip(
            ('g', 'delay_buffer', 'spikes', 'v', 'refrac'), state, strict=True
        )
    }
    shape = fields['v'].shape
    if len(shape) != 2 or not all(shape):
        raise ValueError('CPU observer requires trial-by-neuron state')
    for name, value in fields.items():
        expected = (shape[0], 19, shape[1]) if name == 'delay_buffer' else shape
        if value.shape != expected or not np.isfinite(value).all():
            raise ValueError(f'Invalid native CPU reference field: {name}')
    spikes, refractory = fields['spikes'], fields['refrac']
    if (
        np.any((spikes != 0) & (spikes != 1))
        or np.any(refractory < 0)
        or np.any(refractory != np.floor(refractory))
    ):
        raise ValueError(
            'CPU reference spikes and refractory counters must be discrete'
        )
    hashes = tuple(
        phase_hash({name: value[trial : trial + 1] for name, value in fields.items()})
        for trial in range(shape[0])
    )
    return TorchSnapshot(step, fields, hashes)


def observe(
    model: TorchModel, events: NDArray[np.uint8], targets: tuple[int, ...]
) -> Generator[TorchSnapshot, None, None]:
    if (
        events.ndim != 3
        or events.shape[0] != model.neurons.neuron.batch
        or not events.shape[1]
        or events.shape[2] != len(targets)
        or events.dtype != np.uint8
        or np.any(events > 1)
    ):
        raise ValueError('CPU observer requires canonical trial-by-step channels')
    with torch.no_grad():
        state = model.state_init()
    yield capture(state, -1)
    for step in range(events.shape[1]):
        counts = replay_inputs(events[:, step, :], targets, model.neurons.size)
        with torch.no_grad():
            state = model.forward(counts, *state)
        yield capture(state, step)
