import json
from contextlib import closing
from pathlib import Path

import numpy as np

from fly_brain.simulation.models import Stimulus

from .active_cpu import TorchStep
from .torch_observer import TorchSnapshot, observe
from .torch_reference import TorchModel


def collect(
    model: TorchModel,
    stimulus: Stimulus,
    output: Path,
    advance: TorchStep | None = None,
) -> None:
    output.mkdir(parents=True, exist_ok=False)
    trials: list[int] = []
    neurons: list[int] = []
    steps: list[int] = []
    final: TorchSnapshot | None = None
    with (
        closing(
            observe(model, stimulus.events, stimulus.targets, advance)
        ) as snapshots,
        (output / 'native-digests.jsonl').open('x') as digests,
    ):
        for snapshot in snapshots:
            digests.write(
                json.dumps(
                    {
                        'step': snapshot.step,
                        'native_sha256': snapshot.native_sha256,
                    }
                )
                + '\n'
            )
            if snapshot.step >= 0:
                rows, indices = np.nonzero(snapshot.fields['spikes'])
                trials.extend(rows.tolist())
                neurons.extend(indices.tolist())
                steps.extend([snapshot.step] * len(rows))
            final = snapshot
    if final is None or final.step != stimulus.events.shape[1] - 1:
        raise ValueError('CPU collection is missing complete native final state')
    with (output / 'native.npz').open('xb') as artifact:
        np.savez_compressed(
            artifact,
            **final.fields,
            spike_trials=np.asarray(trials, dtype=np.int64),
            spike_neurons=np.asarray(neurons, dtype=np.int64),
            spike_steps=np.asarray(steps, dtype=np.int64),
        )
