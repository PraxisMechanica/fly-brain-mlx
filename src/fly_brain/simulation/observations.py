import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Generic, TypeVar

import numpy as np
from numpy.typing import NDArray

HostArray = NDArray[np.float32 | np.float64 | np.int32 | np.int64 | np.bool_]
Scalar = TypeVar('Scalar', bound=np.generic, covariant=True)
SnapshotScalar = TypeVar('SnapshotScalar', bound=np.generic)
COMPENSATED_ORDER = 'Actual padded leaf order; adjacent-pair compensated integer-count tree; four high/low scale products; 16-leaf compensated final tree.'
EXACT_ORDER = 'Actual padded leaf order; leaf-axis float32 exact integer-count sum; four high/low scale products; 16-leaf compensated final tree.'


@dataclass(frozen=True)
class HostSnapshot(Generic[Scalar]):
    payload: bytes
    dtype: np.dtype[Scalar]
    shape: tuple[int, ...]

    @staticmethod
    def capture(values: NDArray[SnapshotScalar]) -> 'HostSnapshot[SnapshotScalar]':
        return HostSnapshot(values.tobytes(order='C'), values.dtype, values.shape)

    @property
    def array(self) -> NDArray[Scalar]:
        return np.ndarray(self.shape, dtype=self.dtype, buffer=self.payload)


@dataclass(frozen=True)
class HostFieldSnapshots:
    snapshots: tuple[
        tuple[
            str, HostSnapshot[np.float32 | np.float64 | np.int32 | np.int64 | np.bool_]
        ],
        ...,
    ]

    @classmethod
    def capture(cls, fields: Mapping[str, HostArray]) -> 'HostFieldSnapshots':
        return cls(
            tuple((name, HostSnapshot.capture(value)) for name, value in fields.items())
        )

    @property
    def fields(self) -> Mapping[str, HostArray]:
        return MappingProxyType({name: value.array for name, value in self.snapshots})


def capture_edges(
    edges: tuple[NDArray[np.int32], ...],
) -> tuple[HostSnapshot[np.int32], ...]:
    return tuple(HostSnapshot.capture(value) for value in edges)


@dataclass(frozen=True, init=False)
class ReductionRow:
    neuron: int
    _edges_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _counts_snapshot: HostSnapshot[np.float32] = field(init=False, repr=False)
    _occupied_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)

    def __init__(
        self,
        neuron: int,
        edges: NDArray[np.int32],
        counts: NDArray[np.float32],
        occupied: NDArray[np.bool_],
    ) -> None:
        if (
            edges.dtype != np.int32
            or counts.dtype != np.float32
            or occupied.dtype != np.bool_
            or edges.ndim != 1
            or edges.shape != counts.shape
            or edges.shape != occupied.shape
        ):
            raise ValueError(
                'Reduction rows require equal native one-dimensional fields'
            )
        object.__setattr__(self, 'neuron', neuron)
        object.__setattr__(self, '_edges_snapshot', HostSnapshot.capture(edges))
        object.__setattr__(self, '_counts_snapshot', HostSnapshot.capture(counts))
        object.__setattr__(self, '_occupied_snapshot', HostSnapshot.capture(occupied))

    @property
    def edges(self) -> NDArray[np.int32]:
        return self._edges_snapshot.array

    @property
    def counts(self) -> NDArray[np.float32]:
        return self._counts_snapshot.array

    @property
    def occupied(self) -> NDArray[np.bool_]:
        return self._occupied_snapshot.array


@dataclass(frozen=True)
class ReductionEvidence:
    rows: tuple[ReductionRow, ...]
    order: str


ReductionReader = Callable[[tuple[int, ...]], ReductionEvidence]

