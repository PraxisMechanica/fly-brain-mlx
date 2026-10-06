import os
import platform
from functools import partial
from time import perf_counter

from fly_brain.comparison.ports import ComparisonCommand
from fly_brain.qualification.fan_in_ports import FanInCaseBuilder
from fly_brain.qualification.ports import (
    DiagnosticCommand,
    ParityCommand,
    QualificationCommand,
)
from fly_brain.simulation.ports import (
    ConnectomeReader,
    PinnedInputs,
    SimulationCommand,
    StimulusGenerator,
)


def configure_mlx() -> str:
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise RuntimeError('The application requires Apple silicon and macOS')
    precision = os.environ.setdefault('MLX_ENABLE_TF32', '0')
    if precision != '0':
        raise RuntimeError('Launch with MLX_ENABLE_TF32=0')
    return precision


def qualification() -> QualificationCommand:
    from fly_brain.qualification.adapters.pytest_runner import run_tests
    from fly_brain.qualification.adapters.results import write_result

    configure_mlx()
    from fly_brain.qualification.module import build_qualification

    return build_qualification(run_tests, write_result)


def comparison() -> ComparisonCommand:
    from fly_brain.comparison.module import build_comparison
    from fly_brain.comparison.storage import read_spikes, write_comparison

    return build_comparison(read_spikes, write_comparison)


def accumulation() -> DiagnosticCommand:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.accumulation_probe import run
    from fly_brain.qualification.module import build_project_probe

    return build_project_probe(partial(run, precision=precision))


def factored() -> DiagnosticCommand:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.factored_probe import run
    from fly_brain.qualification.module import build_project_probe

    return build_project_probe(partial(run, precision=precision))


def bucketed_scalars() -> DiagnosticCommand:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.bucketed_scalars import run
    from fly_brain.qualification.module import build_project_probe

    return build_project_probe(partial(run, precision=precision))


def replay() -> DiagnosticCommand:
    from fly_brain.qualification.adapters.replay_probe import run
    from fly_brain.qualification.module import build_output_probe

    return build_output_probe(run)


def schedule() -> DiagnosticCommand:
    from fly_brain.qualification.adapters.schedule_probe import run
    from fly_brain.qualification.module import build_output_probe

    return build_output_probe(run)


def build_connectome_reader() -> ConnectomeReader:
    from fly_brain.simulation.inputs import load_connectome

    return load_connectome


def pinned_inputs() -> PinnedInputs:
    from fly_brain.simulation.module import build_pinned_inputs

    return build_pinned_inputs(build_connectome_reader)


def input_audit() -> DiagnosticCommand:
    from fly_brain.qualification.adapters.connectome_probe import run
    from fly_brain.qualification.module import build_input_probe

    return build_input_probe(pinned_inputs(), run)


def fan_in_audit() -> DiagnosticCommand:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.fan_in_probe import run
    from fly_brain.qualification.module import build_input_probe

    return build_input_probe(
        pinned_inputs(), partial(run, precision=precision, build_cases=fan_in_cases())
    )


def layout_fan_in_audit() -> DiagnosticCommand:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.bucketed_fan_in import evaluate_cases
    from fly_brain.qualification.adapters.fan_in_probe import run
    from fly_brain.qualification.module import build_input_probe

    return build_input_probe(
        pinned_inputs(),
        partial(
            run,
            precision=precision,
            evaluator=evaluate_cases,
            build_cases=fan_in_cases(),
            scope='All prescribed pinned fan-in cases through production layout; not full-network dynamics.',
        ),
    )


def device_layout_audit() -> DiagnosticCommand:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.device_layout_probe import run
    from fly_brain.qualification.module import build_input_probe

    return build_input_probe(pinned_inputs(), partial(run, precision=precision))


def connectome_pulse() -> DiagnosticCommand:
    precision = configure_mlx()
    from fly_brain.qualification.adapters.connectome_pulse import run
    from fly_brain.qualification.module import build_input_probe

    return build_input_probe(pinned_inputs(), partial(run, precision=precision))


def simulation() -> SimulationCommand:
    precision = configure_mlx()
    from fly_brain.simulation.backend.runner import run
    from fly_brain.simulation.module import build_simulation
    from fly_brain.simulation.storage import persist_stimulus, write_run

    return build_simulation(
        pinned_inputs(),
        persist_stimulus,
        partial(run, precision=precision),
        partial(write_run, clock=perf_counter),
        perf_counter,
        stimulus(),
    )


def parity_case() -> ParityCommand:
    precision = configure_mlx()
    import torch

    from fly_brain.qualification.adapters.parity_case import run
    from fly_brain.qualification.module import build_parity_case

    torch.set_num_threads(1)
    return build_parity_case(
        pinned_inputs(), partial(run, precision=precision, generate=stimulus())
    )


def stimulus() -> StimulusGenerator:
    from fly_brain.infrastructure.seeded_random import uniforms
    from fly_brain.simulation.module import build_stimulus

    return build_stimulus(uniforms)


def fan_in_cases() -> FanInCaseBuilder:
    from fly_brain.infrastructure.seeded_random import permutation, uniforms
    from fly_brain.qualification.module import build_fan_in_cases

    return build_fan_in_cases(uniforms, permutation)
