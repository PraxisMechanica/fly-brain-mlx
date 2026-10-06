from pathlib import Path

import pytest
from pydantic import ValidationError

from fly_brain import bootstrap
from fly_brain.cli import main
from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.ports import ParityCommand
from fly_brain.qualification.schemas import ParityOptions

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('case', required_cases())
def test_boundary_accepts_every_frozen_case(tmp_path: Path, case: ParityCase) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    options = ParityOptions(
        project=tmp_path,
        output=tmp_path / 'fresh',
        experiment=case.experiment,
        duration_s=case.steps * 0.0001,
        trial=case.trial,
    )
    assert options.to_case() == case


@pytest.mark.parametrize(
    'experiment,duration,trial',
    (
        ('p9', 0.2, 0),
        ('silent', 0.1, 1),
        ('sugar-silenced', 10, 0),
        ('two-class', 10, 0),
        ('sugar', 0.1, -1),
        ('sugar', 0.1, 5),
        ('sugar', float('nan'), 0),
        ('sugar', float('inf'), 0),
    ),
)
def test_boundary_rejects_unprescribed_cases(
    tmp_path: Path, experiment: str, duration: float, trial: int
) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    with pytest.raises(ValidationError):
        ParityOptions.model_validate(
            {
                'project': tmp_path,
                'output': tmp_path / 'fresh',
                'experiment': experiment,
                'duration_s': duration,
                'trial': trial,
            }
        )


@pytest.mark.parametrize('accepted', (True, False))
def test_command_dispatches_validated_case_and_reports_its_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, accepted: bool
) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    calls: list[tuple[Path, Path, ParityCase]] = []

    def use_case(project: Path, output: Path, case: ParityCase) -> dict[str, object]:
        calls.append((project, output, case))
        return {
            'case': {
                'experiment': case.experiment,
                'steps': case.steps,
                'trial': case.trial,
            },
            'case_accepted': accepted,
            'scientific_review_required': not accepted,
        }

    def compose() -> ParityCommand:
        from functools import partial

        from fly_brain.qualification.commands import parity_case

        return partial(parity_case, use_case=use_case)

    monkeypatch.setattr(bootstrap, 'parity_case', compose)
    code = main(
        [
            'qualify-parity',
            '--project',
            str(tmp_path),
            '--output',
            str(tmp_path / 'case'),
            '--experiment',
            'p9',
            '--trial',
            '4',
        ]
    )
    assert calls == [(tmp_path, tmp_path / 'case', ParityCase('p9', 1000, 4))]
    assert code == (0 if accepted else 1)
