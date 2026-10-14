from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING

from .identifiers import NeuronRow, TrialId
from .models import Connectome
from .observation_ports import ObservationSession, ObservationSessionFactory
from .observations import ObservationInitialState, ReductionReader

if TYPE_CHECKING:
    from .backend.core import Network, State
    from .backend.engines import Advance, Execution

    Preparation = Callable[
        [Connectome, tuple[NeuronRow, ...], tuple[NeuronRow, ...], str],
        tuple[Execution, ReductionReader],
    ]
    SessionConstructor = Callable[
        [Advance, Network, State, tuple[TrialId, ...]], ObservationSession
    ]


def _new_session(
    trial_indices: tuple[TrialId, ...],
    initial: ObservationInitialState | None,
    execution: 'Execution',
    construct: 'SessionConstructor',
) -> ObservationSession:
    from .backend.core import initial_state

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
    return construct(execution.advance, execution.network, state, trial_indices)


def _build_observation_sessions(
    connectome: Connectome,
    targets: tuple[NeuronRow, ...],
    silenced: tuple[NeuronRow, ...],
    precision: str,
    *,
    prepare: 'Preparation',
    construct: 'SessionConstructor',
) -> tuple[ObservationSessionFactory, ReductionReader]:
    execution, read_rows = prepare(connectome, targets, silenced, precision)
    return partial(_new_session, execution=execution, construct=construct), read_rows


def build_observation_assembly() -> Callable[
    [Connectome, tuple[NeuronRow, ...], tuple[NeuronRow, ...], str],
    tuple[ObservationSessionFactory, ReductionReader],
]:
    from .backend.bucketed import prepare_observed
    from .backend.observation_session import NativeObservationSession

    return partial(
        _build_observation_sessions,
        prepare=prepare_observed,
        construct=NativeObservationSession,
    )


def build_observation_sessions(
    connectome: Connectome,
    targets: tuple[NeuronRow, ...],
    silenced: tuple[NeuronRow, ...],
    precision: str,
) -> tuple[ObservationSessionFactory, ReductionReader]:
    return build_observation_assembly()(connectome, targets, silenced, precision)
