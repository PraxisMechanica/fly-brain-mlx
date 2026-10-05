from pathlib import Path

import pytest

from tests.quality.hook_fixture import (
    BAD,
    GOOD,
    SERVICE,
    commit_document,
    hook_repository,
)
from tests.quality.support import git

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    'source',
    [
        'import fly_brain.simulation.backend as implementation\n',
        'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n'
        '    from fly_brain.simulation.backend import VALUE\n',
        'from fly_brain.simulation.helper import VALUE\n',
    ],
)
def test_alias_type_only_and_indirect_dependencies_are_rejected(
    tmp_path: Path, source: str
) -> None:
    repo, environment = hook_repository(tmp_path)
    helper = repo / 'src/fly_brain/simulation/helper.py'
    helper.write_text(BAD)
    (repo / SERVICE).write_text(source)
    git(repo, 'add', 'src')
    result = commit_document(repo, environment)
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert 'fly_brain.simulation.service' in output
    assert 'fly_brain.simulation.backend' in output
    assert '(l.' in output


def test_reexport_cannot_launder_implementation_dependency(tmp_path: Path) -> None:
    repo, environment = hook_repository(tmp_path)
    (repo / 'src/fly_brain/simulation/models.py').write_text(BAD)
    (repo / SERVICE).write_text(GOOD)
    git(repo, 'add', 'src')
    result = commit_document(repo, environment)
    assert result.returncode != 0
    assert 'fly_brain.simulation.models' in result.stdout + result.stderr


def test_weakened_transitive_rule_stops_detecting_indirect_violation(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path)
    (repo / 'src/fly_brain/simulation/helper.py').write_text(BAD)
    (repo / SERVICE).write_text('from fly_brain.simulation.helper import VALUE\n')
    git(repo, 'add', 'src')
    rejected = commit_document(repo, environment)
    assert rejected.returncode != 0
    assert 'fly_brain.simulation.helper' in rejected.stdout + rejected.stderr
    policy = repo / 'pyproject.toml'
    policy.write_text(
        policy.read_text().replace(
            'type = "forbidden"',
            'type = "forbidden"\nallow_indirect_imports = true',
            1,
        )
    )
    git(repo, 'add', 'pyproject.toml')
    weakened = commit_document(repo, environment)
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr
