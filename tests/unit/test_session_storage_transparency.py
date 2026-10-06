from dataclasses import fields
from typing import get_type_hints

import numpy as np

from fly_brain.qualification.session_blocks import SessionBlock
from fly_brain.qualification.session_expectations import LedgerState
from fly_brain.simulation.observations import (
    HostSnapshot,
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationInitialState,
    ObservationOperands,
    PhysicalQueueObservation,
    ReductionRow,
)


def test_frozen_records_declare_actual_snapshot_storage_and_typed_view_properties() -> (
    None
):
    for record in (
        ReductionRow,
        ObservationInitialState,
        ObservationConfiguration,
        NativeObservation,
        ObservationOperands,
        NativeComparison,
        PhysicalQueueObservation,
        LedgerState,
        SessionBlock,
    ):
        assert '__getattribute__' not in vars(record)
        assert '__getattr__' not in vars(record)
        annotations = get_type_hints(record)
        for stored in fields(record):
            if stored.name.startswith('_'):
                assert stored.name.endswith('_snapshot')
                assert 'HostSnapshot' in str(
                    annotations[stored.name]
                ) or 'HostFieldSnapshots' in str(annotations[stored.name])
                public = stored.name.removeprefix('_').removesuffix('_snapshot')
                descriptor = vars(record)[public]
                assert isinstance(descriptor, property)
                getter = descriptor.fget
                assert getter is not None
                assert 'return' in get_type_hints(getter)


def test_snapshot_storage_fields_match_their_declared_runtime_type() -> None:
    row = ReductionRow(
        2,
        np.array([0, -1], dtype=np.int32),
        np.array([1, 0], dtype=np.float32),
        np.array([True, False], dtype=np.bool_),
    )
    stored = vars(row)
    for name in ('_edges_snapshot', '_counts_snapshot', '_occupied_snapshot'):
        assert isinstance(stored[name], HostSnapshot)
    assert row.edges.dtype == np.int32
    assert row.counts.dtype == np.float32
    assert row.occupied.dtype == np.bool_