PHASE_DTYPES = MappingProxyType(
    {
        'pre_v': np.dtype(np.float32),
        'pre_g': np.dtype(np.float32),
        'pre_not_refractory': np.dtype(np.bool_),
        'spikes': np.dtype(np.bool_),
        'before_v': np.dtype(np.float32),
        'before_g': np.dtype(np.float32),
        'before_not_refractory': np.dtype(np.bool_),
        'end_v': np.dtype(np.float32),
        'end_g': np.dtype(np.float32),
        'end_last_spike_step': np.dtype(np.int32),
        'end_not_refractory': np.dtype(np.bool_),
        'accepted_inputs': np.dtype(np.bool_),
    }
)
PHASE_UNITS = MappingProxyType(
    {
        name: 'mV'
        if dtype == np.dtype(np.float32)
        else 'steps'
        if dtype == np.dtype(np.int32)
        else 'Boolean'
        for name, dtype in PHASE_DTYPES.items()
    }
)


@dataclass(frozen=True, init=False)
class ObservationInitialState:
    _voltage_mv_snapshot: HostSnapshot[np.float64] = field(init=False, repr=False)
    _synaptic_mv_snapshot: HostSnapshot[np.float64] = field(init=False, repr=False)
    _last_spike_step_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)

    def __init__(
        self,
        voltage_mv: NDArray[np.float64],
        synaptic_mv: NDArray[np.float64],
        last_spike_step: NDArray[np.int32],
    ) -> None:
        if (
            voltage_mv.dtype != np.float64
            or synaptic_mv.dtype != np.float64
            or last_spike_step.dtype != np.int32
            or voltage_mv.ndim != 2
            or synaptic_mv.shape != voltage_mv.shape
            or last_spike_step.shape != voltage_mv.shape
        ):
            raise ValueError(
                'Initial observation fields require equal trial/neuron shapes'
            )
        object.__setattr__(
            self, '_voltage_mv_snapshot', HostSnapshot.capture(voltage_mv)
        )
        object.__setattr__(
            self, '_synaptic_mv_snapshot', HostSnapshot.capture(synaptic_mv)
        )
        object.__setattr__(
            self, '_last_spike_step_snapshot', HostSnapshot.capture(last_spike_step)
        )

    @property
    def voltage_mv(self) -> NDArray[np.float64]:
        return self._voltage_mv_snapshot.array

    @property
    def synaptic_mv(self) -> NDArray[np.float64]:
        return self._synaptic_mv_snapshot.array

    @property
    def last_spike_step(self) -> NDArray[np.int32]:
        return self._last_spike_step_snapshot.array


