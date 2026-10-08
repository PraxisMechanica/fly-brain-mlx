import builtins
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

from fly_brain import bootstrap
from fly_brain.comparison import commands as comparison_commands
from fly_brain.comparison.models import ComparisonRequest, ComparisonResult, Spikes
from fly_brain.comparison.module import build_comparison
from fly_brain.infrastructure.seeded_random import uniforms
from fly_brain.qualification import commands as qualification_commands
from fly_brain.qualification.fan_in_ports import FanInCaseBuilder
from fly_brain.qualification.models import (
    ParityCase,
    QualificationRequest,
    QualificationResult,
)
from fly_brain.qualification.models import (
    TestCounts as Counts,
)
from fly_brain.qualification.module import (
    build_input_probe,
    build_output_probe,
    build_parity_case,
    build_project_probe,
    build_qualification,
)
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
from fly_brain.simulation.module import (
    build_pinned_inputs,
    build_simulation,
    build_stimulus,
)
from fly_brain.simulation.ports import (
    Clock,
    ConnectomeReader,
    PinnedInputs,
)

pytestmark = pytest.mark.unit


def empty_connectome() -> Connectome:
    return Connectome(
        np.array([10, 20], dtype=np.int64),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )


def test_pinned_reader_is_created_and_called_only_at_the_load_stage() -> None:
    calls: list[object] = []
    connectome = empty_connectome()

    def read(completeness: Path, connectivity: Path, pin: InputPin) -> Connectome:
        calls.append((completeness, connectivity, pin))
        return connectome

    def reader_factory() -> ConnectomeReader:
        calls.append('reader')
        return read

    load = build_pinned_inputs(reader_factory)
    assert calls == []
    loaded, pin = load(Path('/project'))
    assert loaded is connectome
    assert pin == InputPin(
        '52b0ac6094cd32c546f8d4c341e094376f48f4e791f8db9b166de5dff8199ea4',
        'efeb23fb99098e9c390f6869969b2a121a2ee92c833cfc45ecb2c1d8e1af0347',
        138639,
        15091983,
    )
    assert calls == [
        'reader',
        (
            Path('/project/data/2025_Completeness_783.csv'),
            Path('/project/data/2025_Connectivity_783.parquet'),
            pin,
        ),
    ]


@pytest.mark.parametrize('accepted', (True, False))
def test_qualification_runs_and_writes_only_when_the_owned_command_is_called(
    capsys: pytest.CaptureFixture[str], accepted: bool
) -> None:
    request = QualificationRequest(Path('/project'), Path('/fresh'))
    result = QualificationResult(('pytest',), 0, Counts(1, 0, 0, int(not accepted)))
    calls: list[object] = []

    def runner(value: QualificationRequest) -> QualificationResult:
        calls.append(value)
        return result

    def writer(value: QualificationRequest, observed: QualificationResult) -> None:
        calls.append((value, observed))

    command = build_qualification(runner, writer)
    assert calls == []
    assert command(request) == (0 if accepted else 1)
    assert calls == [request, (request, result)]
    assert (
        capsys.readouterr().out
        == json.dumps({'accepted': accepted, 'exit_code': 0}, indent=2) + '\n'
    )


@pytest.mark.parametrize('report', ({'accepted': True}, {'accepted': False}, {}))
def test_project_and_output_diagnostics_preserve_report_and_exit_contracts(
    capsys: pytest.CaptureFixture[str], report: dict[str, object]
) -> None:
    request = QualificationRequest(Path('/project'), Path('/fresh'))
    calls: list[object] = []

    def project_probe(project: Path, output: Path) -> dict[str, object]:
        calls.append((project, output))
        return report

    def output_probe(output: Path) -> dict[str, object]:
        calls.append(output)
        return report

    commands = (build_project_probe(project_probe), build_output_probe(output_probe))
    assert calls == []
    for command in commands:
        exit_code = command(request)
        assert exit_code == (0 if report.get('accepted', True) else 1)
        displayed = json.loads(capsys.readouterr().out)
        assert (displayed['summary'], displayed['output'], displayed['exit_code']) == (
            report,
            str(request.output),
            exit_code,
        )
    assert calls == [(request.project, request.output), request.output]


def test_input_audit_passes_the_loaded_identity_to_one_probe(
    capsys: pytest.CaptureFixture[str],
) -> None:
    request = QualificationRequest(Path('/project'), Path('/fresh'))
    connectome, pin = empty_connectome(), InputPin('csv', 'parquet', 2, 0)
    calls: list[object] = []

    def load(project: Path) -> tuple[Connectome, InputPin]:
        calls.append(project)
        return connectome, pin

    def probe(network: Connectome, inputs: InputPin, output: Path) -> dict[str, object]:
        assert network is connectome and inputs is pin
        calls.append(output)
        return {'accepted': True}

    command = build_input_probe(load, probe)
    assert calls == []
    assert command(request) == 0
    assert calls == [request.project, request.output]
    displayed = json.loads(capsys.readouterr().out)
    assert (displayed['summary'], displayed['output']) == (
        {'accepted': True},
        str(request.output),
    )


