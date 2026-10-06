from functools import partial
from typing import TYPE_CHECKING

from .models import Connectome
from .observation_ports import ObservationSession, ObservationSessionFactory
from .observations import ObservationInitialState, ReductionReader

if TYPE_CHECKING:
    from .backend.engines import Execution


def _new_session(
    trial_indices: tuple[int, ...],
    initial: ObservationInitialState | None,
    execution: 'Execution',
) -> ObservationSession:
    from .backend.core import initial_state
    from .backend.observation_session import NativeObservationSession

    if initial is None:
        state = initial_state(execution.network, len(trial_indices))
    else:
        state = initial_state(
            execution.network,
            len(trial_indices),
            initial.voltage_mv,
            initial.synaptic_mv,
            initial.last_spike_step,
        )
    return NativeObservationSession(
        execution.advance, execution.network, state, trial_indices
    )


def build_observation_sessions(
    connectome: Connectome,
    targets: tuple[int, ...],
    silenced: tuple[int, ...],
    precision: str,
) -> tuple[ObservationSessionFactory, ReductionReader]:
    from .backend.bucketed import prepare_observed

    execution, read_rows = prepare_observed(connectome, targets, silenced, precision)
    return partial(_new_session, execution=execution), read_rows
