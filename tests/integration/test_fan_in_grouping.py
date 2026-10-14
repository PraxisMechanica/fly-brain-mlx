import sys
from pathlib import Path
from types import ModuleType
from typing import NoReturn

import numpy as np
import pytest
from numpy.typing import NDArray

from fly_brain.qualification.input_patterns import InputPatterns, InputPreparation
from fly_brain.simulation.identifiers import FlyWireIds64, NeuronRows32
from fly_brain.simulation.models import Connectome, DestinationGrouping, InputPin
from fly_brain.simulation.module import (
    build_absolute_count_reader,
    build_destination_grouping_reader,
)
from tests.quality.support import PROJECT
from tests.quality.test_reference_silencing_boundary import typed

pytestmark = pytest.mark.integration
SOURCE = PROJECT / 'src/fly_brain/qualification/adapters/fan_in_probe.py'
NATIVE = """from pathlib import Path
from api import run
from fly_brain.qualification.fan_in_ports import FanInCaseBuilder
from fly_brain.qualification.ports import DestinationGroupingReader
from fly_brain.simulation.models import Connectome, DestinationGrouping, InputPin
from fly_brain.simulation.module import build_absolute_count_reader, build_destination_grouping_reader
reader: DestinationGroupingReader = build_destination_grouping_reader()
def wrong(network: Connectome) -> int:
    return 0
def close(network: Connectome) -> DestinationGrouping:
    return reader(network)
def drive(network: Connectome, pin: InputPin, output: Path, cases: FanInCaseBuilder) -> dict[str, object]:
    return run(network, pin, output, '0', build_cases=cases, read_absolute_counts=build_absolute_count_reader(){keyword})
"""
PHASES = ('analysis', 'counts', 'completion', 'grouping', 'cases')


def payload(
    *values: NDArray[np.int32] | NDArray[np.int64] | NDArray[np.float64],
) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (value.dtype, value.shape, value.strides, value.tobytes()) for value in values
    )


def network_payload(network: Connectome) -> tuple[tuple[object, ...], ...]:
    return payload(
        network.neuron_ids,
        network.sources,
        network.destinations,
        network.counts,
        network.weights_mv,
    )


def check_types(root: Path, code: str, status: int, *diagnostics: str) -> None:
    result, output = typed(root, code)
    assert (result, all(item in output for item in diagnostics)) == (status, True), (
        output
    )


