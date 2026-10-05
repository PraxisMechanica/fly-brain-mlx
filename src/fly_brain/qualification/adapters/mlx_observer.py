import hashlib
from collections.abc import Iterator
from dataclasses import dataclass

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import (
    HostArray,
    as_host,
    boolean_input,
    evaluate,
)
from fly_brain.simulation.backend.engines import Execution

from .mlx_ledger import EventLedger


@dataclass(frozen=True)
class MLXBlock:
    begin: int
    rows: int
    fields: dict[str, HostArray]
    checks: NDArray[np.bool_]
    queue_sha256: tuple[str, ...]
    final_queue: NDArray[np.bool_] | None
    due_edges: tuple[tuple[NDArray[np.int32], ...], ...]
    due_sha256: tuple[tuple[str, ...], ...]


def phase_fields(state: core.State, trace: core.StepTrace) -> dict[str, mx.array]:
    return {
        'pre_v': trace.pre_voltage_mv,
        'pre_g': trace.pre_synaptic_mv,
        'pre_not_refractory': trace.available,
        'spikes': trace.spikes,
        'before_v': trace.before_reset_voltage_mv,
        'before_g': trace.before_reset_synaptic_mv,
        'before_not_refractory': trace.receiving,
        'end_v': state.voltage_mv,
        'end_g': state.synaptic_mv,
        'end_last_spike_step': state.last_spike_step,
        'end_not_refractory': trace.receiving,
        'accepted_inputs': trace.accepted_inputs,
    }


def queue_hashes(queue: NDArray[np.bool_]) -> tuple[str, ...]:
    hashes: list[str] = []
    for trial in range(queue.shape[1]):
        digest = hashlib.sha256()
        for slot in range(queue.shape[0]):
            digest.update(memoryview(queue[slot, trial]))
        hashes.append(digest.hexdigest())
    return tuple(hashes)


def observe(
    execution: Execution,
    state: core.State,
    events: NDArray[np.uint8],
    ledger: EventLedger,
    block_size: int = 32,
) -> Iterator[MLXBlock]:
    if not 1 <= block_size <= 32:
        raise ValueError('MLX observer blocks must contain 1 to 32 steps')
    steps = events.shape[1]
    for begin in range(0, steps, block_size):
        end = min(begin + block_size, steps)
        rows: dict[str, list[mx.array]] = {}
        checks: list[mx.array] = []
        due_edges: list[tuple[NDArray[np.int32], ...]] = []
        due_sha256: list[tuple[str, ...]] = []
        for step in range(begin, end):
            with mx.stream(mx.gpu):
                inputs = boolean_input(events[:, step, :].astype(np.bool_))
                state, trace = execution.advance(state, inputs)
                fields = phase_fields(state, trace)
                flags = ledger.check(state, trace, inputs)
                evaluate(*state[:-1], *fields.values(), flags)
                due = np.asarray(trace.due, dtype=np.bool_)
                due_sha256.append(
                    tuple(
                        hashlib.sha256(memoryview(trial)).hexdigest() for trial in due
                    )
                )
                due_edges.append(
                    tuple(np.flatnonzero(trial).astype(np.int32) for trial in due)
                )
                del due
            checks.append(flags)
            for name, value in fields.items():
                rows.setdefault(name, []).append(value)
        with mx.stream(mx.gpu):
            arrays = {name: mx.stack(values) for name, values in rows.items()}
            flags = mx.stack(checks)
            evaluate(*arrays.values(), flags)
            recorded = {name: as_host(value) for name, value in arrays.items()}
            observed_checks = np.asarray(flags, dtype=np.bool_)
            queue = np.asarray(state.queue, dtype=np.bool_)
        hashes = queue_hashes(queue)
        final_queue = queue if end == steps else None
        del queue
        yield MLXBlock(
            begin,
            end - begin,
            recorded,
            observed_checks,
            hashes,
            final_queue,
            tuple(due_edges),
            tuple(due_sha256),
        )
