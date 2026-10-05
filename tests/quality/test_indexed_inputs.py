from functools import partial
from pathlib import Path

import pytest

from tests.quality.support import git, repository
from tools.code_quality import gate

pytestmark = pytest.mark.integration


@pytest.fixture
def indexed_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = repository(tmp_path)
    for name in (
        'main.py',
        'pyproject.toml',
        'uv.lock',
        'package.json',
        'pnpm-lock.yaml',
        'justfile',
        '.pre-commit-config.yaml',
    ):
        (repo / name).touch()
    git(repo, 'add', '.')
    git(repo, 'update-ref', 'refs/remotes/origin/main', 'HEAD')
    monkeypatch.chdir(repo)
    monkeypatch.setattr(gate, 'git', partial(git, repo))
    for name in (
        'QUALITY_BASE',
        'QUALITY_HEAD',
        'PRE_COMMIT_FROM_REF',
        'PRE_COMMIT_TO_REF',
    ):
        monkeypatch.delenv(name, raising=False)
    return repo


@pytest.mark.parametrize(
    'name', ['src/fly_brain/extension.py', 'typings/provider.pyi', 'tools/checker.py']
)
@pytest.mark.parametrize('ignored', [False, True])
def test_unindexed_input_is_rejected_until_staged(
    indexed_repository: Path, name: str, ignored: bool
) -> None:
    repo = indexed_repository
    source = repo / name
    source.parent.mkdir(parents=True)
    source.write_text('VALUE = 1\n')
    if ignored:
        (repo / '.gitignore').write_text(name + '\n')
    with pytest.raises(ValueError, match='COV001') as finding:
        gate.require_indexed_inputs()
    assert name in str(finding.value)
    git(repo, 'add', '--force', name)
    gate.require_indexed_inputs()


def test_non_source_evidence_does_not_require_indexing(
    indexed_repository: Path,
) -> None:
    (indexed_repository / 'measurement.csv').write_text('duration\n1\n')
    gate.require_indexed_inputs()


def test_disabling_index_guard_hides_uncommitted_source(
    indexed_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def passed_metric(_arguments: list[str], _name: str) -> int:
        return 0

    source = indexed_repository / 'tools/uncommitted.py'
    source.parent.mkdir()
    source.write_text('VALUE = 1\n')
    monkeypatch.setenv('PRE_COMMIT', '1')
    monkeypatch.setattr(gate, 'measure', passed_metric)
    with pytest.raises(ValueError, match='COV001'):
        gate.main()
    monkeypatch.setattr(gate, 'require_indexed_inputs', lambda: None)
    assert gate.main() == 0
