from pathlib import Path

import pytest

from tests.quality.hook_fixture import commit_document, hook_repository
from tests.quality.support import git

pytestmark = pytest.mark.integration
RULES = 'src/fly_brain/comparison/metrics.py'
SERVICE = 'from fly_brain.comparison.service import VALUE\n'
NEUTRAL = 'from fly_brain.comparison.models import VALUE\n'
INDIRECT = 'from fly_brain.comparison.helper import VALUE\n'


def sources(repo: Path, source: str, reexport: bool = False) -> None:
    (repo / 'src/fly_brain/comparison/models.py').write_text(
        SERVICE if reexport else 'VALUE = 1\n'
    )
    (repo / 'src/fly_brain/comparison/helper.py').write_text(SERVICE)
    (repo / RULES).write_text(source)
    git(repo, 'add', 'src')


@pytest.mark.parametrize(
    'source,reexport',
    (
        ('import fly_brain.comparison.service as implementation\n', False),
        (
            'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n'
            '    from fly_brain.comparison.service import VALUE\n',
            False,
        ),
        (INDIRECT, False),
        (NEUTRAL, True),
    ),
)
def test_comparison_rules_reject_service_paths_then_accept_owned_values(
    tmp_path: Path, source: str, reexport: bool
) -> None:
    repo, environment = hook_repository(tmp_path)
    sources(repo, source, reexport)
    rejected = commit_document(repo, environment)
    evidence = rejected.stdout + rejected.stderr
    assert rejected.returncode != 0
    assert 'DEP001: Comparison rules' in evidence
    assert 'fly_brain.comparison.metrics' in evidence
    assert 'fly_brain.comparison.service' in evidence and '(l.' in evidence
    sources(repo, NEUTRAL)
    accepted = commit_document(repo, environment)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr


def test_removing_the_pure_rule_scope_hides_its_unchanged_service_dependency(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path)
    sources(repo, SERVICE)
    assert commit_document(repo, environment).returncode != 0
    policy = repo / 'pyproject.toml'
    prefix, boundary = policy.read_text().split(
        'name = "DEP001: Comparison rules have no orchestration dependencies"', 1
    )
    policy.write_text(
        prefix
        + 'name = "DEP001: Comparison rules have no orchestration dependencies"'
        + boundary.replace('    "fly_brain.comparison.metrics",\n', '', 1)
    )
    git(repo, 'add', 'pyproject.toml')
    weakened = commit_document(repo, environment)
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr


def test_disabling_transitive_rule_paths_hides_the_same_indirect_service_dependency(
    tmp_path: Path,
) -> None:
    repo, environment = hook_repository(tmp_path)
    sources(repo, INDIRECT)
    assert commit_document(repo, environment).returncode != 0
    policy = repo / 'pyproject.toml'
    policy.write_text(policy.read_text() + '\nallow_indirect_imports = true\n')
    git(repo, 'add', 'pyproject.toml')
    weakened = commit_document(repo, environment)
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr
