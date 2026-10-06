import hashlib
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.models import Connectome
from fly_brain.simulation.observations import (
    HostSnapshot,
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationInitialState,
    ObservationOperands,
    PhysicalQueueObservation,
)

CHECK_NAMES = (
    'available',
    'threshold',
    'receiving',
    'due',
    'accepted',
    'discarded',
    'accepted_inputs',
    'last_spike_step',
    'finite_pre',
    'finite_before',
    'finite_end',
    *(f'queue-slot-{slot}' for slot in range(19)),
)


def capture_history(
    history: tuple[NDArray[np.bool_], ...],
) -> tuple[HostSnapshot[np.bool_], ...]:
    return tuple(HostSnapshot.capture(value) for value in history)


@dataclass(frozen=True, init=False)
class LedgerState:
    step: int
    _last_spike_step_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _refractory_steps_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _history_snapshot: tuple[HostSnapshot[np.bool_], ...] = field(
        init=False, repr=False
    )

    def __init__(
        self,
        step: int,
        last_spike_step: NDArray[np.int32],
        refractory_steps: NDArray[np.int32],
        history: tuple[NDArray[np.bool_], ...],
    ) -> None:
        shape = last_spike_step.shape
        if (
            last_spike_step.dtype != np.int32
            or len(shape) != 2
            or refractory_steps.dtype != np.int32
            or refractory_steps.shape != (shape[1],)
            or len(history) != 19
            or any(value.dtype != np.bool_ or value.shape != shape for value in history)
        ):
            raise ValueError(
                'Qualification history requires every trial, neuron and slot'
            )
        object.__setattr__(self, 'step', step)
        object.__setattr__(
            self, '_last_spike_step_snapshot', HostSnapshot.capture(last_spike_step)
        )
        object.__setattr__(
            self, '_refractory_steps_snapshot', HostSnapshot.capture(refractory_steps)
        )
        object.__setattr__(self, '_history_snapshot', capture_history(history))

    @property
    def last_spike_step(self) -> NDArray[np.int32]:
        return self._last_spike_step_snapshot.array

    @property
    def refractory_steps(self) -> NDArray[np.int32]:
        return self._refractory_steps_snapshot.array

    @property
    def history(self) -> tuple[NDArray[np.bool_], ...]:
        return tuple(value.array for value in self._history_snapshot)


def initial_ledger(
    connectome: Connectome,
    targets: tuple[int, ...],
    trials: int,
    initial: ObservationInitialState | None,
) -> LedgerState:
    shape = (trials, connectome.neuron_ids.size)
    last = (
        np.full(shape, -100000000, dtype=np.int32)
        if initial is None
        else initial.last_spike_step
    )
    refractory = np.full(shape[1], 22, dtype=np.int32)
    refractory[list(targets)] = 0
    empty = np.zeros(shape, dtype=np.bool_)
    return LedgerState(0, last, refractory, (empty,) * 19)


def require_configuration(
    actual: ObservationConfiguration,
    connectome: Connectome,
    targets: tuple[int, ...],
    trial_indices: tuple[int, ...],
    initial: ObservationInitialState | None,
    ledger: LedgerState,
) -> None:
    shape = ledger.last_spike_step.shape
    voltage = (
        np.full(shape, -52, dtype=np.float32)
        if initial is None
        else initial.voltage_mv.astype(np.float32)
    )
    synaptic = (
        np.zeros(shape, dtype=np.float32)
        if initial is None
        else initial.synaptic_mv.astype(np.float32)
    )
    arrays = (
        (actual.sources, connectome.sources),
        (actual.destinations, connectome.destinations),
        (actual.targets, np.asarray(targets, dtype=np.int32)),
        (actual.refractory_steps, ledger.refractory_steps),
        (actual.initial_last_spike_step, ledger.last_spike_step),
        (actual.initial_voltage_mv, voltage),
        (actual.initial_synaptic_mv, synaptic),
    )
    if (
        actual.neurons != shape[1]
        or actual.queue_slots != 19
        or actual.initial_step != 0
        or actual.trial_indices != trial_indices
        or any(
            (a.dtype, a.shape, a.tobytes()) != (b.dtype, b.shape, b.tobytes())
            for a, b in arrays
        )
    ):
        raise ValueError(
            'Actual session configuration differs from independent pinned inputs'
        )


