import json
from contextlib import closing
from pathlib import Path

import numpy as np

from fly_brain.qualification.ports import ObservationSessionFactory
from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.qualification.session_expectations import CHECK_NAMES
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.models import Connectome, Stimulus

from .paired_observer import phase_hash, trial_block


def collect(
    factory: ObservationSessionFactory,
    connectome: Connectome,
    stimulus: Stimulus,
    output: Path,
) -> None:
    events = stimulus.events
    if (
        events.ndim != 3
        or events.shape[0] != 4
        or not events.shape[1]
        or events.shape[2] != len(stimulus.targets)
        or events.dtype != np.uint8
        or np.any(events > 1)
        or stimulus.trial_indices != (0, 1, 2, 3)
    ):
        raise ValueError('MLX batch collection requires four complete canonical trials')
    output.mkdir(parents=True, exist_ok=False)
    trials: list[int] = []
    neurons: list[int] = []
    steps: list[int] = []
    last: SessionBlock | None = None
    completed = 0
    with (
        closing(
            observe_session(
                factory,
                connectome,
                stimulus.targets,
                stimulus.trial_indices,
                events,
            )
        ) as blocks,
        (output / 'phase-digests.jsonl').open('x') as phases,
    ):
        for block in blocks:
            if (
                block.begin != completed
                or block.rows != min(32, events.shape[1] - completed)
                or block.checks.shape != (block.rows, 4, len(CHECK_NAMES))
                or not block.checks.all()
            ):
                raise ValueError(
                    'MLX batch observation has incomplete or invalid evidence'
                )
            phases.write(
                json.dumps(
                    {
                        'begin': block.begin,
                        'rows': block.rows,
                        'native_phase_sha256': [
                            phase_hash(trial_block(block, trial).fields)
                            for trial in range(4)
                        ],
                        'mlx_queue_sha256': block.queue_sha256,
                        'mlx_due_sha256': block.due_sha256,
                    }
                )
                + '\n'
            )
            rows, positions, indices = np.nonzero(block.fields['spikes'])
            trials.extend(positions.tolist())
            neurons.extend(indices.tolist())
            steps.extend((rows + block.begin).tolist())
            completed += block.rows
            last = block
    if last is None or last.final_queue is None or completed != events.shape[1]:
        raise ValueError(
            'MLX batch collection is missing complete final state or queues'
        )
    with (output / 'native.npz').open('xb') as artifact:
        np.savez_compressed(
            artifact,
            **{name: value[-1].copy() for name, value in last.fields.items()},
            queue=last.final_queue,
            spike_trials=np.asarray(trials, dtype=np.int64),
            spike_neurons=np.asarray(neurons, dtype=np.int64),
            spike_steps=np.asarray(steps, dtype=np.int64),
        )
