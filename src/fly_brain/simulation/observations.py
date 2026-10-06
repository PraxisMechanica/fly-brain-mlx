import hashlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Generic, TypeGuard, TypeVar

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


def _is_snapshot(value: object) -> TypeGuard[HostSnapshot[np.generic]]:
    return isinstance(value, HostSnapshot)


def _is_tuple(value: object) -> TypeGuard[tuple[object, ...]]:
    return isinstance(value, tuple)


def snapshot_view(value: object) -> object:
    if _is_snapshot(value):
        return value.array
    if isinstance(value, HostFieldSnapshots):
        return value.fields
    if _is_tuple(value):
        return tuple(snapshot_view(item) for item in value)
    return value


@dataclass(frozen=True)
class ReductionRow:
    neuron: int
    edges: NDArray[np.int32]
    counts: NDArray[np.float32]
    occupied: NDArray[np.bool_]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        if (
            self.edges.dtype != np.int32
            or self.counts.dtype != np.float32
            or self.occupied.dtype != np.bool_
            or self.edges.ndim != 1
            or self.edges.shape != self.counts.shape
            or self.edges.shape != self.occupied.shape
        ):
            raise ValueError(
                'Reduction rows require equal native one-dimensional fields'
            )
        object.__setattr__(self, 'edges', HostSnapshot.capture(self.edges))
        object.__setattr__(self, 'counts', HostSnapshot.capture(self.counts))
        object.__setattr__(self, 'occupied', HostSnapshot.capture(self.occupied))


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


@dataclass(frozen=True)
class ObservationInitialState:
    voltage_mv: NDArray[np.float64]
    synaptic_mv: NDArray[np.float64]
    last_spike_step: NDArray[np.int32]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        if (
            self.voltage_mv.dtype != np.float64
            or self.synaptic_mv.dtype != np.float64
            or self.last_spike_step.dtype != np.int32
            or self.voltage_mv.ndim != 2
            or self.synaptic_mv.shape != self.voltage_mv.shape
            or self.last_spike_step.shape != self.voltage_mv.shape
        ):
            raise ValueError(
                'Initial observation fields require equal trial/neuron shapes'
            )
        for name in ('voltage_mv', 'synaptic_mv', 'last_spike_step'):
            object.__setattr__(self, name, HostSnapshot.capture(getattr(self, name)))


@dataclass(frozen=True)
class ObservationConfiguration:
    neurons: int
    queue_slots: int
    initial_step: int
    trial_indices: tuple[int, ...]
    sources: NDArray[np.int32]
    destinations: NDArray[np.int32]
    targets: NDArray[np.int32]
    refractory_steps: NDArray[np.int32]
    initial_voltage_mv: NDArray[np.float32]
    initial_synaptic_mv: NDArray[np.float32]
    initial_last_spike_step: NDArray[np.int32]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        for name in ('sources', 'destinations', 'targets', 'refractory_steps'):
            value = getattr(self, name)
            if value.dtype != np.int32 or value.ndim != 1:
                raise ValueError('Observation configuration requires native int32 maps')
            object.__setattr__(self, name, HostSnapshot.capture(value))
        shape = (len(self.trial_indices), self.neurons)
        for name, dtype in (
            ('initial_voltage_mv', np.float32),
            ('initial_synaptic_mv', np.float32),
            ('initial_last_spike_step', np.int32),
        ):
            value = getattr(self, name)
            if value.dtype != dtype or value.shape != shape:
                raise ValueError('Initial native observation coverage differs')
            object.__setattr__(self, name, HostSnapshot.capture(value))
        if (
            self.sources.shape != self.destinations.shape
            or self.refractory_steps.shape != (self.neurons,)
        ):
            raise ValueError('Native observation map coverage differs')


