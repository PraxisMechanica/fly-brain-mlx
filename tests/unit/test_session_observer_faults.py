from dataclasses import replace

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.ports import ObservationSession, ObservationSessionFactory
from fly_brain.qualification.session_expectations import (
    initial_ledger,
    require_configuration,
)
from fly_brain.qualification.session_observer import observe_session
from fly_brain.simulation.observations import (
    NativeComparison,
    NativeObservation,
    ObservationConfiguration,
    ObservationInitialState,
    ObservationOperands,
    PhysicalQueueObservation,
)
from tests.unit.test_session_expectations import connectome, observation

pytestmark = pytest.mark.unit


class Session:
    def __init__(self, fault: str) -> None:
        self.fault = fault
        self.calls: list[str] = []
        self.step = 0

    @property
    def configuration(self) -> ObservationConfiguration:
        network = connectome()
        return ObservationConfiguration(
            2,
            19,
            0,
            (0,),
            network.sources,
            network.destinations,
            np.array([], dtype=np.int32),
            np.array([22, 22], dtype=np.int32),
            np.full((1, 2), -52, dtype=np.float32),
            np.zeros((1, 2), dtype=np.float32),
            np.full((1, 2), -100000000, dtype=np.int32),
        )

    def advance(self, events: NDArray[np.bool_]) -> NativeObservation:
        self.calls.append('advance')
        self.step += 1
        actual = observation(self.step, (-52, -52))
        if self.fault == 'clock':
            return replace(actual, completed_steps=self.step + 1)
        if self.fault == 'trial':
            return replace(actual, trial_indices=(1,))
        return actual

    def compare(self, operands: ObservationOperands) -> NativeComparison:
        self.calls.append('compare')
        gates = np.ones((1, 8), dtype=np.bool_)
        queues = np.ones((1, 19), dtype=np.bool_)
        if self.fault == 'gate':
            gates[0, 4] = False
        if self.fault == 'slot':
            queues[0, 0] = False
        return NativeComparison(
            self.step + int(self.fault == 'comparison-clock'),
            (1,) if self.fault == 'comparison-trial' else (0,),
            gates,
            queues[:, :-1] if self.fault == 'omitted-slot' else queues,
        )

    def physical_queue(self) -> PhysicalQueueObservation:
        self.calls.append('queue')
        queues = np.zeros((19, 1, 3), dtype=np.bool_)
        if self.fault == 'boundary-slot':
            queues[0, 0, 0] = True
        return PhysicalQueueObservation(self.step, (0,), queues)


@pytest.mark.parametrize(
    'fault',
    (
        'clock',
        'trial',
        'gate',
        'slot',
        'comparison-clock',
        'comparison-trial',
        'omitted-slot',
        'boundary-slot',
    ),
)
def test_missing_reordered_or_wrong_comparisons_never_advance_or_emit_accepted_blocks(
    fault: str,
) -> None:
    session = Session(fault)

    def create(
        trial_indices: tuple[int, ...], initial: ObservationInitialState | None
    ) -> ObservationSession:
        return session

    factory: ObservationSessionFactory = create
    with pytest.raises(ValueError):
        next(
            observe_session(
                factory,
                connectome(),
                (),
                (0,),
                np.zeros((1, 2, 0), dtype=np.uint8),
                block_size=1,
            )
        )
    assert session.calls.count('advance') == 1


@pytest.mark.parametrize(
    'field',
    (
        'sources',
        'destinations',
        'targets',
        'refractory_steps',
        'initial_last_spike_step',
        'initial_step',
        'trial_indices',
        'queue_slots',
    ),
)
def test_qualification_pins_actual_maps_clocks_trials_and_every_queue_slot(
    field: str,
) -> None:
    network = connectome()
    configuration = Session('').configuration
    if field == 'sources':
        actual = replace(configuration, sources=configuration.sources[::-1])
    elif field == 'destinations':
        actual = replace(configuration, destinations=configuration.destinations[::-1])
    elif field == 'targets':
        actual = replace(configuration, targets=np.array([0], dtype=np.int32))
    elif field == 'refractory_steps':
        actual = replace(
            configuration, refractory_steps=np.array([0, 0], dtype=np.int32)
        )
    elif field == 'initial_last_spike_step':
        actual = replace(
            configuration,
            initial_last_spike_step=configuration.initial_last_spike_step + np.int32(1),
        )
    elif field == 'initial_step':
        actual = replace(configuration, initial_step=1)
    elif field == 'trial_indices':
        actual = replace(configuration, trial_indices=(1,))
    else:
        actual = replace(configuration, queue_slots=18)
    with pytest.raises(ValueError, match='independent pinned inputs'):
        require_configuration(
            actual, network, (), (0,), None, initial_ledger(network, (), 1, None)
        )