@pytest.mark.parametrize('accepted', (True, False))
def test_parity_loads_before_one_probe_and_preserves_the_summary(
    capsys: pytest.CaptureFixture[str], accepted: bool
) -> None:
    project, output, case = Path('/project'), Path('/fresh'), ParityCase('p9', 1000, 4)
    connectome, pin = empty_connectome(), InputPin('csv', 'parquet', 2, 0)
    calls: list[object] = []
    report: dict[str, object] = {
        'case': {'experiment': 'p9', 'steps': 1000, 'trial': 4},
        'case_accepted': accepted,
        'scientific_review_required': not accepted,
        'private_diagnostic': 'retained in the case report',
    }

    def load(value: Path) -> tuple[Connectome, InputPin]:
        calls.append(value)
        return connectome, pin

    def probe(
        network: Connectome, inputs: InputPin, selected: ParityCase, destination: Path
    ) -> dict[str, object]:
        assert network is connectome and inputs is pin
        calls.append((selected, destination))
        return report

    command = build_parity_case(load, probe)
    assert calls == []
    assert command(project, output, case) == (0 if accepted else 1)
    assert calls == [project, (case, output)]
    assert (
        capsys.readouterr().out
        == json.dumps(
            {
                'case': report['case'],
                'case_accepted': accepted,
                'scientific_review_required': not accepted,
                'report': '/fresh/case.json',
            },
            indent=2,
        )
        + '\n'
    )


def test_comparison_reads_in_order_and_writes_before_printing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    request = ComparisonRequest(Path('/first'), Path('/second'), 0.1, 1, 0.1, 'a', 'b')
    output = Path('/fresh')
    spikes = Spikes(
        np.array([0], dtype=np.int16),
        np.array([10], dtype=np.int64),
        np.array([0.001], dtype=np.float64),
    )
    calls: list[object] = []
    results: list[ComparisonResult] = []

    def reader(path: Path, duration_s: float) -> Spikes:
        calls.append((path, duration_s))
        return spikes

    def writer(destination: Path, result: ComparisonResult) -> None:
        assert capsys.readouterr().out == ''
        calls.append(destination)
        results.append(result)

    command = build_comparison(reader, writer)
    assert calls == []
    assert command(request, output) == 0
    assert calls == [(request.first, 0.1), (request.second, 0.1), output]
    assert capsys.readouterr().out == json.dumps(results[0].summary, indent=2) + '\n'
    assert results[0].summary['timing_f1'] == 1.0
    assert results[0].rates[0]['flywire_id'] == 10


def test_simulation_preserves_stage_order_clock_calls_and_result_format(
    capsys: pytest.CaptureFixture[str],
) -> None:
    request = SimulationRequest(Path('/project'), Path('/fresh'), 'silent', 0.001, 1, 0)
    connectome, pin = empty_connectome(), InputPin('csv', 'parquet', 2, 0)
    events = SpikeEvents(*(np.array([], dtype=np.int64) for _ in range(3)))
    run = SimulationRun(events, {}, 0, 'test')
    result = SimulationResult(Path('/fresh/spikes.parquet'), 0, 0, 13.0)
    calls: list[object] = []
    times = iter((100.0, 102.0, 105.0, 108.0, 109.0, 113.0))

    def clock() -> float:
        value = next(times)
        calls.append(value)
        return value

    def load(project: Path) -> tuple[Connectome, InputPin]:
        calls.append(project)
        return connectome, pin

    def persist(
        output: Path, experiment: Experiment, inputs: InputPin, stimulus: Stimulus
    ) -> Stimulus:
        assert experiment.name == 'silent' and inputs is pin
        assert stimulus.events.shape == (1, 10, 0)
        calls.append(output)
        return stimulus

    def execute(
        network: Connectome, stimulus: Stimulus, silenced: tuple[int, ...]
    ) -> SimulationRun:
        assert network is connectome and silenced == ()
        calls.append('execute')
        return run

    def write(
        value: SimulationRequest,
        network: Connectome,
        inputs: InputPin,
        stimulus: Stimulus,
        completed: SimulationRun,
        timings: dict[str, float],
        started: float,
    ) -> SimulationResult:
        assert value is request and network is connectome and inputs is pin
        assert completed is run
        calls.append((timings, started))
        return result

    command = build_simulation(
        load, persist, execute, write, clock, build_stimulus(uniforms)
    )
    assert calls == []
    assert command(request) == 0
    assert calls == [
        100.0,
        request.project,
        102.0,
        105.0,
        108.0,
        109.0,
        request.output,
        113.0,
        'execute',
        ({'data_load_s': 2.0, 'schedule_s': 3.0, 'stimulus_io_s': 4.0}, 100.0),
    ]
    assert (
        capsys.readouterr().out
        == json.dumps(
            {
                'spike_file': '/fresh/spikes.parquet',
                'spikes': 0,
                'active_neurons': 0,
                'elapsed_s': 13.0,
            },
            indent=2,
        )
        + '\n'
    )


FACTORIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ('qualification', ('pytest_runner', 'results', 'configure')),
    ('comparison', ('comparison.storage',)),
    ('accumulation', ('configure', 'accumulation_probe')),
    ('factored', ('configure', 'factored_probe')),
    ('bucketed_scalars', ('configure', 'bucketed_scalars')),
    ('replay', ('replay_probe',)),
    ('schedule', ('schedule_probe',)),
    ('input_audit', ('connectome_probe',)),
    ('fan_in_audit', ('configure', 'fan_in_probe')),
    ('layout_fan_in_audit', ('configure', 'bucketed_fan_in', 'fan_in_probe')),
    ('device_layout_audit', ('configure', 'device_layout_probe')),
    ('connectome_pulse', ('configure', 'connectome_pulse')),
    ('simulation', ('configure', 'simulation.backend.runner', 'simulation.storage')),
    ('parity_case', ('configure', 'torch', 'parity_case', 'threads:1')),
)


@pytest.mark.parametrize('factory,expected', FACTORIES)
def test_bootstrap_factories_preserve_configuration_order_without_workflow_effects(
    monkeypatch: pytest.MonkeyPatch, factory: str, expected: tuple[str, ...]
) -> None:
    events: list[str] = []

    def forbidden(*values: object, **options: object) -> object:
        raise AssertionError('Composition executed a runtime collaborator')

    def configure() -> str:
        events.append('configure')
        return '0'

    def threads(count: int) -> None:
        events.append(f'threads:{count}')

    def reader_factory() -> ConnectomeReader:
        raise AssertionError('Composition created the lazy input reader')

    names = {
        'fly_brain.qualification.adapters.' + name
        for name in (
            'pytest_runner',
            'results',
            'accumulation_probe',
            'factored_probe',
            'bucketed_scalars',
            'replay_probe',
            'schedule_probe',
            'connectome_probe',
            'fan_in_probe',
            'bucketed_fan_in',
            'device_layout_probe',
            'connectome_pulse',
            'parity_case',
        )
    } | {
        'fly_brain.simulation.backend.runner',
        'fly_brain.simulation.storage',
        'fly_brain.comparison.storage',
        'torch',
    }
    for name in names:
        module = ModuleType(name)
        for attribute in (
            'run',
            'run_tests',
            'write_result',
            'read_spikes',
            'write_comparison',
            'persist_stimulus',
            'write_run',
            'evaluate_cases',
            'set_num_threads',
        ):
            setattr(
                module,
                attribute,
                threads if attribute == 'set_num_threads' else forbidden,
            )
        monkeypatch.setitem(sys.modules, name, module)

    observations = ModuleType('fly_brain.simulation.observation_module')
    observations.__dict__['build_observation_assembly'] = lambda: forbidden
    monkeypatch.setitem(sys.modules, observations.__name__, observations)

    importing = builtins.__import__

    def observe_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: Sequence[str] = (),
        level: int = 0,
    ) -> ModuleType:
        if name in names:
            if name.startswith('fly_brain.qualification.adapters.'):
                events.append(name.rsplit('.', 1)[1])
            else:
                events.append(name.removeprefix('fly_brain.'))
        return importing(name, globals, locals, fromlist, level)

    monkeypatch.setattr(bootstrap, 'configure_mlx', configure)
    monkeypatch.setattr(bootstrap, 'build_connectome_reader', reader_factory)
    monkeypatch.setattr(builtins, '__import__', observe_import)
    command: object = getattr(bootstrap, factory)()
    assert callable(command)
    assert events == list(expected)


