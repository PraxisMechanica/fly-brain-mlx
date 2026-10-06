from collections.abc import Callable
from pathlib import Path

from .experiments import EXPERIMENTS
from .models import (
    Connectome,
    Experiment,
    InputPin,
    SimulationRequest,
    SimulationResult,
    SimulationRun,
    Stimulus,
)
from .stimuli import generate, neuron_indices


def simulate(
    request: SimulationRequest,
    load: Callable[[Path], tuple[Connectome, InputPin]],
    persist: Callable[[Path, Experiment, InputPin, Stimulus], Stimulus],
    execute: Callable[[Connectome, Stimulus, tuple[int, ...]], SimulationRun],
    write: Callable[
        [
            SimulationRequest,
            Connectome,
            InputPin,
            Stimulus,
            SimulationRun,
            dict[str, float],
            float,
        ],
        SimulationResult,
    ],
    clock: Callable[[], float],
) -> SimulationResult:
    started = clock()
    connectome, pin = load(request.project)
    timings = {'data_load_s': clock() - started}
    scheduled = clock()
    experiment = EXPERIMENTS[request.experiment]
    stimulus = generate(
        connectome,
        experiment,
        round(request.duration_s * 10000),
        tuple(range(request.trials)),
        request.seed,
    )
    silenced = neuron_indices(connectome, experiment.silenced_ids)
    timings['schedule_s'] = clock() - scheduled
    persisted = clock()
    stimulus = persist(request.output, experiment, pin, stimulus)
    timings['stimulus_io_s'] = clock() - persisted
    run = execute(connectome, stimulus, silenced)
    return write(request, connectome, pin, stimulus, run, timings, started)
