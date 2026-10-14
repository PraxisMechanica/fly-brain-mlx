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
    assert 'Comparison calculations avoid orchestration and storage' in evidence
    assert 'fly_brain.comparison.metrics' in evidence
    assert 'fly_brain.comparison.service' in evidence and '(l.' in evidence
    sources(repo, NEUTRAL)
    accepted = commit_document(repo, environment)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