def expect_step(
    ledger: LedgerState,
    actual: NativeObservation,
    events: NDArray[np.bool_],
    connectome: Connectome,
    targets: tuple[int, ...],
) -> tuple[LedgerState, ObservationOperands]:
    step = ledger.step
    if (
        actual.completed_steps != step + 1
        or actual.fields['pre_v'].shape != ledger.last_spike_step.shape
    ):
        raise ValueError('Native observation step or clock is out of order')
    if (
        events.dtype != np.bool_
        or events.shape != (ledger.last_spike_step.shape[0], len(targets))
        or actual.fields['accepted_inputs'].shape != events.shape
    ):
        raise ValueError('Qualification events have incomplete trial/channel coverage')
    available = step - ledger.last_spike_step >= ledger.refractory_steps
    spikes = available & (actual.fields['pre_v'] > np.float32(-45))
    receiving = available & ~spikes
    empty = np.zeros_like(spikes)
    due_sources = ledger.history[(step - 18) % 19] if step >= 18 else empty
    last = np.where(spikes, np.int32(step), ledger.last_spike_step)
    history = list(ledger.history)
    history[step % 19] = spikes
    pending: list[NDArray[np.bool_]] = []
    for slot in range(19):
        due_step = step + 1 + (slot - step - 1) % 19
        source_step = due_step - 18
        pending.append(history[source_step % 19] if 0 <= source_step <= step else empty)
    operands = ObservationOperands(
        connectome.sources,
        connectome.destinations,
        available,
        spikes,
        receiving,
        due_sources,
        receiving,
        ~receiving,
        events & receiving[:, np.asarray(targets, dtype=np.int32)],
        last,
        np.stack(pending),
    )
    return LedgerState(
        step + 1, last, ledger.refractory_steps, tuple(history)
    ), operands


def observation_checks(
    actual: NativeObservation,
    comparison: NativeComparison,
    operands: ObservationOperands,
) -> NDArray[np.bool_]:
    if (
        comparison.completed_steps != actual.completed_steps
        or comparison.trial_indices != actual.trial_indices
        or comparison.queue_equal.shape != (len(actual.trial_indices), 19)
    ):
        raise ValueError(
            'Actual comparison has missing, reordered or incomplete evidence'
        )
    gates = comparison.gates_equal.copy()
    for column, expected, names in (
        (0, operands.available, ('pre_not_refractory',)),
        (1, operands.spikes, ('spikes',)),
        (2, operands.receiving, ('before_not_refractory', 'end_not_refractory')),
        (6, operands.accepted_inputs, ('accepted_inputs',)),
        (7, operands.last_spike_step, ('end_last_spike_step',)),
    ):
        for name in names:
            gates[:, column] &= np.all(actual.fields[name] == expected, axis=1)
    due = operands.due_sources[:, operands.sources]
    for trial, value in enumerate(due):
        gates[trial, 3] &= (
            np.array_equal(
                actual.due_edges[trial], np.flatnonzero(value).astype(np.int32)
            )
            and actual.due_sha256[trial] == hashlib.sha256(value.tobytes()).hexdigest()
        )
    finite = np.stack(
        [
            np.all(
                np.isfinite(actual.fields[phase + '_v'])
                & np.isfinite(actual.fields[phase + '_g']),
                axis=1,
            )
            for phase in ('pre', 'before', 'end')
        ],
        axis=1,
    )
    return np.concatenate((gates, finite, comparison.queue_equal), axis=1)


def require_physical_queue(
    actual: PhysicalQueueObservation,
    operands: ObservationOperands,
    completed_steps: int,
    trial_indices: tuple[int, ...],
) -> None:
    if (
        actual.completed_steps != completed_steps
        or actual.trial_indices != trial_indices
        or actual.queue.shape != (19, len(trial_indices), operands.sources.size)
    ):
        raise ValueError('Actual physical queue has incomplete boundary coverage')
    for slot in range(19):
        for trial in range(len(trial_indices)):
            expected = operands.pending_sources[slot, trial, operands.sources]
            if not np.array_equal(actual.queue[slot, trial], expected):
                raise ValueError(
                    'Actual boundary physical queue differs from independent history'
                )
