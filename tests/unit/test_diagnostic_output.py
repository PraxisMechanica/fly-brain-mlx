import json
from pathlib import Path
from typing import cast

import pytest
from pydantic import ValidationError

from fly_brain import bootstrap, cli
from fly_brain.qualification.commands import diagnostic
from fly_brain.qualification.models import QualificationRequest
from fly_brain.qualification.schemas import ParityOptions, QualificationOptions
from fly_brain.simulation.schemas import SimulationOptions
from tools.architecture.compiler import JsonValue, object_value

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('accepted', (True, False, None))
def test_display_preserves_exit_and_explicit_scientific_flags_only(
    capsys: pytest.CaptureFixture[str], accepted: bool | None
) -> None:
    request = QualificationRequest(Path('/project'), Path('/executions/probe'))
    report: dict[str, object] = {'cases': 157, 'scalar_qualification_passed': True}
    if accepted is not None:
        report['accepted'] = accepted
    calls: list[QualificationRequest] = []

    def execute(value: QualificationRequest) -> dict[str, object]:
        calls.append(value)
        return report

    code = diagnostic(request, execute)
    display = object_value(cast(JsonValue, json.loads(capsys.readouterr().out)))
    summary = object_value(display['summary'])
    assert code == display['exit_code'] == (1 if accepted is False else 0)
    assert display['kind'] == 'diagnostic' and display['output'] == str(request.output)
    assert ('accepted' in summary) == (accepted is not None)
    assert 'case_accepted' not in summary and 'full_matrix_accepted' not in summary
    assert summary['scalar_qualification_passed'] is True
    assert calls == [request] and report['cases'] == 157


def test_large_report_keeps_late_false_checks_and_skips_visible_without_mutation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    checks = {f'gate-{index}': True for index in range(5000)}
    checks['last-failed-gate'] = False
    report: dict[str, object] = {
        'accepted': True,
        'metadata': ['unused' * 1000] * 5000,
        'details': {
            'checks': checks,
            'skipped': 3,
            'errors': ['native error ' + 'x' * 10000] * 30,
            'first_divergence': {'step': 9999, 'neuron': 42, 'reason': 'late fork'},
        },
    }
    request = QualificationRequest(Path('/project'), Path('/executions/probe'))
    assert diagnostic(request, lambda _: report) == 0
    text = capsys.readouterr().out
    display = object_value(cast(JsonValue, json.loads(text)))
    false_flags, alerts = (
        object_value(display['false_flags']),
        object_value(display['alerts']),
    )
    assert len(text) < 5000
    assert false_flags == {
        'total': 1,
        'examples': ['details.checks.last-failed-gate'],
        'omitted': 0,
    }
    assert alerts['total'] == 3 and alerts['omitted'] == 0
    assert (
        'details.skipped' in text
        and 'details.errors' in text
        and 'details.first_divergence' in text
    )
    assert 'characters omitted' in text and 'omitted_items' in text
    assert report['details'] is not None and checks['last-failed-gate'] is False
    assert len(cast(list[str], report['metadata'])) == 5000


def test_many_failed_flags_have_exact_totals_and_explicit_omissions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report: dict[str, object] = {
        'accepted': False,
        'checks': {f'failure-{index}': False for index in range(200)},
        'reason': 'unbounded reason ' * 10000,
    }
    assert (
        diagnostic(
            QualificationRequest(Path('/project'), Path('/fresh')), lambda _: report
        )
        == 1
    )
    display = object_value(cast(JsonValue, json.loads(capsys.readouterr().out)))
    flags = object_value(display['false_flags'])
    examples = flags['examples']
    assert isinstance(examples, list)
    assert (flags['total'], len(examples), flags['omitted']) == (201, 10, 191)
    assert 'characters omitted' in cast(str, object_value(display['summary'])['reason'])


