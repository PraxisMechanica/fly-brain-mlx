from functools import partial

from . import commands, service
from .models import ResultWriter, TestRunner
from .ports import (
    DiagnosticCommand,
    InputProbe,
    OutputProbe,
    ParityCommand,
    ParityProbe,
    PinnedInputs,
    ProjectProbe,
    QualificationCommand,
)


def build_qualification(
    runner: TestRunner, writer: ResultWriter
) -> QualificationCommand:
    use_case = partial(service.qualify, runner=runner, writer=writer)
    return partial(commands.qualification, use_case=use_case)


def build_project_probe(execute: ProjectProbe) -> DiagnosticCommand:
    use_case = partial(service.probe_project, execute=execute)
    return partial(commands.diagnostic, use_case=use_case)


def build_output_probe(execute: OutputProbe) -> DiagnosticCommand:
    use_case = partial(service.probe_output, execute=execute)
    return partial(commands.diagnostic, use_case=use_case)


def build_input_probe(load: PinnedInputs, execute: InputProbe) -> DiagnosticCommand:
    use_case = partial(service.audit_inputs, load=load, execute=execute)
    return partial(commands.diagnostic, use_case=use_case)


def build_parity_case(load: PinnedInputs, execute: ParityProbe) -> ParityCommand:
    use_case = partial(service.parity_case, load=load, execute=execute)
    return partial(commands.parity_case, use_case=use_case)
