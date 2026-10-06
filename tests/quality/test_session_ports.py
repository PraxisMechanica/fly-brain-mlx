from pathlib import Path

import pytest

from tests.quality.hook_fixture import BAD, commit_document, hook_repository
from tests.quality.support import git

pytestmark = pytest.mark.integration
SCOPES = (
    'fly_brain.qualification.session_expectations',
    'fly_brain.qualification.session_observer',
    'fly_brain.simulation.observation_ports',
    'fly_brain.qualification.session_blocks',
    'fly_brain.simulation.observations',
)
NEUTRAL = 'from fly_brain.simulation.observations import VALUE\n'


def add_scopes(repo: Path) -> None:
    policy = repo / 'pyproject.toml'
    contract = policy.read_text().split('[[tool.importlinter.contracts]]', 2)[1]
    sources = contract.split('forbidden_modules', 1)[0]
    assert all('"' + scope + '"' in sources for scope in SCOPES)
    for scope in SCOPES:
        (repo / Path('src', *scope.split('.')).with_suffix('.py')).write_text(NEUTRAL)
    (repo / 'src/fly_brain/simulation/observations.py').write_text('VALUE = 1\n')


def install_source(repo: Path, scope: str, source: str, reexport: bool = False) -> None:
    (repo / Path('src', *scope.split('.')).with_suffix('.py')).write_text(source)
    (repo / 'src/fly_brain/qualification/helper.py').write_text(
        BAD + 'def factory():\n    return lambda: VALUE\n'
    )
    if scope != 'fly_brain.simulation.observations':
        (repo / 'src/fly_brain/simulation/observations.py').write_text(
            BAD if reexport else 'VALUE = 1\n'
        )
    git(repo, 'add', 'src', 'pyproject.toml')


@pytest.mark.parametrize('scope', SCOPES)
def test_each_session_consumer_scope_rejects_native_implementation_then_accepts_neutral_values(
    tmp_path: Path, scope: str
) -> None:
    repo, environment = hook_repository(tmp_path)
    add_scopes(repo)
    install_source(repo, scope, BAD)
    rejected = commit_document(repo, environment)
    output = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert 'DEP001/DEP004' in output and scope in output
    assert 'fly_brain.simulation.backend' in output and '(l.' in output
    repaired = (
        'VALUE = 1\n' if scope == 'fly_brain.simulation.observations' else NEUTRAL
    )
    install_source(repo, scope, repaired)
    accepted = commit_document(repo, environment)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr


@pytest.mark.parametrize(
    'source,reexport',
    (
        (
            'import fly_brain.simulation.backend as device\nread = lambda: device.VALUE\n',
            False,
        ),
        (
            'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from fly_brain.simulation.backend import VALUE\n',
            False,
        ),
        ('from fly_brain.qualification.helper import VALUE\n', False),
        (
            'from fly_brain.qualification.helper import factory\nread = factory()\n',
            False,
        ),
        (NEUTRAL, True),
    ),
)
def test_session_boundary_rejects_aliased_type_only_captured_factory_and_reexport_paths(
    tmp_path: Path, source: str, reexport: bool
) -> None:
    repo, environment = hook_repository(tmp_path)
    add_scopes(repo)
    scope = SCOPES[1]
    install_source(repo, scope, source, reexport)
    rejected = commit_document(repo, environment)
    output = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert scope in output and 'fly_brain.simulation.backend' in output
    if 'helper' in source:
        assert 'fly_brain.qualification.helper' in output
    install_source(repo, scope, NEUTRAL)
    accepted = commit_document(repo, environment)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr


def test_omitting_a_session_consumer_scope_hides_unchanged_dependency_debt(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path)
    add_scopes(repo)
    scope = SCOPES[1]
    install_source(repo, scope, BAD)
    assert commit_document(repo, environment).returncode != 0
    policy = repo / 'pyproject.toml'
    policy.write_text(policy.read_text().replace(f'    "{scope}",\n', '', 1))
    git(repo, 'add', 'pyproject.toml')
    weakened = commit_document(repo, environment)
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr
