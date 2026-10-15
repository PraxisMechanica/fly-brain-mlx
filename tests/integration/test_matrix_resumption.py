import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from fly_brain import bootstrap
from fly_brain.comparison.models import SpikeSteps
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.matrix_diagnostics import CaseRasters
from fly_brain.qualification.models import ParityCase, QualificationRequest
from fly_brain.simulation.identifiers import FlyWireIds64
from fly_brain.simulation.models import Connectome, InputPin
from fly_brain.simulation.ports import StimulusGenerator
from tests.unit.test_stimuli import connectome
from tools import qualify_matrix
from tools.qualification_cases import VerifiedCase, read_index

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'fault', ('none', 'duplicate', 'reordered', 'unknown', 'missing')
)
def test_case_index_requires_a_unique_prescribed_prefix(
    tmp_path: Path, fault: str
) -> None:
    cases = required_cases()
    rows = [{'case': asdict(case), 'exit_code': 0} for case in cases[:2]]
    if fault == 'duplicate':
        rows[1] = rows[0]
    elif fault == 'reordered':
        rows.reverse()
    elif fault == 'unknown':
        rows[1]['case'] = asdict(ParityCase('silent', 7, cases[0].trial))
    elif fault == 'missing':
        rows.pop(0)
    index = tmp_path / 'matrix.json'
    index.write_text(json.dumps({'required_cases': 52, 'cases': rows}))
    if fault != 'none':
        with pytest.raises(ValueError, match='unique prescribed'):
            read_index(index)
    else:
        loaded = read_index(index)
        assert tuple(loaded) == cases[:2]
        assert loaded[cases[0]].directory == tmp_path / 'cases/sugar-1000-0'


@pytest.mark.parametrize(
    'mode', ('verify-only', 'missing-case', 'unaccepted', 'reviewed')
)
def test_resumption_uses_original_paths_and_launches_only_missing_cases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    project = Path(__file__).resolve().parents[2]
    previous, output = tmp_path / 'previous', tmp_path / 'resumed'
    previous.mkdir()
    cases = required_cases()
    rows: list[dict[str, object]] = []
    original_bytes: dict[Path, bytes] = {}
    for case in cases[:2]:
        directory = previous / 'cases' / qualify_matrix.case_name(case)
        directory.mkdir(parents=True)
        path = directory / 'case.json'
        path.write_text(
            json.dumps({'case': asdict(case), 'case_accepted': case == cases[0]})
        )
        original_bytes[path] = path.read_bytes()
        rows.append({'case': asdict(case), 'exit_code': 0 if case == cases[0] else 1})
    (previous / 'matrix.json').write_text(
        json.dumps({'required_cases': 52, 'cases': rows})
    )
    network = connectome()
    pin = InputPin('csv', 'parquet', len(network.neuron_ids), 0)

    def inputs(_: Path) -> tuple[Connectome, InputPin]:
        return network, pin

    def pinned_inputs():
        return inputs

    monkeypatch.setattr(bootstrap, 'pinned_inputs', pinned_inputs)

    def canonical(
        connectome: Connectome, pin: InputPin, output: Path, generate: StimulusGenerator
    ) -> dict[ParityCase, str]:
        return dict.fromkeys(cases, 'canonical')

    monkeypatch.setattr(qualify_matrix, 'canonical_inputs', canonical)
    script = Path(qualify_matrix.__file__).read_bytes()

    def git(command: list[str], **kwargs: object) -> str | bytes:
        return 'checkpoint' if kwargs.get('text') else script

    monkeypatch.setattr(qualify_matrix.subprocess, 'check_output', git)
    launched: list[Path] = []

    def execute(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        destination = Path(command[command.index('--output') + 1])
        launched.append(destination)
        destination.mkdir()
        (destination / 'case.json').write_text('{}')
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(qualify_matrix.subprocess, 'run', execute)
    empty = SpikeSteps(FlyWireIds64(np.empty(0, np.int64)), np.empty(0, np.int64))
    reviewed = mode in ('reviewed', 'missing-case')
    reviews = tmp_path / 'reviews'
    if reviewed:
        (reviews / 'sugar-1000-1').mkdir(parents=True)
    visited: list[Path] = []

    def verify(
        project: Path,
        directory: Path,
        case: ParityCase,
        connectome: Connectome,
        pin: InputPin,
        *,
        canonical_sha256: str,
        review: Path | None,
        bound_files: dict[str, str] | None,
    ) -> VerifiedCase:
        assert canonical_sha256 == 'canonical'
        visited.append(directory)
        return VerifiedCase(
            directory,
            'launch',
            CaseRasters(case, empty, empty, empty),
            case == cases[0] or (case == cases[1] and reviewed),
            {
                'case.json': hashlib.sha256(
                    (directory / 'case.json').read_bytes()
                ).hexdigest()
            },
            review,
            {'review-decision.json': 'bound-review'}
            if reviewed and case == cases[1]
            else {},
        )

    monkeypatch.setattr(qualify_matrix, 'verify_case', verify)
    result = qualify_matrix.run(
        QualificationRequest(project, output),
        resume_from=previous,
        reviews=reviews if reviewed else None,
        verify_only=mode in ('verify-only', 'reviewed'),
    )
    assert result['accepted'] is False
    assert result['complete'] is False
    assert visited[:2] == [
        previous / 'cases' / qualify_matrix.case_name(case) for case in cases[:2]
    ]
    assert launched == (
        [output / 'cases/sugar-1000-2'] if mode == 'missing-case' else []
    )
    for path, raw in original_bytes.items():
        assert path.read_bytes() == raw
    resumed = read_index(output / 'matrix.json')
    assert resumed[cases[0]].directory == previous / 'cases/sugar-1000-0'
    assert resumed[cases[0]].artifact_sha256 is not None
    if reviewed:
        assert resumed[cases[1]].review == reviews / 'sugar-1000-1'
        assert resumed[cases[1]].review_sha256 == {
            'review-decision.json': 'bound-review'
        }
