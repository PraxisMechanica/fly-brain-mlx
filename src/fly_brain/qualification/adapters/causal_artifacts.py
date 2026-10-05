from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from .causal_capture import CauseContext
from .observer_evidence import array_record, physical_record


def write_context(path: Path, context: CauseContext) -> dict[str, object]:
    arrays: dict[str, NDArray[np.generic]] = {}
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
        arrays[f'{position}_reference_spikes'] = observed.snapshot.spikes
        arrays[f'{position}_reference_source_spikes'] = observed.snapshot.source_spikes
        for index, pathway in enumerate(observed.snapshot.pathways):
            prefix = f'{position}_reference_pathway_{index}'
            arrays[prefix + '_delivered'] = pathway.delivered
            for thread, queue in enumerate(pathway.queues):
                queue_prefix = f'{prefix}_queue_{thread}'
                arrays[queue_prefix + '_offset'] = np.asarray(
                    queue.offset, dtype=np.int32
                )
                for slot, values in enumerate(queue.slots):
                    arrays[f'{queue_prefix}_slot_{slot}'] = values
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
