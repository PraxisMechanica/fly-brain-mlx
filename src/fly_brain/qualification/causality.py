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


class CausalAudit:
    def __init__(self) -> None:
        self.step = 0
        self.first_budget_violation: BudgetViolation | None = None
        self.first_spike_step: int | None = None
        self.first_spike_neurons: tuple[int, ...] = ()

    def check(
        self,
        step: int,
        reference: StateFields,
        mlx: StateFields,
        reference_spikes: NDArray[np.bool_],
        mlx_spikes: NDArray[np.bool_],
    ) -> None:
        if step != self.step:
            raise ValueError('Causal observations must cover consecutive steps')
        if any(
            not np.isfinite(values).all()
            for fields in (reference, mlx)
            for values in fields.values()
        ):
            raise ValueError('Causal state observations must be finite')
        if self.first_spike_step is None:
            changed = np.flatnonzero(reference_spikes != mlx_spikes)
            for phase in ('pre', 'before', 'end'):
                if phase != 'pre' and changed.size:
                    break
                for field in ('v', 'g'):
                    expected = np.asarray(
                        reference[phase + '_' + field], dtype=np.float64
                    )
                    actual = np.asarray(mlx[phase + '_' + field], dtype=np.float64)
                    budget = 1e-3 + 1e-5 * np.abs(expected)
                    failed = np.flatnonzero(np.abs(actual - expected) > budget)
                    if failed.size and self.first_budget_violation is None:
                        neuron = int(failed[0])
                        self.first_budget_violation = BudgetViolation(
                            step,
                            phase,
                            field,
                            neuron,
                            float(expected[neuron]),
                            float(actual[neuron]),
                            float(budget[neuron]),
                        )
            if changed.size:
                self.first_spike_step = step
                self.first_spike_neurons = tuple(int(index) for index in changed)
        self.step += 1
