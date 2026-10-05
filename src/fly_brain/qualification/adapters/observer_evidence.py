import hashlib
import json

import numpy as np
from numpy.typing import NDArray

from .observer_stream import StepSnapshot


def array_record(value: NDArray[np.generic]) -> dict[str, object]:
    return {
        'dtype': value.dtype.str,
        'shape': list(value.shape),
        'sha256': hashlib.sha256(value.tobytes(order='C')).hexdigest(),
    }


def physical_arrays(
    snapshot: StepSnapshot, prefix: str
) -> dict[str, NDArray[np.generic]]:
    arrays: dict[str, NDArray[np.generic]] = {
        prefix + '_spikes': snapshot.spikes,
        prefix + '_source_spikes': snapshot.source_spikes,
    }
    for index, pathway in enumerate(snapshot.pathways):
        path_prefix = f'{prefix}_pathway_{index}'
        arrays[path_prefix + '_delivered'] = pathway.delivered
        for thread, queue in enumerate(pathway.queues):
            queue_prefix = f'{path_prefix}_queue_{thread}'
            arrays[queue_prefix + '_offset'] = np.asarray(queue.offset, dtype=np.int32)
            for slot, values in enumerate(queue.slots):
                arrays[f'{queue_prefix}_slot_{slot}'] = values
    return arrays


def physical_record(snapshot: StepSnapshot) -> dict[str, object]:
    return {
        'step': snapshot.step,
        'clock_step': snapshot.clock_step,
        'time_s_hex': snapshot.time_s.hex(),
        'source_cursor': snapshot.source_cursor,
        'spikes': array_record(snapshot.spikes),
        'source_spikes': array_record(snapshot.source_spikes),
        'pathways': [
            {
                'queues': [
                    {
                        'offset': queue.offset,
                        'slots': [array_record(slot) for slot in queue.slots],
                    }
                    for queue in pathway.queues
                ],
                'delivered': array_record(pathway.delivered),
            }
            for pathway in snapshot.pathways
        ],
    }


def physical_hash(snapshot: StepSnapshot) -> str:
    encoded = json.dumps(
        physical_record(snapshot), sort_keys=True, separators=(',', ':')
    ).encode()
    return hashlib.sha256(encoded).hexdigest()