@pytest.fixture
def probe(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    core, metal = ModuleType('mlx.core'), ModuleType('mlx.core.metal')
    core.__dict__.update(metal=metal, disable_compile=lambda: None)
    metal.__dict__['is_available'] = lambda: True
    package = ModuleType('mlx')
    package.__dict__['core'] = core
    backend = ModuleType('fly_brain.simulation.backend.accumulation')

    def forbidden(*arguments: object) -> NoReturn:
        raise AssertionError('Grouping qualification must not run a backend')

    backend.__dict__['factored_sum'] = forbidden
    for dependency in (package, core, backend):
        monkeypatch.setitem(sys.modules, dependency.__name__, dependency)
    module = ModuleType('fan_in_grouping_probe')
    module.__dict__['__file__'] = str(SOURCE)
    exec(compile(SOURCE.read_bytes(), str(SOURCE), 'exec'), module.__dict__)
    return module


@pytest.mark.parametrize('failure', PHASES)
def test_reader_order_identity_and_failure_before_evaluation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: str, probe: ModuleType
) -> None:
    counts = np.array([4, -1, 0, 2], dtype=np.int32)
    network = Connectome(
        FlyWireIds64(np.arange(3, dtype=np.int64)),
        NeuronRows32(np.array([0, 2, 1, 2], dtype=np.int32)),
        NeuronRows32(np.array([1, 0, 0, 1], dtype=np.int32)),
        counts,
        counts.astype(np.float64) * 0.275,
    )
    output = tmp_path / 'fan-in'
    calls: list[str] = []
    original = probe.prepare_inputs
    complete = probe.analyze_inputs
    supplied = build_destination_grouping_reader()
    absolute = build_absolute_count_reader()
    before = network_payload(network)

    def observe(name: str, received: Connectome) -> None:
        calls.append(name)
        assert (received is network, output.is_dir()) == (True, True)
        assert not tuple(output.iterdir())
        if name == failure:
            raise ValueError('injected ' + name)

    def analyze(received: Connectome) -> InputPreparation:
        observe('analysis', received)
        return original(received)

    def read_absolute(received: Connectome) -> NDArray[np.int64]:
        observe('counts', received)
        return absolute(received)

    def finish(
        prepared: InputPreparation, *, absolute_counts: NDArray[np.int64]
    ) -> InputPatterns:
        observe('completion', network)
        return complete(prepared, absolute_counts=absolute_counts)

    def read(received: Connectome) -> DestinationGrouping:
        observe('grouping', received)
        return supplied(received)

    def cases(
        target: int,
        sources: NDArray[np.int32],
        counts: NDArray[np.int32],
        weights: NDArray[np.float64],
    ) -> NoReturn:
        calls.append('cases')
        assert target == 0
        edges = np.array([1, 2], dtype=np.int32)
        assert payload(sources, counts, weights) == payload(
            network.sources[edges], network.counts[edges], network.weights_mv[edges]
        )
        raise ValueError('injected cases')

    def version(package: str) -> str:
        return {'mlx': '0.32.3', 'mlx-metal': '0.32.3'}[package]

    monkeypatch.setattr(probe.mx, 'disable_compile', lambda: calls.append('disable'))
    monkeypatch.setattr(probe.importlib.metadata, 'version', version)
    monkeypatch.setattr(probe, 'prepare_inputs', analyze)
    monkeypatch.setattr(probe, 'analyze_inputs', finish)
    with pytest.raises(ValueError, match='^injected ' + failure + '$'):
        probe.run(
            network,
            InputPin('csv', 'parquet', 3, 4),
            output,
            '0',
            build_cases=cases,
            read_grouping=read,
            read_absolute_counts=read_absolute,
        )
    observed = (calls, network_payload(network), probe.run.__defaults__)
    assert observed == (
        ['disable', *PHASES[: PHASES.index(failure) + 1]],
        before,
        (
            probe.evaluate_cases,
            'Isolated pinned-data fan-in qualification; not a full-network run.',
        ),
    )


@pytest.mark.checker
def test_required_reader_omission_repair_and_independent_weakening(
    tmp_path: Path,
) -> None:
    source = SOURCE.read_text()
    (tmp_path / 'api.py').write_text(source)
    check_types(
        tmp_path,
        NATIVE.format(keyword=''),
        1,
        'consumer.py:',
        '"read_grouping"',
    )
    check_types(tmp_path, NATIVE.format(keyword=', read_grouping=reader'), 0)
    weakened = source.replace(
        'from fly_brain.simulation.models import Connectome, InputPin',
        'from fly_brain.simulation.mapping import group_destinations\n'
        'from fly_brain.simulation.models import Connectome, InputPin',
    ).replace(
        'read_grouping: DestinationGroupingReader,',
        'read_grouping: DestinationGroupingReader = group_destinations,',
    )
    assert weakened != source
    (tmp_path / 'api.py').write_text(weakened)
    check_types(tmp_path, NATIVE.format(keyword=''), 0)


@pytest.mark.checker
@pytest.mark.parametrize(
    'reader,status,diagnostic',
    (('wrong', 1, 'reportArgumentType'), ('close', 0, '0 errors')),
)
def test_actual_required_port_rejects_wrong_result_and_accepts_close_shape(
    tmp_path: Path, reader: str, status: int, diagnostic: str
) -> None:
    (tmp_path / 'api.py').write_text(SOURCE.read_text())
    check_types(
        tmp_path, NATIVE.format(keyword=', read_grouping=' + reader), status, diagnostic
    )
