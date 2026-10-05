import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import mlx.core as mx
import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import (
    MLXBlock,
    observe,
)
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import (
    HostArray,
    as_host,
    boolean_input,
    evaluate,
)
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.models import Connectome

pytestmark = [pytest.mark.integration, pytest.mark.metal]


@dataclass(frozen=True)
class Fixture:
    connectome: Connectome
    targets: tuple[int, ...]
    events: NDArray[np.uint8]


def fixture(empty: bool = False) -> Fixture:
    counts = np.array([] if empty else [360, 0, 1, -2, 3, 360, -1, -1], dtype=np.int32)
    original = Connectome(
        np.arange(6, dtype=np.int64),
        np.array([] if empty else [0, 0, 0, 1, 2, 3, 4, 4], dtype=np.int32),
        np.array([] if empty else [1, 1, 0, 2, 3, 0, 5, 5], dtype=np.int32),
        counts,
        counts.astype(np.float64) * 0.275,
    )
    targets = () if empty else (0, 0, 1)
    events = np.zeros((4, 101, len(targets)), dtype=np.uint8)
    if targets:
        for trial in range(4):
            events[trial, trial::3, 0] = 1
            events[trial, trial::7, 1] = 1
            events[trial, trial::4, 2] = 1
    return Fixture(original, targets, events)


def initial(network: core.Network, trials: int) -> core.State:
    return core.initial_state(
        network,
        trials,
        voltage_mv=(-52, -52, -44, -44, -44, -52),
        synaptic_mv=(0, 0, 100, 0, 0, 0),
    )


def observed(case: Fixture, precision: str, block_size: int) -> list[MLXBlock]:
    execution = prepare(case.connectome, case.targets, (3,), precision)
    trials = case.events.shape[0]
    return list(
        observe(
            execution,
            initial(execution.network, trials),
            case.events,
            EventLedger(case.connectome, case.targets, trials),
            block_size,
        )
    )


def stock(case: Fixture, precision: str) -> dict[str, HostArray]:
    execution = prepare(case.connectome, case.targets, (3,), precision)
    state = initial(execution.network, case.events.shape[0])
    rows: dict[str, list[mx.array]] = {}
    for step in range(case.events.shape[1]):
        with mx.stream(mx.gpu):
            inputs = boolean_input(case.events[:, step, :].astype(np.bool_))
            state, trace = execution.advance(state, inputs)
            evaluate(*state[:-1], trace.spikes)
        for name, value in (
            ('pre_v', trace.pre_voltage_mv),
            ('pre_g', trace.pre_synaptic_mv),
            ('pre_not_refractory', trace.available),
            ('spikes', trace.spikes),
            ('before_v', trace.before_reset_voltage_mv),
            ('before_g', trace.before_reset_synaptic_mv),
            ('before_not_refractory', trace.receiving),
            ('end_v', state.voltage_mv),
            ('end_g', state.synaptic_mv),
            ('end_last_spike_step', state.last_spike_step),
            ('end_not_refractory', trace.receiving),
            ('accepted_inputs', trace.accepted_inputs),
            ('due', trace.due),
        ):
            rows.setdefault(name, []).append(value)
        rows.setdefault('queue', []).append(state.queue)
    with mx.stream(mx.gpu):
        arrays = {name: mx.stack(values) for name, values in rows.items()}
        evaluate(*arrays.values())
        return {name: as_host(value) for name, value in arrays.items()}