def test_first_step_divergence_and_late_list_check_are_not_treated_as_empty(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report: dict[str, object] = {
        'checks': [True] * 5000 + [False],
        'first_spike_step': 0,
        'first_budget_violation': None,
    }
    assert (
        diagnostic(
            QualificationRequest(Path('/project'), Path('/fresh')), lambda _: report
        )
        == 0
    )
    display = object_value(cast(JsonValue, json.loads(capsys.readouterr().out)))
    assert display['false_flags'] == {
        'total': 1,
        'examples': ['checks[5000]'],
        'omitted': 0,
    }
    assert display['alerts'] == {
        'total': 1,
        'examples': [{'field': 'first_spike_step', 'value': 0}],
        'omitted': 0,
    }


@pytest.mark.parametrize(
    'schema', (SimulationOptions, QualificationOptions, ParityOptions)
)
@pytest.mark.parametrize('root_name', ('project', 'cwd'))
@pytest.mark.parametrize('alias', (False, True))
def test_scientific_destinations_reject_disposable_logs_and_resolved_aliases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    schema: type[SimulationOptions] | type[QualificationOptions] | type[ParityOptions],
    root_name: str,
    alias: bool,
) -> None:
    project, cwd = tmp_path / 'project', tmp_path / 'cwd'
    (project / 'tests/qualification').mkdir(parents=True)
    (project / 'data').mkdir()
    for name in ('2025_Completeness_783.csv', '2025_Connectivity_783.parquet'):
        (project / 'data' / name).touch()
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    logs = (project if root_name == 'project' else cwd) / 'logs'
    logs.mkdir()
    base = tmp_path / 'alias' if alias else logs
    if alias:
        base.symlink_to(logs, target_is_directory=True)
    with pytest.raises(ValidationError, match='disposable logs'):
        schema(project=project, output=base / 'fresh')
    assert not (logs / 'fresh').exists()


@pytest.mark.parametrize(
    'schema', (SimulationOptions, QualificationOptions, ParityOptions)
)
def test_scientific_destinations_accept_retained_and_arbitrary_external_fresh_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    schema: type[SimulationOptions] | type[QualificationOptions] | type[ParityOptions],
) -> None:
    project, cwd = tmp_path / 'project', tmp_path / 'cwd'
    (project / 'tests/qualification').mkdir(parents=True)
    (project / 'data').mkdir()
    for name in ('2025_Completeness_783.csv', '2025_Connectivity_783.parquet'):
        (project / 'data' / name).touch()
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    for output in (project / 'executions/run', tmp_path / 'external/logs/fresh'):
        options = schema(project=project, output=output)
        assert options.output == output.resolve() and not output.exists()


@pytest.mark.parametrize(
    'command', ('simulate', 'qualify', 'qualify-parity', 'compare')
)
def test_cli_rejects_disposable_output_before_any_command_is_composed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    (tmp_path / 'data').mkdir()
    for name in ('2025_Completeness_783.csv', '2025_Connectivity_783.parquet'):
        (tmp_path / 'data' / name).touch()
    first, second = tmp_path / 'first', tmp_path / 'second'
    first.touch()
    second.touch()
    monkeypatch.chdir(tmp_path)
    composed: list[str] = []

    def compose() -> None:
        composed.append('unexpected')
        raise AssertionError('Invalid output must not reach command composition')

    for name in ('simulation', 'qualification', 'parity_case', 'comparison'):
        monkeypatch.setattr(bootstrap, name, compose)
    arguments = [command, '--output', str(tmp_path / 'logs/fresh')]
    if command == 'compare':
        arguments += [
            '--first',
            str(first),
            '--second',
            str(second),
            '--duration-s',
            '0.1',
            '--trials',
            '1',
        ]
        error = ValueError
    else:
        arguments += ['--project', str(tmp_path)]
        error = ValidationError
    with pytest.raises(error, match='disposable logs'):
        cli.main(arguments)
    assert composed == []
