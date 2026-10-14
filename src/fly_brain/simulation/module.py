from functools import partial

from .commands import simulation
from .input_service import load_pinned_inputs
from .ports import (
    Clock,
    ConnectomeReaderFactory,
    ExperimentReader,
    PinnedInputs,
    SimulationCommand,
    SimulationExecutor,
    SimulationWriter,
    StimulusGenerator,
    StimulusRecorder,
    StimulusWriter,
    UniformDraws,
)
from .service import simulate
from .stimulus_service import read_experiment, record_stimulus, schedule


def build_pinned_inputs(reader_factory: ConnectomeReaderFactory) -> PinnedInputs:
    return partial(load_pinned_inputs, reader_factory=reader_factory)


def build_simulation(
    load: PinnedInputs,
    persist: StimulusWriter,
    execute: SimulationExecutor,
    write: SimulationWriter,
    clock: Clock,
    generate: StimulusGenerator,
) -> SimulationCommand:
    use_case = partial(
        simulate,
        load=load,
        persist=persist,
        execute=execute,
        write=write,
        clock=clock,
        generate=generate,
    )
    return partial(simulation, use_case=use_case)


def build_stimulus(draw_uniforms: UniformDraws) -> StimulusGenerator:
    return partial(schedule, draw_uniforms=draw_uniforms)


def build_experiment_reader() -> ExperimentReader:
    return read_experiment


def build_stimulus_recorder(persist: StimulusWriter) -> StimulusRecorder:
    return partial(record_stimulus, persist=persist)
