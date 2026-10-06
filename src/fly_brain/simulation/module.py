from functools import partial

from .commands import simulation
from .input_service import load_pinned_inputs
from .ports import (
    Clock,
    ConnectomeReaderFactory,
    PinnedInputs,
    SimulationCommand,
    SimulationExecutor,
    SimulationWriter,
    StimulusWriter,
)
from .service import simulate


def build_pinned_inputs(reader_factory: ConnectomeReaderFactory) -> PinnedInputs:
    return partial(load_pinned_inputs, reader_factory=reader_factory)


def build_simulation(
    load: PinnedInputs,
    persist: StimulusWriter,
    execute: SimulationExecutor,
    write: SimulationWriter,
    clock: Clock,
) -> SimulationCommand:
    use_case = partial(
        simulate, load=load, persist=persist, execute=execute, write=write, clock=clock
    )
    return partial(simulation, use_case=use_case)
