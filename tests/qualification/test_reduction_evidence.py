from dataclasses import replace

import mlx.core as mx
import numpy as np
import pytest

from fly_brain.simulation.backend.bucketed import make_layout, prepare_observed
from fly_brain.simulation.backend.reduction_evidence import read_rows
from fly_brain.simulation.models import Connectome
from fly_brain.simulation.observations import COMPENSATED_ORDER, EXACT_ORDER
from tests.qualification.test_mlx_observer import fixture

pytestmark = [pytest.mark.integration, pytest.mark.metal]


@pytest.mark.parametrize('exact', (False, True))
def test_reader_reports_the_actual_bound_reduction_mode(
    precision: str, exact: bool
) -> None:
    case = fixture()
    _, read = prepare_observed(
        case.connectome, case.targets, (3,), precision, exact_counts=exact
    )
    assert read(()).order == (EXACT_ORDER if exact else COMPENSATED_ORDER)


def test_requested_exact_mode_reports_original_fallback_outside_the_guard(
    precision: str,
) -> None:
    counts = np.array([2**24, 2**24], dtype=np.int32)
    connectome = Connectome(
        np.array([10, 20], dtype=np.int64),
        np.array([0, 0], dtype=np.int32),
        np.array([1, 1], dtype=np.int32),
        counts,
        counts.astype(np.float64) * 0.275,
    )
    _, read = prepare_observed(connectome, (), (), precision, exact_counts=True)
    assert read(()).order == COMPENSATED_ORDER


def test_reader_observes_changed_actual_device_leaves_instead_of_reconstructing_input(
    precision: str,
) -> None:
    case = fixture()
    layout = make_layout(case.connectome)
    bucket = next(
        bucket for bucket in layout.buckets if np.asarray(bucket.targets).size
    )
    with mx.stream(mx.gpu):
        counts = bucket.counts + 1
        changed = replace(bucket, counts=counts)
    actual = replace(
        layout,
        buckets=tuple(changed if item is bucket else item for item in layout.buckets),
    )
    target = int(np.asarray(bucket.targets)[0])
    observed = read_rows(actual, (target,)).rows[0]
    assert observed.counts.tobytes() == np.asarray(counts[0]).tobytes()
    assert observed.counts.tobytes() != np.asarray(bucket.counts[0]).tobytes()


def test_reader_rejects_a_neuron_missing_from_the_actual_layout(precision: str) -> None:
    case = fixture()
    _, read = prepare_observed(case.connectome, case.targets, (), precision)
    with pytest.raises(ValueError, match='absent from the actual device layout'):
        read((case.connectome.neuron_ids.size,))


def test_reader_rejects_changed_actual_native_dtype(precision: str) -> None:
    case = fixture()
    layout = make_layout(case.connectome)
    bucket = layout.buckets[0]
    with mx.stream(mx.gpu):
        changed = replace(bucket, counts=bucket.counts.astype(mx.float16))
    actual = replace(layout, buckets=(changed, *layout.buckets[1:]))
    target = int(np.asarray(bucket.targets)[0])
    with pytest.raises(ValueError, match='equal native one-dimensional fields'):
        read_rows(actual, (target,))
