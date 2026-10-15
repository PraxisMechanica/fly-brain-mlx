import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypeVar

import numpy as np
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
from tests.support.observation_fixtures import fixture

pytestmark = pytest.mark.integration
PHASES = ('grouping', 'counts', 'silence', 'buckets')
P = ParamSpec('P')
Value = TypeVar('Value')


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


def test_host_audit_persists_actual_inputs_grouping_and_report(tmp_path: Path) -> None:
    connectome = fixture().connectome
    pin = InputPin('csv', 'parquet', 6, 8)
    before = payload(connectome)
    output = tmp_path / 'audit'
    calls: list[str] = []
    actual = current(connectome, pin, output, calls, None, InputAuditRepository())
    assert (calls, payload(connectome)) == (list(PHASES), before)
    assert json.loads((output / 'mapping.json').read_text()) == actual
    assert (
        actual['artifact_sha256']
        == hashlib.sha256((output / 'mapped-inputs.npz').read_bytes()).hexdigest()
    )
    expected = {
        'neuron_ids': connectome.neuron_ids,
        'sources': connectome.sources,
        'destinations': connectome.destinations,
        'signed_counts': connectome.counts,
        'weights_mv': connectome.weights_mv,
        'grouped_edge_ids': np.array([2, 5, 0, 1, 3, 4, 6, 7], dtype=np.int32),
        'inverse_grouping': np.array([2, 3, 0, 4, 5, 1, 6, 7], dtype=np.int32),
        'destination_offsets': np.array([0, 2, 4, 5, 6, 6, 8], dtype=np.int64),
        'absolute_count_sums': np.array([361, 360, 2, 3, 0, 2], dtype=np.int64),
    }
    with np.load(output / 'mapped-inputs.npz') as archive:
        assert set(archive.files) == set(expected)
        for name, value in expected.items():
            assert (
                archive[name].dtype,
                archive[name].shape,
                archive[name].tobytes(),
            ) == (value.dtype, value.shape, value.tobytes()), name


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
    with pytest.raises(ValueError, match='zero-size array'):
        current(connectome, pin, output, calls, None, InputAuditRepository())
    assert (
        calls,
        (output / 'mapped-inputs.npz').exists(),
        (output / 'mapping.json').exists(),
    ) == (
        list(PHASES[:3]),
        True,
        False,
    )
