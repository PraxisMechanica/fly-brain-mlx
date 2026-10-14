from collections.abc import Mapping
from pathlib import Path, PosixPath
from typing import NoReturn

import pytest

from fly_brain.qualification.adapters.connectome_probe import InputAuditRepository
from fly_brain.qualification.models import InputAuditArtifact, MappedArray
from fly_brain.qualification.module import build_host_input_probe
from fly_brain.qualification.ports import InputAuditFiles
from fly_brain.simulation.models import InputPin
from tests.integration.test_input_audit_boundary import current
from tests.quality.support import PROJECT
from tests.quality.test_input_audit_boundary import TYPES, contract, sources
from tests.quality.test_parity_stimulus_boundary import lint
from tests.quality.test_reference_silencing_boundary import typed
from tests.support.observation_fixtures import fixture

pytestmark = pytest.mark.integration
RULE = 'DEP001: Host input audit uses injected file storage'
SOURCES = (
    'fly_brain.qualification.input_audit_service',
    'fly_brain.qualification.input_audit_rules',
)
REPOSITORY = 'fly_brain.qualification.adapters.connectome_probe'
STAGES = (
    'directory',
    'grouping',
    'counts',
    'silence',
    'npz',
    'identity',
    'buckets',
    'json',
)
OPERATIONS = ('create_output', 'write_arrays', 'read_artifact_identity', 'write_report')


class IdentityPath(PosixPath):
    calls: list[str]

    def __str__(self) -> str:
        self.calls.append('str')
        return super().__str__()

    def read_bytes(self) -> bytes:
        self.calls.append('read')
        return super().read_bytes()


class RecordedFiles:
    def __init__(
        self, delegate: InputAuditFiles, calls: list[str], failure: str | None
    ) -> None:
        self.delegate, self.calls, self.failure = delegate, calls, failure
        self.artifact: Path | None = None

    def record(self, phase: str) -> None:
        self.calls.append(phase)
        if phase == self.failure:
            raise OSError('injected ' + phase)

    def create_output(self, output: Path, /) -> None:
        self.record('directory')
        self.delegate.create_output(output)

    def write_arrays(self, output: Path, arrays: Mapping[str, MappedArray], /) -> Path:
        self.record('npz')
        result = IdentityPath(self.delegate.write_arrays(output, arrays))
        result.calls = self.calls
        self.artifact = result
        return result

    def read_artifact_identity(self, artifact: Path, /) -> InputAuditArtifact:
        self.record('identity')
        assert artifact is self.artifact
        return self.delegate.read_artifact_identity(artifact)

    def write_report(self, output: Path, report: dict[str, object], /) -> None:
        self.record('json')
        self.delegate.write_report(output, report)


@pytest.mark.parametrize(
    'failure', (None, 'directory', 'npz', 'identity', 'json', 'empty-header')
)
def test_storage_and_header_failures_keep_exact_phases_and_returned_path(
    tmp_path: Path,
    failure: str | None,
) -> None:
    calls: list[str] = []
    files = RecordedFiles(InputAuditRepository(), calls, failure)
    connectome = fixture(failure == 'empty-header').connectome
    output = tmp_path / 'audit'
    if failure is None:
        current(
            connectome, InputPin('csv', 'parquet', 6, 8), output, calls, None, files
        )
    else:
        with pytest.raises(ValueError if failure == 'empty-header' else OSError):
            current(
                connectome, InputPin('csv', 'parquet', 6, 8), output, calls, None, files
            )
    expected = (
        STAGES
        if failure is None
        else STAGES[:5]
        if failure == 'empty-header'
        else STAGES[: STAGES.index(failure) + 1]
    )
    assert (
        tuple(phase for phase in calls if phase in STAGES),
        output.is_dir(),
        (output / 'mapped-inputs.npz').exists(),
        (output / 'mapping.json').exists(),
    ) == (
        expected,
        failure != 'directory',
        failure not in ('directory', 'npz'),
        failure is None,
    )
    if failure in (None, 'json'):
        assert calls[calls.index('identity') + 1 : calls.index('identity') + 3] == [
            'str',
            'read',
        ]


def test_owned_assembly_performs_no_storage_or_mapping_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*arguments: object, **options: object) -> NoReturn:
        raise AssertionError('Assembly executed an operation')

    for operation in OPERATIONS:
        monkeypatch.setattr(InputAuditRepository, operation, forbidden)
    assert callable(build_host_input_probe(forbidden, forbidden, forbidden, forbidden))


@pytest.mark.parametrize('source', SOURCES)
def test_actual_storage_contract_rejects_direct_and_transitive_paths_then_repairs(
    tmp_path: Path,
    source: str,
) -> None:
    config = sources(
        tmp_path, REPOSITORY, f'from {REPOSITORY} import VALUE as hidden\n', source
    )
    config.write_text(contract(RULE))
    path = tmp_path / 'src' / Path(*source.split('.')).with_suffix('.py')
    for code in (
        f'from {REPOSITORY} import VALUE as hidden\n',
        'from fly_brain.qualification.mapping_helper import VALUE as neutral\n',
    ):
        path.write_text(code)
        result, output = lint(tmp_path, config)
        assert (
            result != 0,
            RULE in output,
            source in output,
            REPOSITORY in output,
            '(l.1)' in output,
        ) == (True,) * 5
    config.write_text(
        contract(RULE).replace(
            'allow_indirect_imports = false', 'allow_indirect_imports = true'
        )
    )
    assert lint(tmp_path, config)[0] == 0
    config.write_text(contract(RULE))
    path.write_text('from fly_brain.qualification.ports import VALUE\n')
    assert (lint(tmp_path, config)[0], lint(PROJECT, config)[0]) == (0, 0)
    path.write_text('# import connectome_probe\nVALUE = "storage"\n')
    assert lint(tmp_path, config)[0] == 0


def test_required_storage_port_rejects_omission_and_wrong_shape_then_repairs(
    tmp_path: Path,
) -> None:
    result, output = typed(tmp_path, TYPES.replace('files=files, ', ''))
    assert result == 1 and 'consumer.py:' in output and '"files"' in output
    result, output = typed(tmp_path, TYPES.replace('files=files, ', 'files=object(), '))
    assert result == 1 and 'reportArgumentType' in output
    assert (
        typed(
            tmp_path,
            TYPES
            + '\nfrom fly_brain.qualification.adapters.connectome_probe import InputAuditRepository\nprovided: InputAuditFiles = InputAuditRepository()\n',
        )[0]
        == 0
    )