@dataclass(frozen=True, init=False)
class ObservationConfiguration:
    neurons: int
    queue_slots: int
    initial_step: int
    trial_indices: tuple[int, ...]
    _sources_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _destinations_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _targets_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _refractory_steps_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _initial_voltage_mv_snapshot: HostSnapshot[np.float32] = field(
        init=False, repr=False
    )
    _initial_synaptic_mv_snapshot: HostSnapshot[np.float32] = field(
        init=False, repr=False
    )
    _initial_last_spike_step_snapshot: HostSnapshot[np.int32] = field(
        init=False, repr=False
    )

    def __init__(
        self,
        neurons: int,
        queue_slots: int,
        initial_step: int,
        trial_indices: tuple[int, ...],
        sources: NDArray[np.int32],
        destinations: NDArray[np.int32],
        targets: NDArray[np.int32],
        refractory_steps: NDArray[np.int32],
        initial_voltage_mv: NDArray[np.float32],
        initial_synaptic_mv: NDArray[np.float32],
        initial_last_spike_step: NDArray[np.int32],
    ) -> None:
        for value in (sources, destinations, targets, refractory_steps):
            if value.dtype != np.int32 or value.ndim != 1:
                raise ValueError('Observation configuration requires native int32 maps')
        shape = (len(trial_indices), neurons)
        if (
            initial_voltage_mv.dtype != np.float32
            or initial_synaptic_mv.dtype != np.float32
            or initial_last_spike_step.dtype != np.int32
            or any(
                value.shape != shape
                for value in (
                    initial_voltage_mv,
                    initial_synaptic_mv,
                    initial_last_spike_step,
                )
            )
        ):
            raise ValueError('Initial native observation coverage differs')
        if sources.shape != destinations.shape or refractory_steps.shape != (neurons,):
            raise ValueError('Native observation map coverage differs')
        object.__setattr__(self, 'neurons', neurons)
        object.__setattr__(self, 'queue_slots', queue_slots)
        object.__setattr__(self, 'initial_step', initial_step)
        object.__setattr__(self, 'trial_indices', trial_indices)
        object.__setattr__(self, '_sources_snapshot', HostSnapshot.capture(sources))
        object.__setattr__(
            self, '_destinations_snapshot', HostSnapshot.capture(destinations)
        )
        object.__setattr__(self, '_targets_snapshot', HostSnapshot.capture(targets))
        object.__setattr__(
            self, '_refractory_steps_snapshot', HostSnapshot.capture(refractory_steps)
        )
        object.__setattr__(
            self,
            '_initial_voltage_mv_snapshot',
            HostSnapshot.capture(initial_voltage_mv),
        )
        object.__setattr__(
            self,
            '_initial_synaptic_mv_snapshot',
            HostSnapshot.capture(initial_synaptic_mv),
        )
        object.__setattr__(
            self,
            '_initial_last_spike_step_snapshot',
            HostSnapshot.capture(initial_last_spike_step),
        )

    @property
    def sources(self) -> NDArray[np.int32]:
        return self._sources_snapshot.array

    @property
    def destinations(self) -> NDArray[np.int32]:
        return self._destinations_snapshot.array

    @property
    def targets(self) -> NDArray[np.int32]:
        return self._targets_snapshot.array

    @property
    def refractory_steps(self) -> NDArray[np.int32]:
        return self._refractory_steps_snapshot.array

    @property
    def initial_voltage_mv(self) -> NDArray[np.float32]:
        return self._initial_voltage_mv_snapshot.array

    @property
    def initial_synaptic_mv(self) -> NDArray[np.float32]:
        return self._initial_synaptic_mv_snapshot.array

    @property
    def initial_last_spike_step(self) -> NDArray[np.int32]:
        return self._initial_last_spike_step_snapshot.array


@dataclass(frozen=True, init=False)
class NativeObservation:
    completed_steps: int
    trial_indices: tuple[int, ...]
    _fields_snapshot: HostFieldSnapshots = field(init=False, repr=False)
    _due_edges_snapshot: tuple[HostSnapshot[np.int32], ...] = field(
        init=False, repr=False
    )
    due_sha256: tuple[str, ...]

    def __init__(
        self,
        completed_steps: int,
        trial_indices: tuple[int, ...],
        fields: Mapping[str, HostArray],
        due_edges: tuple[NDArray[np.int32], ...],
        due_sha256: tuple[str, ...],
    ) -> None:
        if set(fields) != set(PHASE_DTYPES):
            raise ValueError('Native observation requires every actual phase field')
        shape = fields['pre_v'].shape
        if len(shape) != 2 or shape[0] != len(trial_indices):
            raise ValueError('Native observation trial/neuron coverage differs')
        for name, value in fields.items():
            if value.dtype != PHASE_DTYPES[name] or value.ndim != 2:
                raise ValueError('Native observation dtype or phase coverage differs')
            expected_shape = (
                shape if name != 'accepted_inputs' else (shape[0], value.shape[-1])
            )
            if value.shape != expected_shape:
                raise ValueError('Native observation dtype or phase coverage differs')
        if len(due_edges) != shape[0] or len(due_sha256) != shape[0]:
            raise ValueError('Native due observations require every trial')
        for edges in due_edges:
            if edges.dtype != np.int32 or edges.ndim != 1:
                raise ValueError('Native due identities require one-dimensional int32')
        object.__setattr__(self, 'completed_steps', completed_steps)
        object.__setattr__(self, 'trial_indices', trial_indices)
        object.__setattr__(self, '_fields_snapshot', HostFieldSnapshots.capture(fields))
        object.__setattr__(self, '_due_edges_snapshot', capture_edges(due_edges))
        object.__setattr__(self, 'due_sha256', due_sha256)

    @property
    def fields(self) -> Mapping[str, HostArray]:
        return self._fields_snapshot.fields

    @property
    def due_edges(self) -> tuple[NDArray[np.int32], ...]:
        return tuple(value.array for value in self._due_edges_snapshot)


