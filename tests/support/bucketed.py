import numpy as np

from fly_brain.simulation.backend.accumulation import SCALE
from fly_brain.simulation.backend.bucketed import prepare
from fly_brain.simulation.backend.engines import Execution
from fly_brain.simulation.models import Connectome, NetworkCase


def bucketed_case(
    case: NetworkCase, precision: str, *, exact_counts: bool = False
) -> Execution:
    weights = np.asarray(case.weights, dtype=np.float64)
    counts = np.rint(weights / SCALE).astype(np.int32)
    np.testing.assert_array_equal(counts.astype(np.float64) * SCALE, weights)
    connectome = Connectome(
        np.arange(case.neurons, dtype=np.int64),
        np.asarray(case.sources, dtype=np.int32),
        np.asarray(case.destinations, dtype=np.int32),
        counts,
        weights,
    )
    return prepare(
        connectome, case.targets, case.silenced, precision, exact_counts=exact_counts
    )


def exact_bucketed_case(case: NetworkCase, precision: str) -> Execution:
    return bucketed_case(case, precision, exact_counts=True)