def test_layout_fan_in_factory_preserves_precision_evaluator_and_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = QualificationRequest(Path('/project'), Path('/fresh'))
    connectome, pin = empty_connectome(), InputPin('csv', 'parquet', 2, 0)
    calls: list[object] = []

    def load(project: Path) -> tuple[Connectome, InputPin]:
        calls.append(project)
        return connectome, pin

    def compose_inputs() -> PinnedInputs:
        return load

    def evaluator() -> None:
        raise AssertionError('Wiring must not evaluate cases')

    def run(
        network: Connectome,
        inputs: InputPin,
        output: Path,
        precision: str,
        evaluator: object,
        scope: str,
        build_cases: FanInCaseBuilder,
    ) -> dict[str, object]:
        assert network is connectome and inputs is pin
        assert callable(build_cases)
        calls.append((output, precision, evaluator, scope))
        return {'accepted': True}

    fan_in = ModuleType('fly_brain.qualification.adapters.fan_in_probe')
    layout = ModuleType('fly_brain.qualification.adapters.bucketed_fan_in')
    for module, name, value in (
        (fan_in, 'run', run),
        (layout, 'evaluate_cases', evaluator),
    ):
        setattr(module, name, value)
        monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(bootstrap, 'configure_mlx', lambda: '0')
    monkeypatch.setattr(bootstrap, 'pinned_inputs', compose_inputs)
    command = bootstrap.layout_fan_in_audit()
    assert calls == []
    assert command(request) == 0
    assert calls == [
        request.project,
        (
            request.output,
            '0',
            evaluator,
            'All prescribed pinned fan-in cases through production layout; not full-network dynamics.',
        ),
    ]


def test_simulation_factory_shares_the_injected_clock_with_the_result_writer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = SimulationRequest(Path('/project'), Path('/fresh'), 'silent', 0.001, 1, 0)
    connectome = empty_connectome()
    events = SpikeEvents(*(np.array([], dtype=np.int64) for _ in range(3)))
    run = SimulationRun(events, {}, 0, 'test')
    result = SimulationResult(Path('/fresh/spikes.parquet'), 0, 0, 13.0)
    calls: list[object] = []
    times = iter((100.0, 102.0, 105.0, 108.0, 109.0, 113.0, 114.0))

    def timed_clock() -> float:
        value = next(times)
        calls.append(value)
        return value

    def read(completeness: Path, connectivity: Path, pin: InputPin) -> Connectome:
        calls.append('read')
        return connectome

    def reader_factory() -> ConnectomeReader:
        calls.append('reader')
        return read

    def persist(
        output: Path, experiment: Experiment, pin: InputPin, stimulus: Stimulus
    ) -> Stimulus:
        calls.append('persist')
        return stimulus

    def execute(
        network: Connectome,
        stimulus: Stimulus,
        silenced: tuple[int, ...],
        *,
        precision: str,
    ) -> SimulationRun:
        calls.append(('execute', precision))
        return run

    def write(
        request: SimulationRequest,
        network: Connectome,
        pin: InputPin,
        stimulus: Stimulus,
        completed: SimulationRun,
        timings: dict[str, float],
        started: float,
        clock: Clock,
    ) -> SimulationResult:
        assert clock is timed_clock
        calls.append(('write', timings, started))
        clock()
        return result

    runner = ModuleType('fly_brain.simulation.backend.runner')
    storage = ModuleType('fly_brain.simulation.storage')
    for module, name, value in (
        (runner, 'run', execute),
        (storage, 'persist_stimulus', persist),
        (storage, 'write_run', write),
    ):
        setattr(module, name, value)
        monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(bootstrap, 'configure_mlx', lambda: '0')
    monkeypatch.setattr(bootstrap, 'build_connectome_reader', reader_factory)
    monkeypatch.setattr(bootstrap, 'perf_counter', timed_clock)
    command = bootstrap.simulation()
    assert calls == []
    assert command(request) == 0
    assert calls == [
        100.0,
        'reader',
        'read',
        102.0,
        105.0,
        108.0,
        109.0,
        'persist',
        113.0,
        ('execute', '0'),
        ('write', {'data_load_s': 2.0, 'schedule_s': 3.0, 'stimulus_io_s': 4.0}, 100.0),
        114.0,
    ]


def test_owned_diagnostic_command_propagates_use_case_failures() -> None:
    def fail(request: QualificationRequest) -> dict[str, object]:
        raise ValueError('failure')

    with pytest.raises(ValueError, match='failure'):
        qualification_commands.diagnostic(
            QualificationRequest(Path('/project'), Path('/fresh')), fail
        )


def test_owned_comparison_command_propagates_use_case_failures() -> None:
    def fail(request: ComparisonRequest, output: Path) -> ComparisonResult:
        raise ValueError('failure')

    request = ComparisonRequest(Path('/first'), Path('/second'), 0.1, 1, 0.1, 'a', 'b')
    with pytest.raises(ValueError, match='failure'):
        comparison_commands.comparison(request, Path('/fresh'), fail)
