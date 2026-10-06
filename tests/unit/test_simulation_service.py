from pathlib import Path

import numpy as np
import pytest

from fly_brain.infrastructure.seeded_random import uniforms
from fly_brain.simulation.models import (
    Connectome,
    Experiment,
    InputPin,
    SimulationRequest,
    SimulationResult,
    SimulationRun,
    SpikeEvents,
    Stimulus,
)
from fly_brain.simulation.module import build_stimulus
from fly_brain.simulation.service import simulate

pytestmark = pytest.mark.unit


def test_stage_timings_use_only_the_injected_clock() -> None:
    request = SimulationRequest(
        Path('/project'), Path('/result'), 'silent', 0.001, 1, 0
    )
    connectome = Connectome(
        np.array([10, 20], dtype=np.int64),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    pin = InputPin('csv', 'parquet', 2, 0)
    events = SpikeEvents(
        np.array([], dtype=np.int64),
        np.array([], dtype=np.int64),
        np.array([], dtype=np.int64),
    )
    run = SimulationRun(events, {}, 0, 'test')
    result = SimulationResult(Path('/result/spikes.parquet'), 0, 0, 13.0)
    observed: list[tuple[dict[str, float], float]] = []

    def load(project: Path) -> tuple[Connectome, InputPin]:
        return connectome, pin

    def persist(
        output: Path, experiment: Experiment, inputs: InputPin, stimulus: Stimulus
    ) -> Stimulus:
        return stimulus

    def execute(
        network: Connectome, stimulus: Stimulus, silenced: tuple[int, ...]
    ) -> SimulationRun:
        return run

    def write(
        options: SimulationRequest,
        network: Connectome,
        inputs: InputPin,
        stimulus: Stimulus,
        completed: SimulationRun,
        timings: dict[str, float],
        started: float,
    ) -> SimulationResult:
        observed.append((timings, started))
        return result

    clock = iter((100.0, 102.0, 105.0, 108.0, 109.0, 113.0)).__next__
    assert (
        simulate(
            request, load, persist, execute, write, clock, build_stimulus(uniforms)
        )
        is result
    )
    assert observed == [
        ({'data_load_s': 2.0, 'schedule_s': 3.0, 'stimulus_io_s': 4.0}, 100.0)
    ]
