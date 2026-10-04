from collections.abc import Callable
from pathlib import Path
from time import perf_counter

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
) -> SimulationResult:
    started = perf_counter()
    connectome, pin = load(request.project)
    timings = {'data_load_s': perf_counter() - started}
    scheduled = perf_counter()
    experiment = EXPERIMENTS[request.experiment]
    stimulus = generate(
        connectome,
        experiment,
        round(request.duration_s * 10000),
        tuple(range(request.trials)),
        request.seed,
    )
    silenced = neuron_indices(connectome, experiment.silenced_ids)
    timings['schedule_s'] = perf_counter() - scheduled
    persisted = perf_counter()
    stimulus = persist(request.output, experiment, pin, stimulus)
    timings['stimulus_io_s'] = perf_counter() - persisted
    run = execute(connectome, stimulus, silenced)
    return write(request, connectome, pin, stimulus, run, timings, started)
