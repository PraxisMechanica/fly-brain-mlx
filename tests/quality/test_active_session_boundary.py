import os
import subprocess
from pathlib import Path

import pytest

from tests.quality.hook_fixture import commit_document, hook_repository
from tests.quality.support import PROJECT, git

pytestmark = pytest.mark.integration
SCOPES = (
    'fly_brain.qualification.adapters.paired_collect',
    'fly_brain.qualification.adapters.mlx_batch_collect',
    'fly_brain.qualification.adapters.case_execution',
    'fly_brain.qualification.adapters.paired_observer',
    'fly_brain.qualification.adapters.paired_causes',
    'fly_brain.qualification.adapters.parity_case',
)
TARGETS = (
    'fly_brain.simulation.backend',
    'fly_brain.simulation.observation_module',
)
NEUTRAL = 'from fly_brain.qualification.ports import VALUE\n'
CONTRACT = 'DEP001/DEP003: Active qualification uses injected observation sessions'


def policy(root: Path, scopes: tuple[str, ...] = SCOPES) -> str:
    canonical = (
        '[tool.importlinter]'
        + (PROJECT / 'pyproject.toml').read_text().split('[tool.importlinter]', 1)[1]
    )
    contracts = canonical.split('[[tool.importlinter.contracts]]')
    canonical = contracts[0] + ''.join(
        '[[tool.importlinter.contracts]]' + contract
        for contract in contracts[1:]
        if f'name = "{CONTRACT}"' not in contract
    )
    return (
        canonical
        + '\n[[tool.importlinter.contracts]]\n'
        + f'name = "{CONTRACT}"\n'
        + 'type = "forbidden"\n'
        + 'source_modules = [\n'
        + ''.join(f'    "{scope}",\n' for scope in scopes)
        + ']\nforbidden_modules = [\n'
        + ''.join(f'    "{target}",\n' for target in TARGETS)
        + ']\nallow_indirect_imports = false\n'
    )


def install(repo: Path, scope: str, source: str, target: str) -> None:
    (repo / 'pyproject.toml').write_text(policy(repo))
    for name in (*SCOPES, TARGETS[1]):
        path = repo / 'src' / Path(*name.split('.')).with_suffix('.py')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('VALUE = 1\n' if name == TARGETS[1] else NEUTRAL)
    (repo / 'src/fly_brain/qualification/ports.py').write_text('VALUE = 1\n')
    (repo / 'src' / Path(*scope.split('.')).with_suffix('.py')).write_text(source)
    helper = repo / 'src/fly_brain/qualification/session_helper.py'
    helper.write_text(
        f'from {target} import VALUE\ndef factory():\n    return lambda: VALUE\n'
    )
    git(repo, 'add', 'src', 'pyproject.toml')


@pytest.mark.parametrize('scope', SCOPES)
@pytest.mark.parametrize('target', TARGETS)
def test_each_active_consumer_rejects_native_or_assembly_dependency_then_accepts_port(
    tmp_path: Path, scope: str, target: str
) -> None:
    repo, environment = hook_repository(tmp_path)
    install(repo, scope, f'from {target} import VALUE\n', target)
    rejected = commit_document(repo, environment)
    output = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert CONTRACT in output and scope in output and target in output
    assert '(l.' in output
    install(repo, scope, NEUTRAL, target)
    repaired = commit_document(repo, environment)
    assert repaired.returncode == 0, repaired.stdout + repaired.stderr


@pytest.mark.parametrize('target', TARGETS)
@pytest.mark.parametrize(
    'form', ('alias', 'type-only', 'transitive', 'capture', 'factory', 'reexport')
)
def test_active_boundary_resolves_alias_type_only_transitive_capture_factory_and_reexport(
    tmp_path: Path, target: str, form: str
) -> None:
    repo, environment = hook_repository(tmp_path)
    scope = SCOPES[0]
    sources = {
        'alias': f'import {target} as native\nVALUE = native.VALUE\n',
        'type-only': f'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from {target} import VALUE\n',
        'transitive': 'from fly_brain.qualification.session_helper import VALUE\n',
        'capture': f'from {target} import VALUE\nread = lambda: VALUE\n',
        'factory': 'from fly_brain.qualification.session_helper import factory\nread = factory()\n',
        'reexport': 'from fly_brain.qualification.session_helper import VALUE as PUBLIC\n',
    }
    install(repo, scope, sources[form], target)
    rejected = commit_document(repo, environment)
    output = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert CONTRACT in output and scope in output and target in output
    if form in ('transitive', 'factory', 'reexport'):
        assert 'fly_brain.qualification.session_helper' in output
    install(repo, scope, NEUTRAL, target)
    repaired = commit_document(repo, environment)
    assert repaired.returncode == 0, repaired.stdout + repaired.stderr


def test_omitting_active_consumer_scope_hides_unchanged_implementation_debt(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path)
    scope = SCOPES[0]
    install(repo, scope, f'from {TARGETS[1]} import VALUE\n', TARGETS[1])
    assert commit_document(repo, environment).returncode != 0
    (repo / 'pyproject.toml').write_text(policy(repo, SCOPES[1:]))
    git(repo, 'add', 'pyproject.toml')
    weakened = commit_document(repo, environment)
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr


def test_actual_active_consumers_use_ports_without_native_or_assembly_paths(
    tmp_path: Path,
) -> None:
    configuration = tmp_path / 'pyproject.toml'
    configuration.write_text(policy(PROJECT))
    environment = dict(os.environ)
    environment['PYTHONPATH'] = str(PROJECT / 'src')
    result = subprocess.run(
        ['lint-imports', '--config', str(configuration), '--no-cache'],
        cwd=PROJECT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert CONTRACT in result.stdout and 'Contracts: 5 kept, 0 broken.' in result.stdout
