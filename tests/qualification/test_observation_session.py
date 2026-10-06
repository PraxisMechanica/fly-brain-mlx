import hashlib
from pathlib import Path
from typing import cast

import numpy as np
import pytest

from fly_brain.qualification.ports import ObservationSessionFactory
from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.qualification.session_expectations import (
    CHECK_NAMES,
    expect_step,
    initial_ledger,
    observation_checks,
    require_configuration,
)
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.models import Connectome
from fly_brain.simulation.observation_module import build_observation_sessions
from fly_brain.simulation.observations import ObservationInitialState
from tests.qualification.test_mlx_observer import Fixture, fixture, observed, stock

pytestmark = [pytest.mark.integration, pytest.mark.metal]


def initial(case: Fixture) -> ObservationInitialState:
    shape = (case.events.shape[0], 6)
    return ObservationInitialState(
        np.broadcast_to(
            np.array([-52, -52, -44, -44, -44, -52], dtype=np.float64), shape
        ),
        np.broadcast_to(np.array([0, 0, 100, 0, 0, 0], dtype=np.float64), shape),
        np.full(shape, -100000000, dtype=np.int32),
    )


def session_blocks(
    case: Fixture, precision: str, block_size: int
) -> list[SessionBlock]:
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (3,), precision
    )
    consumer: ObservationSessionFactory = factory
    return list(
        observe_session(
            consumer,
            case.connectome,
            case.targets,
            tuple(range(case.events.shape[0])),
            case.events,
            initial(case),
            block_size,
        )
    )


@pytest.mark.parametrize('block_size', (1, 17, 32))
@pytest.mark.parametrize('empty', (False, True))
def test_opaque_sessions_preserve_ordinary_legacy_and_repeat_native_bytes(
    precision: str,
    block_size: int,
    empty: bool,
    request: pytest.FixtureRequest,
) -> None:
    case = fixture(empty)
    ordinary = stock(case, precision)
    legacy = observed(case, precision, block_size)
    actual = session_blocks(case, precision, block_size)
    repeat = session_blocks(case, precision, block_size)
    assert sum(block.rows for block in actual) == 101
    for old, new, repeated in zip(legacy, actual, repeat, strict=True):
        assert (new.begin, new.rows, new.queue_sha256, new.due_sha256) == (
            old.begin,
            old.rows,
            old.queue_sha256,
            old.due_sha256,
        )
        assert new.checks.shape == (new.rows, 4, len(CHECK_NAMES)) and new.checks.all()
        assert new.checks.tobytes() == old.checks.tobytes() == repeated.checks.tobytes()
        assert new.queue_sha256 == repeated.queue_sha256
        assert new.queue_slot_sha256 == repeated.queue_slot_sha256
        for name, value in new.fields.items():
            expected = ordinary[name][new.begin : new.begin + new.rows]
            assert (value.dtype, value.shape, value.tobytes()) == (
                expected.dtype,
                expected.shape,
                expected.tobytes(),
            ), name
            assert (
                value.tobytes()
                == old.fields[name].tobytes()
                == repeated.fields[name].tobytes()
            ), name
            with pytest.raises(ValueError):
                value.setflags(write=True)
        queues = ordinary['queue'][new.begin + new.rows - 1]
        assert new.queue_slot_sha256 == tuple(
            tuple(
                hashlib.sha256(queues[slot, trial].tobytes()).hexdigest()
                for slot in range(19)
            )
            for trial in range(4)
        )
        for new_row, old_row, repeated_row in zip(
            new.due_edges, old.due_edges, repeated.due_edges, strict=True
        ):
            assert (
                tuple(value.tobytes() for value in new_row)
                == tuple(value.tobytes() for value in old_row)
                == tuple(value.tobytes() for value in repeated_row)
            )
    final = actual[-1].final_queue
    repeated_final = repeat[-1].final_queue
    assert final is not None and repeated_final is not None
    assert (
        final.tobytes() == ordinary['queue'][-1].tobytes() == repeated_final.tobytes()
    )
    destination = cast(str | None, request.config.getoption('--artifact-output'))
    if destination is not None:
        output = Path(destination)
        output.mkdir(parents=True, exist_ok=True)
        with (output / f'session-transparency-{empty}-{block_size}.npz').open(
            'xb'
        ) as artifact:
            np.savez_compressed(
                artifact,
                **{f'ordinary_{name}': value for name, value in ordinary.items()},
                **{
                    f'new_{name}': np.concatenate(
                        [block.fields[name] for block in actual]
                    )
                    for name in actual[0].fields
                },
                final_queue=final,
                checks=np.concatenate([block.checks for block in actual]),
                events=case.events,
            )


