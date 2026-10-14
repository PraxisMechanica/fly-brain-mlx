import numpy as np
from numpy.typing import NDArray

from fly_brain.simulation.identifiers import FlyWireIds64

from .acceptance import (
    assemble_metrics,
    counts_on_support,
    groups_by_neuron,
    match_steps,
)
from .models import FlyWireSpikeSteps, ParityMetrics


def measure_trials(
    trials: tuple[tuple[FlyWireSpikeSteps, FlyWireSpikeSteps], ...],
    support: FlyWireIds64,
    duration_s: float,
) -> ParityMetrics:
    if not trials:
        raise ValueError('Missing trials have unavailable pooled diagnostics')
    first: NDArray[np.int64] = np.stack(
        [counts_on_support(b, support) for b, _ in trials]
    ).sum(axis=0, dtype=np.int64)
    second: NDArray[np.int64] = np.stack(
        [counts_on_support(x, support) for _, x in trials]
    ).sum(axis=0, dtype=np.int64)
    grouped = tuple((groups_by_neuron(b), groups_by_neuron(x)) for b, x in trials)
    return assemble_metrics(
        first,
        second,
        int(first.sum()),
        int(second.sum()),
        [value for b, x in grouped for value in match_steps(b, x, 10)],
        sum(len(match_steps(b, x, 0)) for b, x in grouped),
        sum(len(match_steps(b, x, 1)) for b, x in grouped),
        duration_s * len(trials),
    )