@dataclass(frozen=True)
class NativeObservation:
    completed_steps: int
    trial_indices: tuple[int, ...]
    fields: Mapping[str, HostArray]
    due_edges: tuple[NDArray[np.int32], ...]
    due_sha256: tuple[str, ...]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        if set(self.fields) != set(PHASE_DTYPES):
            raise ValueError('Native observation requires every actual phase field')
        shape = self.fields['pre_v'].shape
        if len(shape) != 2 or shape[0] != len(self.trial_indices):
            raise ValueError('Native observation trial/neuron coverage differs')
        for name, value in self.fields.items():
            if value.dtype != PHASE_DTYPES[name] or value.ndim != 2:
                raise ValueError('Native observation dtype or phase coverage differs')
            expected_shape = (
                shape if name != 'accepted_inputs' else (shape[0], value.shape[-1])
            )
            if value.shape != expected_shape:
                raise ValueError('Native observation dtype or phase coverage differs')
        object.__setattr__(self, 'fields', HostFieldSnapshots.capture(self.fields))
        if len(self.due_edges) != shape[0] or len(self.due_sha256) != shape[0]:
            raise ValueError('Native due observations require every trial')
        for edges in self.due_edges:
            if edges.dtype != np.int32 or edges.ndim != 1:
                raise ValueError('Native due identities require one-dimensional int32')
        object.__setattr__(
            self,
            'due_edges',
            tuple(HostSnapshot.capture(edges) for edges in self.due_edges),
        )


@dataclass(frozen=True)
class ObservationOperands:
    sources: NDArray[np.int32]
    destinations: NDArray[np.int32]
    available: NDArray[np.bool_]
    spikes: NDArray[np.bool_]
    receiving: NDArray[np.bool_]
    due_sources: NDArray[np.bool_]
    accepted_destinations: NDArray[np.bool_]
    discarded_destinations: NDArray[np.bool_]
    accepted_inputs: NDArray[np.bool_]
    last_spike_step: NDArray[np.int32]
    pending_sources: NDArray[np.bool_]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        shape = self.available.shape
        if len(shape) != 2:
            raise ValueError('Comparison operands require trial/neuron matrices')
        for name in (
            'available',
            'spikes',
            'receiving',
            'due_sources',
            'accepted_destinations',
            'discarded_destinations',
        ):
            value = getattr(self, name)
            if value.dtype != np.bool_ or value.shape != shape:
                raise ValueError('Comparison Boolean operands have different coverage')
            object.__setattr__(self, name, HostSnapshot.capture(value))
        for name in ('sources', 'destinations'):
            value = getattr(self, name)
            if value.dtype != np.int32 or value.ndim != 1:
                raise ValueError('Comparison maps require native int32 identities')
            object.__setattr__(self, name, HostSnapshot.capture(value))
        if (
            self.sources.shape != self.destinations.shape
            or self.accepted_inputs.dtype != np.bool_
            or self.accepted_inputs.ndim != 2
            or self.accepted_inputs.shape[0] != shape[0]
            or self.last_spike_step.dtype != np.int32
            or self.last_spike_step.shape != shape
            or self.pending_sources.dtype != np.bool_
            or self.pending_sources.ndim != 3
            or self.pending_sources.shape[1:] != shape
        ):
            raise ValueError(
                'Comparison input, clock or queue operands have different coverage'
            )
        for name in ('accepted_inputs', 'last_spike_step', 'pending_sources'):
            object.__setattr__(self, name, HostSnapshot.capture(getattr(self, name)))


@dataclass(frozen=True)
class NativeComparison:
    completed_steps: int
    trial_indices: tuple[int, ...]
    gates_equal: NDArray[np.bool_]
    queue_equal: NDArray[np.bool_]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        trials = len(self.trial_indices)
        if (
            self.gates_equal.dtype != np.bool_
            or self.gates_equal.shape != (trials, 8)
            or self.queue_equal.dtype != np.bool_
            or self.queue_equal.ndim != 2
            or self.queue_equal.shape[0] != trials
        ):
            raise ValueError('Native comparison requires every supplied gate and trial')
        object.__setattr__(self, 'gates_equal', HostSnapshot.capture(self.gates_equal))
        object.__setattr__(self, 'queue_equal', HostSnapshot.capture(self.queue_equal))


@dataclass(frozen=True)
class PhysicalQueueObservation:
    completed_steps: int
    trial_indices: tuple[int, ...]
    queue: NDArray[np.bool_]

    def __getattribute__(self, name: str) -> object:
        return snapshot_view(object.__getattribute__(self, name))

    def __post_init__(self) -> None:
        if (
            self.queue.dtype != np.bool_
            or self.queue.ndim != 3
            or self.queue.shape[1] != len(self.trial_indices)
        ):
            raise ValueError(
                'Physical queue observations require native slot/trial/edge coverage'
            )
        object.__setattr__(self, 'queue', HostSnapshot.capture(self.queue))

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
