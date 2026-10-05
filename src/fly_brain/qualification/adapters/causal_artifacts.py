from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .causal_capture import CauseContext
from .observer_evidence import array_record, physical_arrays, physical_record


def write_context(
    path: Path,
    context: CauseContext,
    reduction_inputs: dict[str, NDArray[np.generic]],
) -> dict[str, object]:
    arrays = dict(reduction_inputs)
    steps: list[dict[str, object]] = []
    for position, observed in (
        ('current', context.current),
        ('previous', context.previous),
    ):
        if observed is None:
            continue
        for engine, fields in (
            ('reference', observed.reference),
            ('mlx', observed.mlx),
        ):
            arrays.update(
                {f'{position}_{engine}_{name}': value for name, value in fields.items()}
            )
        arrays[f'{position}_mlx_due_edges'] = observed.mlx_due_edges
        arrays.update(physical_arrays(observed.snapshot, f'{position}_reference'))
        steps.append(
            {
                'position': position,
                'actual_snapshot': physical_record(observed.snapshot),
                'mlx_due_mask_sha256': observed.mlx_due_sha256,
            }
        )
    with path.open('xb') as artifact:
        np.savez_compressed(artifact, **arrays)
    return {
        'neurons': list(context.neurons),
        'steps': steps,
        'arrays': {name: array_record(value) for name, value in arrays.items()},
    }
