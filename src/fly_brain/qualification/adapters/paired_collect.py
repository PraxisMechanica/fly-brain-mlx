import json
from contextlib import closing
from pathlib import Path

import numpy as np

from fly_brain.qualification.ports import ReductionReader
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.engines import Execution
from fly_brain.simulation.models import Connectome, Stimulus

from .brian_jobs import BrianJob, results, run
from .causal_capture import CausalCapture
from .mlx_ledger import EventLedger
from .mlx_observer import MLXBlock, observe
from .observer_evidence import physical_arrays, physical_hash, physical_record
from .observer_stream import FinalSnapshot
from .paired_causes import write as write_causes
from .paired_observer import pair_blocks
from .reference_native import verify as verify_native
from .reference_queues import ReferenceQueues


def collect(
    job: BrianJob,
    execution: Execution,
    connectome: Connectome,
    stimulus: Stimulus,
    output: Path,
    *,
    read_rows: ReductionReader,
    record_reference: bool = False,
) -> CausalCapture:
    events = stimulus.events
    if (
        events.ndim != 3
        or events.shape != (1, job.shape.steps, len(stimulus.targets))
        or events.dtype != np.uint8
        or np.any(events > 1)
        or job.shape.neurons != len(connectome.neuron_ids)
        or execution.network.neurons != job.shape.neurons
        or not job.observed
    ):
        raise ValueError('Paired collection requires one complete canonical trial')
    output.mkdir(parents=True, exist_ok=False)
    capture = CausalCapture()
    steps: list[int] = []
    neurons: list[int] = []
    reference_spikes: list[int] = []
    reference_times: list[float] = []
    last: MLXBlock | None = None
    final: FinalSnapshot | None = None
    with (
        closing(
            run(
                job,
                output / 'reference-results',
                tape=output / 'reference-wire.gz' if record_reference else None,
            )
        ) as reference,
        closing(
            observe(
                execution,
                core.initial_state(execution.network),
                events,
                EventLedger(connectome, stimulus.targets, 1),
                job.shape.block_size,
            )
        ) as mlx,
        (output / 'phase-digests.jsonl').open('x') as phases,
        (output / 'physical-digests.jsonl').open('x') as physical,
    ):
        for frame in pair_blocks(
            reference,
            mlx,
            ReferenceQueues(connectome.sources, job.shape.neurons, events[0]),
        ):
            if isinstance(frame, FinalSnapshot):
                final = frame
                snapshots = (frame.step,)
            else:
                capture.check(frame)
                last = frame.mlx
                phases.write(
                    json.dumps(
                        {
                            'begin': last.begin,
                            'rows': last.rows,
                            'native_phase_sha256': frame.native_sha256,
                            'mlx_queue_sha256': last.queue_sha256,
                            'mlx_due_sha256': last.due_sha256,
                        }
                    )
                    + '\n'
                )
                rows, _, indices = np.nonzero(last.fields['spikes'])
                steps.extend((rows + last.begin).tolist())
                neurons.extend(indices.tolist())
                snapshots = frame.snapshots
                for snapshot in snapshots:
                    reference_spikes.extend(snapshot.spikes.tolist())
                    reference_times.extend([snapshot.time_s] * snapshot.spikes.size)
            for snapshot in snapshots:
                physical.write(
                    json.dumps(
                        {'step': snapshot.step, 'sha256': physical_hash(snapshot)}
                    )
                    + '\n'
                )
    if final is None or last is None or last.final_queue is None:
        raise ValueError('Paired collection is missing final actual state or queues')
    native = results(job, output / 'reference-results')
    verify_native(
        job,
        output / 'reference-results',
        final,
        native,
        reference_spikes,
        reference_times,
        connectome.sources.size,
    )
    with (output / 'reference-native.npz').open('xb') as artifact:
        np.savez_compressed(artifact, **native)
    with (output / 'reference-final-physical.npz').open('xb') as artifact:
        np.savez_compressed(artifact, **physical_arrays(final.step, 'reference'))
    with (output / 'reference-final-physical.json').open('x') as metadata:
        json.dump(physical_record(final.step), metadata)
    arrays = {name: value[-1, 0].copy() for name, value in last.fields.items()}
    arrays['queue'] = last.final_queue
    arrays['spike_steps'] = np.asarray(steps, dtype=np.int64)
    arrays['spike_neurons'] = np.asarray(neurons, dtype=np.int64)
    with (output / 'mlx-native.npz').open('xb') as artifact:
        np.savez_compressed(artifact, **arrays)
    write_causes(capture, job, read_rows, connectome, stimulus, output)
    return capture
