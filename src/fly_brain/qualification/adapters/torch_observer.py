from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .paired_observer import phase_hash
from .torch_reference import TensorState
from .torch_setup import native_float


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
    hashes = tuple(
        phase_hash({name: value[trial : trial + 1] for name, value in fields.items()})
        for trial in range(shape[0])
    )
    return TorchSnapshot(step, fields, hashes)
