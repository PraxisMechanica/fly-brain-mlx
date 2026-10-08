from pathlib import Path

import pytest

from fly_brain import bootstrap, cli
from fly_brain.comparison.models import ComparisonRequest
from fly_brain.comparison.ports import ComparisonCommand
from fly_brain.qualification.models import ParityCase, QualificationRequest
from fly_brain.qualification.ports import DiagnosticCommand
from fly_brain.qualification.schemas import ParityOptions
from fly_brain.simulation.models import SimulationRequest
from fly_brain.simulation.ports import SimulationCommand

pytestmark = pytest.mark.unit


DIAGNOSTICS: tuple[tuple[str, str], ...] = (
    ('probe-accumulation', 'accumulation'),
    ('probe-factored', 'factored'),
    ('probe-bucketed', 'bucketed_scalars'),
    ('probe-replay', 'replay'),
    ('inspect-reference', 'schedule'),
    ('audit-inputs', 'input_audit'),
    ('qualify-fan-in', 'fan_in_audit'),
    ('qualify-layout-fan-in', 'layout_fan_in_audit'),
    ('qualify-device-layout', 'device_layout_audit'),
    ('qualify-connectome-pulse', 'connectome_pulse'),
    ('qualify', 'qualification'),
)


@pytest.mark.parametrize('name,factory', DIAGNOSTICS)
def test_cli_dispatches_each_validated_qualification_command_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, factory: str
) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    calls: list[QualificationRequest] = []

    def command(request: QualificationRequest) -> int:
        calls.append(request)
        return 1

    def compose() -> DiagnosticCommand:
        return command

    monkeypatch.setattr(bootstrap, factory, compose)
    assert (
        cli.main(
            [name, '--project', str(tmp_path), '--output', str(tmp_path / 'fresh')]
        )
        == 1
    )
    assert calls == [QualificationRequest(tmp_path, tmp_path / 'fresh')]


def test_cli_preserves_simulation_defaults_and_fresh_default_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / 'data').mkdir()
    for name in ('2025_Completeness_783.csv', '2025_Connectivity_783.parquet'):
        (tmp_path / 'data' / name).touch()
    calls: list[SimulationRequest] = []

    def command(request: SimulationRequest) -> int:
        calls.append(request)
        return 0

    def compose() -> SimulationCommand:
        return command

    monkeypatch.setattr(bootstrap, 'simulation', compose)
    monkeypatch.setattr(cli.time, 'time_ns', lambda: 123)
    assert cli.main(['simulate', '--project', str(tmp_path)]) == 0
    assert calls == [
        SimulationRequest(
            tmp_path, tmp_path / 'executions/mlx-123', 'sugar', 0.1, 1, 20261004
        )
    ]


def test_cli_prepares_the_comparison_request_and_output_before_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second, output = tmp_path / 'first', tmp_path / 'second', tmp_path / 'fresh'
    first.touch()
    second.touch()
    events: list[object] = []
    resolve = Path.resolve

    def resolve_path(value: Path, strict: bool = False) -> Path:
        if value == output:
            events.append('resolve-output')
        return resolve(value, strict=strict)

    def command(request: ComparisonRequest, destination: Path) -> int:
        events.append((request, destination))
        return 0

    def compose() -> ComparisonCommand:
        events.append('compose')
        return command

    monkeypatch.setattr(Path, 'resolve', resolve_path)
    monkeypatch.setattr(bootstrap, 'comparison', compose)
    assert (
        cli.main(
            [
                'compare',
                '--first',
                str(first),
                '--second',
                str(second),
                '--output',
                str(output),
                '--duration-s',
                '0.1',
                '--trials',
                '1',
            ]
        )
        == 0
    )
    assert events == [
        'resolve-output',
        'compose',
        (ComparisonRequest(first, second, 0.1, 1, 0.1, 'mlx', 'brian2cpp'), output),
    ]


def test_cli_prepares_the_parity_case_before_composition(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fly_brain.qualification.ports import ParityCommand

    (tmp_path / 'tests/qualification').mkdir(parents=True)
    events: list[object] = []
    to_case = ParityOptions.to_case

    def selected_case(options: ParityOptions) -> ParityCase:
        events.append('case')
        return to_case(options)

    def command(project: Path, output: Path, case: ParityCase) -> int:
        events.append(case)
        return 0

    def compose() -> ParityCommand:
        events.append('compose')
        return command

    monkeypatch.setattr(ParityOptions, 'to_case', selected_case)
    monkeypatch.setattr(bootstrap, 'parity_case', compose)
    assert (
        cli.main(
            [
                'qualify-parity',
                '--project',
                str(tmp_path),
                '--output',
                str(tmp_path / 'fresh'),
            ]
        )
        == 0
    )
    assert events == ['case', 'case', 'compose', ParityCase('sugar', 1000, 0)]
