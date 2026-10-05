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
