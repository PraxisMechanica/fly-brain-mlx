import json
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray


def verify(paired: Path, steps: int, edges: int) -> tuple[int, ...]:
    metadata = json.loads((paired / 'reference-final-physical.json').read_text())
    if metadata['step'] != steps or metadata['clock_step'] != steps:
        raise ValueError('Final physical queues have a different clock')
    with (
        np.load(paired / 'mlx-native.npz', allow_pickle=False) as mlx,
        np.load(
            paired / 'reference-final-physical.npz', allow_pickle=False
        ) as reference,
    ):
        queue = mlx['queue']
        if queue.dtype != np.bool_ or queue.shape != (19, 1, edges):
            raise ValueError('Actual MLX final queue has invalid native geometry')
        if queue[(steps - 1) % 19].any():
            raise ValueError('Actual MLX delivered slot was not cleared')
        if not edges:
            return (0,) * 18
        offset = reference['reference_pathway_0_queue_0_offset']
        if (
            offset.dtype != np.int32
            or offset.shape != ()
            or offset.item() != steps % 19
        ):
            raise ValueError('Actual reference final queue offset differs')
        counts: list[int] = []
        for delay in range(18):
            slot = (int(offset) + 1 + delay) % 19
            ids = cast(
                NDArray[np.int32], reference[f'reference_pathway_0_queue_0_slot_{slot}']
            )
            if (
                ids.dtype != np.int32
                or ids.ndim != 1
                or np.any(ids < 0)
                or np.any(ids >= edges)
                or len(np.unique(ids)) != len(ids)
            ):
                raise ValueError('Actual reference pending identities are invalid')
            if not np.array_equal(
                np.flatnonzero(queue[(steps + delay) % 19, 0]), np.sort(ids)
            ):
                raise ValueError(
                    f'Actual final pending events differ at step {steps + delay}'
                )
            counts.append(len(ids))
    return tuple(counts)
