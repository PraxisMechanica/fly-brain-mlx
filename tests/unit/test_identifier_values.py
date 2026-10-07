import json

import numpy as np
import pytest

from fly_brain.simulation.identifiers import (
    EdgeRows32,
    FlyWireIds64,
    FlyWireNeuronId,
    NeuronRow,
    NeuronRows32,
    NeuronRows64,
    PaddedEdgeRows32,
    TrialId,
    TrialIds16,
    TrialIds64,
)

pytestmark = pytest.mark.unit


def test_scalar_identities_preserve_native_objects_and_json_values() -> None:
    raw = int('720575940624963786')
    values = (FlyWireNeuronId(raw), NeuronRow(raw), TrialId(raw))
    assert all(value is raw and type(value) is int for value in values)
    assert json.dumps(values) == json.dumps((raw, raw, raw))


@pytest.mark.parametrize('readonly', (False, True))
@pytest.mark.parametrize('empty', (False, True))
def test_array_identities_preserve_object_dtype_shape_bytes_order_and_flags(
    readonly: bool, empty: bool
) -> None:
    native32 = np.arange(12, dtype=np.int32).reshape(3, 4).T
    native64 = np.arange(12, dtype=np.int64).reshape(3, 4).T
    native16 = np.arange(12, dtype=np.int16).reshape(3, 4).T
    if empty:
        native32, native64, native16 = native32[:0], native64[:0], native16[:0]
    for value in (native32, native64, native16):
        value.setflags(write=not readonly)
    pairs = (
        (FlyWireIds64(native64), native64),
        (NeuronRows32(native32), native32),
        (NeuronRows64(native64), native64),
        (EdgeRows32(native32), native32),
        (PaddedEdgeRows32(native32), native32),
        (TrialIds16(native16), native16),
        (TrialIds64(native64), native64),
    )
    for branded, original in pairs:
        assert branded is original
        assert (
            type(branded),
            branded.dtype,
            branded.shape,
            branded.strides,
            branded.tobytes(order='A'),
            branded.flags.writeable,
        ) == (
            type(original),
            original.dtype,
            original.shape,
            original.strides,
            original.tobytes(order='A'),
            original.flags.writeable,
        )