def test_real_four_trial_sessions_match_fresh_singletons(precision: str) -> None:
    case = fixture()
    batch = session_blocks(case, precision, 32)
    for trial in range(4):
        single_case = Fixture(
            case.connectome, case.targets, case.events[trial : trial + 1]
        )
        singles = session_blocks(single_case, precision, 32)
        for many, one in zip(batch, singles, strict=True):
            assert one.checks.tobytes() == many.checks[:, trial : trial + 1].tobytes()
            assert one.queue_sha256 == (many.queue_sha256[trial],)
            assert one.queue_slot_sha256 == (many.queue_slot_sha256[trial],)
            for name, value in one.fields.items():
                assert (
                    value.tobytes() == many.fields[name][:, trial : trial + 1].tobytes()
                )
            assert one.due_sha256 == tuple((row[trial],) for row in many.due_sha256)
            assert tuple(row[0].tobytes() for row in one.due_edges) == tuple(
                row[trial].tobytes() for row in many.due_edges
            )
        final = singles[-1].final_queue
        batch_final = batch[-1].final_queue
        assert final is not None and batch_final is not None
        assert final.tobytes() == batch_final[:, trial : trial + 1].tobytes()


@pytest.mark.parametrize('chunks', ((101,), (1, 17, 32, 51), (18, 1, 19, 63)))
def test_session_chunk_continuation_preserves_native_phases_due_and_all_queues(
    precision: str,
    chunks: tuple[int, ...],
) -> None:
    case = fixture()
    ordinary = stock(case, precision)
    factory, _ = build_observation_sessions(
        case.connectome, case.targets, (3,), precision
    )
    session = factory((0, 1, 2, 3), initial(case))
    ledger = initial_ledger(case.connectome, case.targets, 4, initial(case))
    require_configuration(
        session.configuration,
        case.connectome,
        case.targets,
        (0, 1, 2, 3),
        initial(case),
        ledger,
    )
    saved: dict[str, bytes] | None = None
    saved_fields = None
    offset = 0
    for length in chunks:
        for step in range(offset, offset + length):
            inputs = case.events[:, step].astype(np.bool_)
            actual = session.advance(inputs)
            ledger, operands = expect_step(
                ledger, actual, inputs, case.connectome, case.targets
            )
            assert observation_checks(actual, session.compare(operands), operands).all()
            for name, value in actual.fields.items():
                assert value.tobytes() == ordinary[name][step].tobytes(), (step, name)
            queue = session.physical_queue()
            assert queue.queue.tobytes() == ordinary['queue'][step].tobytes()
            if saved is None:
                saved = {name: value.tobytes() for name, value in actual.fields.items()}
                saved_fields = actual.fields
        offset += length
    assert offset == 101
    assert saved is not None and saved_fields is not None
    assert saved == {name: value.tobytes() for name, value in saved_fields.items()}
    assert session.physical_queue().queue.tobytes() == ordinary['queue'][-1].tobytes()


def test_observation_factory_keeps_actual_reduction_rows_unchanged(
    precision: str,
) -> None:
    from fly_brain.simulation.backend.bucketed import prepare_observed

    case = fixture()
    _, old_reader = prepare_observed(case.connectome, case.targets, (3,), precision)
    _, new_reader = build_observation_sessions(
        case.connectome, case.targets, (3,), precision
    )
    expected, actual = old_reader(tuple(range(6))), new_reader(tuple(range(6)))
    assert expected.order == actual.order
    for old, new in zip(expected.rows, actual.rows, strict=True):
        assert old.neuron == new.neuron
        for a, b in (
            (old.edges, new.edges),
            (old.counts, new.counts),
            (old.occupied, new.occupied),
        ):
            assert (a.dtype, a.shape, a.tobytes()) == (b.dtype, b.shape, b.tobytes())


def test_actual_native_threshold_equality_and_neighbors_match_independent_predicates(
    precision: str,
) -> None:
    from fly_brain.simulation.backend.core import COEFFICIENTS

    network = Connectome(
        np.array([0], dtype=np.int64),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    threshold = np.float32(-45)
    wanted = np.array(
        [
            np.nextafter(threshold, np.float32(-np.inf)),
            threshold,
            np.nextafter(threshold, np.float32(np.inf)),
        ],
        dtype=np.float32,
    ).reshape(3, 1)
    voltage = -52 + (wanted.astype(np.float64) + 52) / COEFFICIENTS[0]
    starting = ObservationInitialState(
        voltage,
        np.zeros((3, 1), dtype=np.float64),
        np.full((3, 1), -100000000, dtype=np.int32),
    )
    factory, _ = build_observation_sessions(network, (0,), (), precision)
    session = factory((0, 1, 2), starting)
    inputs = np.zeros((3, 1), dtype=np.bool_)
    actual = session.advance(inputs)
    assert actual.fields['pre_v'].tobytes() == wanted.tobytes()
    state, operands = expect_step(
        initial_ledger(network, (0,), 3, starting), actual, inputs, network, (0,)
    )
    assert operands.spikes.tolist() == [[False], [False], [True]]
    assert state.history[0].tolist() == [[False], [False], [True]]
    assert observation_checks(actual, session.compare(operands), operands).all()
