import hashlib
from collections.abc import Generator

import mlx.core as mx
import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.adapters.mlx_ledger import EventLedger
from fly_brain.qualification.adapters.mlx_observer import observe, phase_fields
from fly_brain.qualification.ports import (
    ObservationSession,
    ObservationSessionFactory,
)
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.backend import core
from fly_brain.simulation.backend.arrays import as_host, boolean_input, evaluate
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.backend.engines import Advance, Execution
from fly_brain.simulation.models import Connectome, Stimulus
from fly_brain.simulation.observation_module import build_observation_sessions
from fly_brain.simulation.observations import (
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationInitialState,
    ObservationOperands,
    PhysicalQueueObservation,
)
from tests.support.session_proof_recorder import Recorder
from tests.support.session_proof_values import Frame


class RecordingSession:
    def __init__(self, session: ObservationSession, recorder: Recorder) -> None:
        self.session = session
        self.recorder = recorder
        self.completed_steps = 0

    @property
    def configuration(self) -> ObservationConfiguration:
        result = self.session.configuration
        self.recorder.sample('actual-configuration', result.initial_step)
        return result

    def advance(self, events: NDArray[np.bool_]) -> NativeObservation:
        result = self.session.advance(events)
        self.completed_steps = result.completed_steps
        self.recorder.sample('actual-advance-return', result.completed_steps)
        return result

    def compare(self, operands: ObservationOperands) -> NativeComparison:
        self.recorder.sample(
            'independent-operands-before-comparison', self.completed_steps
        )
        result = self.session.compare(operands)
        self.recorder.sample('actual-comparison-return', result.completed_steps)
        return result

    def physical_queue(self) -> PhysicalQueueObservation:
        result = self.session.physical_queue()
        self.recorder.queue(result.completed_steps, result.queue)
        return result


class RecordingFactory:
    def __init__(self, factory: ObservationSessionFactory, recorder: Recorder) -> None:
        self.factory = factory
        self.recorder = recorder

    def __call__(
        self,
        trial_indices: tuple[int, ...],
        initial: ObservationInitialState | None = None,
    ) -> ObservationSession:
        return RecordingSession(self.factory(trial_indices, initial), self.recorder)


class LatestNativeState:
    def __init__(self, advance: Advance) -> None:
        self.advance = advance
        self.state: core.State | None = None

    def __call__(
        self, state: core.State, events: mx.array
    ) -> tuple[core.State, core.StepTrace]:
        updated, trace = self.advance(state, events)
        self.state = updated
        return updated, trace


def ordinary_frames(
    connectome: Connectome, stimulus: Stimulus, recorder: Recorder, precision: str
) -> Generator[Frame, None, None]:
    execution = prepare(connectome, stimulus.targets, (), precision)
    state = core.initial_state(execution.network, len(stimulus.trial_indices))
    for begin in range(0, stimulus.events.shape[1], 32):
        end = min(begin + 32, stimulus.events.shape[1])
        rows: dict[str, list[mx.array]] = {}
        identities: list[tuple[NDArray[np.int32], ...]] = []
        hashes: list[tuple[str, ...]] = []
        for step in range(begin, end):
            with mx.stream(mx.gpu):
                inputs = boolean_input(stimulus.events[:, step].astype(np.bool_))
                state, trace = execution.advance(state, inputs)
                evaluate(*state[:-1], trace.spikes)
                due = np.asarray(trace.due, dtype=np.bool_)
                identities.append(
                    tuple(np.flatnonzero(value).astype(np.int32) for value in due)
                )
                hashes.append(
                    tuple(
                        hashlib.sha256(memoryview(value)).hexdigest() for value in due
                    )
                )
                del due
            for name, value in phase_fields(state, trace).items():
                rows.setdefault(name, []).append(value)
        with mx.stream(mx.gpu):
            arrays = {name: mx.stack(values) for name, values in rows.items()}
            evaluate(*arrays.values())
            fields = {name: as_host(value) for name, value in arrays.items()}
            queue = np.asarray(state.queue, dtype=np.bool_)
        recorder.queue(end, queue)
        yield Frame(begin, end - begin, fields, None, tuple(identities), tuple(hashes))
        del fields, arrays, rows, queue


def legacy_frames(
    connectome: Connectome, stimulus: Stimulus, recorder: Recorder, precision: str
) -> Generator[Frame, None, None]:
    original = prepare(connectome, stimulus.targets, (), precision)
    tap = LatestNativeState(original.advance)
    execution = Execution(original.network, tap)
    state = core.initial_state(execution.network, len(stimulus.trial_indices))
    blocks = observe(
        execution,
        state,
        stimulus.events,
        EventLedger(connectome, stimulus.targets, len(stimulus.trial_indices)),
        32,
    )
    for block in blocks:
        if tap.state is None:
            raise ValueError('Legacy observer did not produce actual native state')
        recorder.queue(
            block.begin + block.rows, np.asarray(tap.state.queue, dtype=np.bool_)
        )
        yield Frame(
            block.begin,
            block.rows,
            block.fields,
            block.checks,
            block.due_edges,
            block.due_sha256,
        )
        del block


def session_frames(
    connectome: Connectome, stimulus: Stimulus, recorder: Recorder, precision: str
) -> Generator[Frame, None, None]:
    original, _ = build_observation_sessions(
        connectome, stimulus.targets, (), precision
    )
    factory = RecordingFactory(original, recorder)
    blocks = observe_session(
        factory,
        connectome,
        stimulus.targets,
        stimulus.trial_indices,
        stimulus.events,
        block_size=32,
    )
    for block in blocks:
        yield Frame(
            block.begin,
            block.rows,
            block.fields,
            block.checks,
            block.due_edges,
            block.due_sha256,
        )
        del block
