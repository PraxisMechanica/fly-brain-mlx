from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

StateFields = Mapping[str, NDArray[np.float32 | np.float64]]


@dataclass(frozen=True)
class BudgetViolation:
    step: int
    phase: str
    field: str
    neuron: int
    reference_mv: float
    mlx_mv: float
    budget_mv: float


@dataclass(frozen=True)
class CausalAudit:
    step: int = 0
    first_budget_violation: BudgetViolation | None = None
    first_spike_step: int | None = None
    first_spike_neurons: tuple[int, ...] = ()


def advance_audit(
    audit: CausalAudit,
    step: int,
    reference: StateFields,
    mlx: StateFields,
    reference_spikes: NDArray[np.bool_],
    mlx_spikes: NDArray[np.bool_],
) -> CausalAudit:
    violation = audit.first_budget_violation
    first_spike_step = audit.first_spike_step
    first_spike_neurons = audit.first_spike_neurons
    if step != audit.step:
        raise ValueError('Causal observations must cover consecutive steps')
    if any(
        not np.isfinite(values).all()
        for fields in (reference, mlx)
        for values in fields.values()
    ):
        raise ValueError('Causal state observations must be finite')
    if first_spike_step is None:
        changed = np.flatnonzero(reference_spikes != mlx_spikes)
        for phase in ('pre', 'before', 'end'):
            if phase != 'pre' and changed.size:
                break
            for field in ('v', 'g'):
                expected = np.asarray(reference[phase + '_' + field], dtype=np.float64)
                actual = np.asarray(mlx[phase + '_' + field], dtype=np.float64)
                budget = 1e-3 + 1e-5 * np.abs(expected)
                failed = np.flatnonzero(np.abs(actual - expected) > budget)
                if failed.size and violation is None:
                    neuron = int(failed[0])
                    violation = BudgetViolation(
                        step,
                        phase,
                        field,
                        neuron,
                        float(expected[neuron]),
                        float(actual[neuron]),
                        float(budget[neuron]),
                    )
        if changed.size:
            first_spike_step = step
            first_spike_neurons = tuple(int(index) for index in changed)
    return CausalAudit(audit.step + 1, violation, first_spike_step, first_spike_neurons)
