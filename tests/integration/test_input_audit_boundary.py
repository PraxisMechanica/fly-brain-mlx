import hashlib
import subprocess
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import ParamSpec, TypeVar

import pytest

from fly_brain.qualification.adapters.connectome_probe import InputAuditRepository
from fly_brain.qualification.input_audit_service import run
from fly_brain.qualification.ports import InputAuditFiles
from fly_brain.simulation.models import Connectome, InputPin
from fly_brain.simulation.module import (
    build_absolute_count_reader,
    build_connectome_silencer,
    build_destination_buckets_reader,
    build_destination_grouping_reader,
)
from tests.quality.support import PROJECT
from tests.support.observation_fixtures import fixture

pytestmark = pytest.mark.integration
BASE = '2d0a7e6b80374fe95f8a6ae492bd298f1bb2dcd1'
SOURCE = 'src/fly_brain/qualification/adapters/connectome_probe.py'
ORIGINAL_SHA256 = 'd80ff290f21c0510ab5677430f9750394245b655cf77c65ddf5981ffeae51310'
PHASES = ('grouping', 'counts', 'silence', 'buckets')
P = ParamSpec('P')
Value = TypeVar('Value')


def baseline() -> ModuleType:
    source = subprocess.check_output(
        ['git', '-C', str(PROJECT), 'show', BASE + ':' + SOURCE]
    )
    assert hashlib.sha256(source).hexdigest() == ORIGINAL_SHA256
    module = ModuleType('original_input_audit')
    exec(compile(source, SOURCE, 'exec'), module.__dict__)
    return module


def payload(connectome: Connectome) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            str(value.dtype),
            value.shape,
            value.strides,
            value.flags.writeable,
            value.tobytes(),
        )
        for value in (
            connectome.neuron_ids,
            connectome.sources,
            connectome.destinations,
            connectome.counts,
            connectome.weights_mv,
        )
    )


def traced(
    name: str,
    operation: Callable[P, Value],
    calls: list[str],
    output: Path,
    fail_at: str | None,
) -> Callable[P, Value]:
    def execute(*arguments: P.args, **options: P.kwargs) -> Value:
        calls.append(name)
        assert (
            output.is_dir(),
            (output / 'mapped-inputs.npz').exists(),
            (output / 'mapping.json').exists(),
        ) == (True, name == 'buckets', False)
        if name == fail_at:
            raise ValueError('injected ' + name)
        return operation(*arguments, **options)

    return execute


def current(
    connectome: Connectome,
    pin: InputPin,
    output: Path,
    calls: list[str],
    fail_at: str | None,
    files: InputAuditFiles,
) -> dict[str, object]:
    return run(
        connectome,
        pin,
        output,
        read_grouping=traced(
            'grouping', build_destination_grouping_reader(), calls, output, fail_at
        ),
        read_absolute_counts=traced(
            'counts', build_absolute_count_reader(), calls, output, fail_at
        ),
        silence=traced('silence', build_connectome_silencer(), calls, output, fail_at),
        read_buckets=traced(
            'buckets', build_destination_buckets_reader(), calls, output, fail_at
        ),
        files=files,
    )


def test_actual_host_driver_preserves_every_archive_and_report_byte(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connectome = fixture().connectome
    pin = InputPin('csv', 'parquet', 6, 8)
    before = payload(connectome)
    roots = (tmp_path / 'original', tmp_path / 'current')
    for root in roots:
        root.mkdir()
    monkeypatch.chdir(roots[0])
    expected = baseline().run(connectome, pin, Path('audit'))
    monkeypatch.chdir(roots[1])
    calls: list[str] = []
    actual = current(
        connectome, pin, Path('audit'), calls, None, InputAuditRepository()
    )
    assert (actual, calls, payload(connectome)) == (expected, list(PHASES), before)
    for name in ('mapped-inputs.npz', 'mapping.json'):
        assert (roots[1] / 'audit' / name).read_bytes() == (
            roots[0] / 'audit' / name
        ).read_bytes()
    print('preserved archive sha256', actual['artifact_sha256'])


@pytest.mark.parametrize('phase', PHASES)
def test_callback_errors_keep_original_directory_and_file_positions(
    tmp_path: Path,
    phase: str,
) -> None:
    calls: list[str] = []
    output = tmp_path / 'audit'
    with pytest.raises(ValueError, match='injected ' + phase):
        current(
            fixture().connectome,
            InputPin('csv', 'parquet', 6, 8),
            output,
            calls,
            phase,
            InputAuditRepository(),
        )
    assert calls == list(PHASES[: PHASES.index(phase) + 1])
    with pytest.raises(FileExistsError):
        current(
            fixture().connectome,
            InputPin('csv', 'parquet', 6, 8),
            output,
            calls,
            None,
            InputAuditRepository(),
        )
    assert calls == list(PHASES[: PHASES.index(phase) + 1])


def test_empty_edge_error_still_follows_archive_and_precedes_bucket_acquisition(
    tmp_path: Path,
) -> None:
    connectome = fixture(True).connectome
    pin = InputPin('csv', 'parquet', 6, 0)
    calls: list[str] = []
    output = tmp_path / 'current'
    with pytest.raises(ValueError) as original:
        baseline().run(connectome, pin, tmp_path / 'original')
    with pytest.raises(ValueError) as actual:
        current(connectome, pin, output, calls, None, InputAuditRepository())
    assert (
        str(actual.value),
        calls,
        (output / 'mapped-inputs.npz').exists(),
        (output / 'mapping.json').exists(),
    ) == (
        str(original.value),
        list(PHASES[:3]),
        True,
        False,
    )