@dataclass(frozen=True, init=False)
class ObservationOperands:
    _sources_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _destinations_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _available_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)
    _spikes_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)
    _receiving_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)
    _due_sources_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)
    _accepted_destinations_snapshot: HostSnapshot[np.bool_] = field(
        init=False, repr=False
    )
    _discarded_destinations_snapshot: HostSnapshot[np.bool_] = field(
        init=False, repr=False
    )
    _accepted_inputs_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)
    _last_spike_step_snapshot: HostSnapshot[np.int32] = field(init=False, repr=False)
    _pending_sources_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)

    def __init__(
        self,
        sources: NDArray[np.int32],
        destinations: NDArray[np.int32],
        available: NDArray[np.bool_],
        spikes: NDArray[np.bool_],
        receiving: NDArray[np.bool_],
        due_sources: NDArray[np.bool_],
        accepted_destinations: NDArray[np.bool_],
        discarded_destinations: NDArray[np.bool_],
        accepted_inputs: NDArray[np.bool_],
        last_spike_step: NDArray[np.int32],
        pending_sources: NDArray[np.bool_],
    ) -> None:
        shape = available.shape
        if len(shape) != 2:
            raise ValueError('Comparison operands require trial/neuron matrices')
        for value in (
            available,
            spikes,
            receiving,
            due_sources,
            accepted_destinations,
            discarded_destinations,
        ):
            if value.dtype != np.bool_ or value.shape != shape:
                raise ValueError('Comparison Boolean operands have different coverage')
        for value in (sources, destinations):
            if value.dtype != np.int32 or value.ndim != 1:
                raise ValueError('Comparison maps require native int32 identities')
        if (
            sources.shape != destinations.shape
            or accepted_inputs.dtype != np.bool_
            or accepted_inputs.ndim != 2
            or accepted_inputs.shape[0] != shape[0]
            or last_spike_step.dtype != np.int32
            or last_spike_step.shape != shape
            or pending_sources.dtype != np.bool_
            or pending_sources.ndim != 3
            or pending_sources.shape[1:] != shape
        ):
            raise ValueError(
                'Comparison input, clock or queue operands have different coverage'
            )
        object.__setattr__(self, '_sources_snapshot', HostSnapshot.capture(sources))
        object.__setattr__(
            self, '_destinations_snapshot', HostSnapshot.capture(destinations)
        )
        object.__setattr__(self, '_available_snapshot', HostSnapshot.capture(available))
        object.__setattr__(self, '_spikes_snapshot', HostSnapshot.capture(spikes))
        object.__setattr__(self, '_receiving_snapshot', HostSnapshot.capture(receiving))
        object.__setattr__(
            self, '_due_sources_snapshot', HostSnapshot.capture(due_sources)
        )
        object.__setattr__(
            self,
            '_accepted_destinations_snapshot',
            HostSnapshot.capture(accepted_destinations),
        )
        object.__setattr__(
            self,
            '_discarded_destinations_snapshot',
            HostSnapshot.capture(discarded_destinations),
        )
        object.__setattr__(
            self, '_accepted_inputs_snapshot', HostSnapshot.capture(accepted_inputs)
        )
        object.__setattr__(
            self, '_last_spike_step_snapshot', HostSnapshot.capture(last_spike_step)
        )
        object.__setattr__(
            self, '_pending_sources_snapshot', HostSnapshot.capture(pending_sources)
        )

    @property
    def sources(self) -> NDArray[np.int32]:
        return self._sources_snapshot.array

    @property
    def destinations(self) -> NDArray[np.int32]:
        return self._destinations_snapshot.array

    @property
    def available(self) -> NDArray[np.bool_]:
        return self._available_snapshot.array

    @property
    def spikes(self) -> NDArray[np.bool_]:
        return self._spikes_snapshot.array

    @property
    def receiving(self) -> NDArray[np.bool_]:
        return self._receiving_snapshot.array

    @property
    def due_sources(self) -> NDArray[np.bool_]:
        return self._due_sources_snapshot.array

    @property
    def accepted_destinations(self) -> NDArray[np.bool_]:
        return self._accepted_destinations_snapshot.array

    @property
    def discarded_destinations(self) -> NDArray[np.bool_]:
        return self._discarded_destinations_snapshot.array

    @property
    def accepted_inputs(self) -> NDArray[np.bool_]:
        return self._accepted_inputs_snapshot.array

    @property
    def last_spike_step(self) -> NDArray[np.int32]:
        return self._last_spike_step_snapshot.array

    @property
    def pending_sources(self) -> NDArray[np.bool_]:
        return self._pending_sources_snapshot.array


@dataclass(frozen=True, init=False)
class NativeComparison:
    completed_steps: int
    trial_indices: tuple[int, ...]
    _gates_equal_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)
    _queue_equal_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)

    def __init__(
        self,
        completed_steps: int,
        trial_indices: tuple[int, ...],
        gates_equal: NDArray[np.bool_],
        queue_equal: NDArray[np.bool_],
    ) -> None:
        trials = len(trial_indices)
        if (
            gates_equal.dtype != np.bool_
            or gates_equal.shape != (trials, 8)
            or queue_equal.dtype != np.bool_
            or queue_equal.ndim != 2
            or queue_equal.shape[0] != trials
        ):
            raise ValueError('Native comparison requires every supplied gate and trial')
        object.__setattr__(self, 'completed_steps', completed_steps)
        object.__setattr__(self, 'trial_indices', trial_indices)
        object.__setattr__(
            self, '_gates_equal_snapshot', HostSnapshot.capture(gates_equal)
        )
        object.__setattr__(
            self, '_queue_equal_snapshot', HostSnapshot.capture(queue_equal)
        )

    @property
    def gates_equal(self) -> NDArray[np.bool_]:
        return self._gates_equal_snapshot.array

    @property
    def queue_equal(self) -> NDArray[np.bool_]:
        return self._queue_equal_snapshot.array


@dataclass(frozen=True, init=False)
class PhysicalQueueObservation:
    completed_steps: int
    trial_indices: tuple[int, ...]
    _queue_snapshot: HostSnapshot[np.bool_] = field(init=False, repr=False)

    def __init__(
        self,
        completed_steps: int,
        trial_indices: tuple[int, ...],
        queue: NDArray[np.bool_],
    ) -> None:
        if (
            queue.dtype != np.bool_
            or queue.ndim != 3
            or queue.shape[1] != len(trial_indices)
        ):
            raise ValueError(
                'Physical queue observations require native slot/trial/edge coverage'
            )
        object.__setattr__(self, 'completed_steps', completed_steps)
        object.__setattr__(self, 'trial_indices', trial_indices)
        object.__setattr__(self, '_queue_snapshot', HostSnapshot.capture(queue))

    @property
    def queue(self) -> NDArray[np.bool_]:
        return self._queue_snapshot.array

    @property
    def sha256(self) -> tuple[str, ...]:
        return tuple(
            hashlib.sha256(self.queue[:, trial].tobytes()).hexdigest()
            for trial in range(self.queue.shape[1])
        )

    @property
    def slot_sha256(self) -> tuple[tuple[str, ...], ...]:
        return tuple(
            tuple(
                hashlib.sha256(self.queue[slot, trial].tobytes()).hexdigest()
                for slot in range(self.queue.shape[0])
            )
            for trial in range(self.queue.shape[1])
        )