@pytest.mark.parametrize('block_size', [1, 17, 32])
@pytest.mark.parametrize('empty', [False, True])
def test_bounded_observation_preserves_every_ordinary_phase_and_queue_byte(
    precision: str, block_size: int, empty: bool, request: pytest.FixtureRequest
) -> None:
    case = fixture(empty)
    expected = stock(case, precision)
    blocks = observed(case, precision, block_size)
    assert sum(block.rows for block in blocks) == 101
    assert blocks[-1].rows == (101 % block_size or block_size)
    actual = {
        name: np.concatenate([block.fields[name] for block in blocks])
        for name in blocks[0].fields
    }
    for name, value in actual.items():
        assert (value.dtype, value.shape, value.tobytes()) == (
            expected[name].dtype,
            expected[name].shape,
            expected[name].tobytes(),
        ), name
    for block in blocks:
        assert block.checks.shape == (block.rows, 4, 30) and block.checks.all()
        queues = expected['queue'][block.begin + block.rows - 1]
        assert block.queue_sha256 == tuple(
            hashlib.sha256(queues[:, trial].tobytes()).hexdigest() for trial in range(4)
        )
        assert (block.final_queue is not None) == (block is blocks[-1])
        for row, trials in enumerate(block.due_edges):
            for trial, edges in enumerate(trials):
                assert np.array_equal(
                    edges,
                    np.flatnonzero(expected['due'][block.begin + row, trial]),
                )
                assert (
                    block.due_sha256[row][trial]
                    == hashlib.sha256(
                        expected['due'][block.begin + row, trial].tobytes()
                    ).hexdigest()
                )
    final = blocks[-1].final_queue
    assert final is not None and final.tobytes() == expected['queue'][-1].tobytes()
    destination = cast(str | None, request.config.getoption('--artifact-output'))
    if destination is not None:
        output = Path(destination)
        output.mkdir(parents=True, exist_ok=True)
        with (output / f'mlx-observer-{empty}-{block_size}.npz').open('xb') as artifact:
            np.savez_compressed(
                artifact,
                **{f'observed_{name}': value for name, value in actual.items()},
                **{f'stock_{name}': value for name, value in expected.items()},
                events=case.events,
                checks=np.concatenate([block.checks for block in blocks]),
                final_queue=final,
            )


def test_observed_state_and_physical_queues_repeat_bit_for_bit(precision: str) -> None:
    case = fixture()
    batch = observed(case, precision, 32)
    repeat = observed(case, precision, 32)
    for first, second in zip(batch, repeat, strict=True):
        assert (first.begin, first.rows, first.queue_sha256) == (
            second.begin,
            second.rows,
            second.queue_sha256,
        )
        assert first.checks.tobytes() == second.checks.tobytes()
        assert first.due_sha256 == second.due_sha256
        for a, b in zip(first.due_edges, second.due_edges, strict=True):
            assert tuple(edges.tobytes() for edges in a) == tuple(
                edges.tobytes() for edges in b
            )
        for name in first.fields:
            assert first.fields[name].tobytes() == second.fields[name].tobytes(), name
    first_final = batch[-1].final_queue
    repeated_final = repeat[-1].final_queue
    assert first_final is not None and repeated_final is not None
    assert first_final.tobytes() == repeated_final.tobytes()


def test_observed_batched_trials_match_independent_execution(precision: str) -> None:
    case = fixture()
    batch = observed(case, precision, 32)
    for trial in range(4):
        single = observed(
            Fixture(case.connectome, case.targets, case.events[trial : trial + 1]),
            precision,
            32,
        )
        for one, many in zip(single, batch, strict=True):
            assert one.queue_sha256 == (many.queue_sha256[trial],)
            assert one.checks.tobytes() == many.checks[:, trial : trial + 1].tobytes()
            for a, b in zip(one.due_edges, many.due_edges, strict=True):
                assert a[0].tobytes() == b[trial].tobytes()
            for a, b in zip(one.due_sha256, many.due_sha256, strict=True):
                assert a[0] == b[trial]
            for name, value in one.fields.items():
                assert (
                    value.tobytes() == many.fields[name][:, trial : trial + 1].tobytes()
                ), (trial, name)
        final = single[-1].final_queue
        batched_final = batch[-1].final_queue
        assert final is not None and batched_final is not None
        assert final.tobytes() == batched_final[:, trial : trial + 1].tobytes()


@pytest.mark.parametrize('block_size', [0, 33])
def test_observer_refuses_unbounded_or_empty_capture_blocks(
    precision: str, block_size: int
) -> None:
    with pytest.raises(ValueError, match='1 to 32'):
        observed(fixture(True), precision, block_size)
