import hashlib
import json
import os
import resource
import subprocess
import time
import tracemalloc
from pathlib import Path

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.observations import PHASE_UNITS
from tests.support.session_proof_values import (
    BlockProof,
    Frame,
    MemorySample,
    TrialProof,
    value_signature,
)


def resident_bytes() -> int:
    value = subprocess.check_output(
        ['/bin/ps', '-o', 'rss=', '-p', str(os.getpid())], text=True
    )
    return int(value.strip()) * 1024


class Recorder:
    def __init__(self, output: Path, trials: tuple[int, ...]) -> None:
        output.mkdir(exist_ok=False)
        self.output = output
        self.trials = trials
        self.started = time.perf_counter()
        self.memory: list[MemorySample] = []
        self.proofs: list[BlockProof] = []

    def sample(self, stage: str, step: int) -> None:
        current, peak = tracemalloc.get_traced_memory()
        self.memory.append(
            MemorySample(
                stage=stage,
                step=step,
                elapsed_s=time.perf_counter() - self.started,
                resident_bytes=resident_bytes(),
                process_peak_resident_bytes=int(
                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                ),
                mlx_active_bytes=mx.get_active_memory(),
                mlx_cache_bytes=mx.get_cache_memory(),
                mlx_peak_bytes=mx.get_peak_memory(),
                traced_host_current_bytes=current,
                traced_host_peak_bytes=peak,
            )
        )
        with (self.output / 'memory-stream.jsonl').open('a') as destination:
            destination.write(self.memory[-1].model_dump_json() + '\n')

    def queue(self, step: int, queue: NDArray[np.bool_]) -> None:
        if queue.dtype != np.bool_ or queue.shape[0:2] != (19, len(self.trials)):
            raise ValueError('Actual queue dtype, slots or trial coverage differs')
        path = self.output / f'queue-{step:04d}.npz'
        with path.open('xb') as destination:
            np.savez_compressed(destination, queue=queue)
        self.sample('physical-queue-return', step)

    def frame(self, frame: Frame) -> None:
        end = frame.begin + frame.rows
        queue_path = self.output / f'queue-{end:04d}.npz'
        path = self.output / f'block-{frame.begin:04d}.npz'
        arrays = dict(frame.fields)
        for row, edges in enumerate(frame.due_edges):
            for trial, identities in enumerate(edges):
                arrays[f'due-{row}-{trial}'] = identities
        if frame.checks is not None:
            if frame.checks.shape != (frame.rows, len(self.trials), 30):
                raise ValueError('Actual checks do not cover all trials and 30 gates')
            if not frame.checks.all():
                raise ValueError('Actual independent observation checks failed')
            arrays['checks'] = frame.checks
        with path.open('xb') as destination:
            np.savez_compressed(destination, **arrays)
        with np.load(queue_path, allow_pickle=False) as saved:
            queue: NDArray[np.bool_] = saved['queue']
        by_trial = {
            str(trial): TrialProof(
                fields={
                    name: value_signature(value[:, row : row + 1])
                    for name, value in frame.fields.items()
                },
                due_edges=tuple(
                    value_signature(edges[row]) for edges in frame.due_edges
                ),
                due_sha256=tuple(hashes[row] for hashes in frame.due_sha256),
                queue=value_signature(queue[:, row : row + 1]),
                queue_slot_sha256=tuple(
                    value_signature(queue[slot, row]).sha256 for slot in range(19)
                ),
            )
            for row, trial in enumerate(self.trials)
        }
        self.proofs.append(
            BlockProof(
                begin=frame.begin,
                rows=frame.rows,
                trials=self.trials,
                units=dict(PHASE_UNITS),
                by_trial=by_trial,
                measured_checks=frame.checks is not None,
                checks_all=frame.checks is not None and bool(frame.checks.all()),
                artifact_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                queue_artifact_sha256=hashlib.sha256(
                    queue_path.read_bytes()
                ).hexdigest(),
            )
        )
        with (self.output / 'blocks-stream.jsonl').open('a') as destination:
            destination.write(self.proofs[-1].model_dump_json() + '\n')
        self.sample('yielded-block-and-artifact-check', end)
        print(
            f'{self.output.name} {end} steps {time.perf_counter() - self.started:.3f}s '
            f'MLX peak {mx.get_peak_memory()} bytes',
            flush=True,
        )

    def finish(self) -> None:
        with (self.output / 'blocks.json').open('x') as destination:
            json.dump([proof.model_dump() for proof in self.proofs], destination)
        with (self.output / 'memory.json').open('x') as destination:
            json.dump([sample.model_dump() for sample in self.memory], destination)
