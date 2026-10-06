from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from fly_brain.qualification.causality import CausalAudit

from .observer_stream import StepSnapshot
from .paired_observer import PairedBlock, audit_block

if TYPE_CHECKING:
    from fly_brain.simulation.observations import HostArray


@dataclass(frozen=True)
class ObservedStep:
    snapshot: StepSnapshot
    reference: dict[str, 'HostArray']
    mlx: dict[str, 'HostArray']
    mlx_due_edges: NDArray[np.int32]
    mlx_due_sha256: str


@dataclass(frozen=True)
class CauseContext:
    neurons: tuple[int, ...]
    current: ObservedStep
    previous: ObservedStep | None


def observed_step(block: PairedBlock, row: int) -> ObservedStep:
    return ObservedStep(
        block.snapshots[row],
        {
            name: np.asarray(value[row]).copy()
            for name, value in block.reference.fields.items()
        },
        {name: value[row, 0].copy() for name, value in block.mlx.fields.items()},
        block.mlx.due_edges[row][0],
        block.mlx.due_sha256[row][0],
    )


class CausalCapture:
    def __init__(self) -> None:
        self.audit = CausalAudit()
        self.budget: CauseContext | None = None
        self.spike: CauseContext | None = None
        self.previous: ObservedStep | None = None

    def context(
        self, block: PairedBlock, step: int, neurons: tuple[int, ...]
    ) -> CauseContext:
        row = step - block.reference.begin
        return CauseContext(
            neurons,
            observed_step(block, row),
            observed_step(block, row - 1) if row else self.previous,
        )

    def check(self, block: PairedBlock) -> None:
        audit_block(block, self.audit)
        violation = self.audit.first_budget_violation
        if self.budget is None and violation is not None:
            self.budget = self.context(block, violation.step, (violation.neuron,))
        if self.spike is None and self.audit.first_spike_step is not None:
            self.spike = self.context(
                block, self.audit.first_spike_step, self.audit.first_spike_neurons
            )
        self.previous = observed_step(block, block.reference.rows - 1)
