from pathlib import Path

import pytest

from tests.quality.hook_fixture import BAD, commit_document, hook_repository
from tests.quality.support import git

pytestmark = pytest.mark.integration
PORT = 'src/fly_brain/qualification/ports.py'
NEUTRAL = 'from fly_brain.simulation.observations import VALUE\n'


def sources(repo: Path, source: str, reexport: bool = False) -> None:
    (repo / 'src/fly_brain/simulation/observations.py').write_text(
        BAD if reexport else 'VALUE = 1\n'
    )
    (repo / 'src/fly_brain/qualification/helper.py').write_text(BAD)
    (repo / PORT).write_text(source)
    git(repo, 'add', 'src')


@pytest.mark.parametrize(
    'source,reexport',
    (
        ('import fly_brain.simulation.backend as implementation\n', False),
        (
            'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n'
            '    from fly_brain.simulation.backend import VALUE\n',
            False,
        ),
        ('from fly_brain.qualification.helper import VALUE\n', False),
        (NEUTRAL, True),
    ),
)
def test_observation_port_rejects_implementation_paths_then_accepts_neutral_values(
    tmp_path: Path, source: str, reexport: bool
) -> None:
    repo, environment = hook_repository(tmp_path)
    sources(repo, source, reexport)
    rejected = commit_document(repo, environment)
    evidence = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert 'DEP004' in evidence
    assert 'fly_brain.qualification.ports' in evidence
    assert 'fly_brain.simulation.backend' in evidence and '(l.' in evidence
    sources(repo, NEUTRAL)
    accepted = commit_document(repo, environment)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr


def test_removing_the_port_scope_hides_its_unchanged_implementation_debt(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path)
    sources(repo, BAD)
    rejected = commit_document(repo, environment)
    assert rejected.returncode != 0
    policy = repo / 'pyproject.toml'
    policy.write_text(
        policy.read_text().replace('    "fly_brain.qualification.ports",\n', '', 1)
    )
    git(repo, 'add', 'pyproject.toml')
    weakened = commit_document(repo, environment)
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr
