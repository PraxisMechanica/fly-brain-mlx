import ast
import inspect
from collections.abc import Callable
from functools import partial
from pathlib import Path
from textwrap import dedent
from typing import TypeGuard, cast

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
        'tools/code-quality/provenance.json',
        'tools/code-quality/vendor/eng-metrics-code-quality-0.1.0.tgz',
        'tools/code-quality/vendor/eng-metrics-code-quality-0.1.1.tgz',
        'tools/code-quality/python-aggregation.patch',
        'tools/code_quality/metrics.mjs',
    ):
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    policy = repo / 'tools/architecture/ownership.json'
    policy.parent.mkdir(parents=True)
    policy.write_text('{}\n')
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
    source.parent.mkdir(parents=True, exist_ok=True)
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
    (indexed_repository / 'measurement.json').write_text('{"duration": 1}\n')
    gate.require_indexed_inputs()


def test_disabling_index_guard_hides_uncommitted_source(
    indexed_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def passed_metric(_arguments: list[str], _name: str) -> int:
        return 0

    source = indexed_repository / 'tools/uncommitted.py'
    source.parent.mkdir(exist_ok=True)
    source.write_text('VALUE = 1\n')
    monkeypatch.setenv('PRE_COMMIT', '1')
    monkeypatch.setattr(gate, 'measure', passed_metric)
    with pytest.raises(ValueError, match='COV001'):
        gate.main()
    monkeypatch.setattr(gate, 'require_indexed_inputs', lambda: None)
    assert gate.main() == 0


@pytest.mark.parametrize(
    'name',
    (
        'tools/architecture/ownership.json',
        'tools/code-quality/provenance.json',
        'tools/code-quality/vendor/eng-metrics-code-quality-0.1.0.tgz',
        'tools/code-quality/vendor/eng-metrics-code-quality-0.1.1.tgz',
        'tools/code-quality/python-aggregation.patch',
        'tools/code_quality/metrics.mjs',
    ),
)
@pytest.mark.parametrize('ignored', (False, True))
def test_canonical_check_input_is_required_until_explicitly_staged(
    indexed_repository: Path, name: str, ignored: bool
) -> None:
    git(indexed_repository, 'rm', '--cached', name)
    if ignored:
        (indexed_repository / '.gitignore').write_text(name + '\n')
    with pytest.raises(ValueError, match='COV001') as finding:
        gate.require_indexed_inputs()
    assert name in str(finding.value)
    git(indexed_repository, 'add', '--force', name)
    gate.require_indexed_inputs()


def matching_literal(node: ast.AST, value: str) -> TypeGuard[ast.Constant]:
    return isinstance(node, ast.Constant) and node.value == value


def matching_literals(tree: ast.AST, value: str) -> list[ast.Constant]:
    return [node for node in ast.walk(tree) if matching_literal(node, value)]


@pytest.mark.parametrize(
    'name',
    (
        'tools/architecture/ownership.json',
        'tools/code-quality/provenance.json',
        'tools/code-quality/vendor/eng-metrics-code-quality-0.1.0.tgz',
        'tools/code-quality/vendor/eng-metrics-code-quality-0.1.1.tgz',
        'tools/code-quality/python-aggregation.patch',
        'tools/code_quality/metrics.mjs',
    ),
)
def test_removing_one_canonical_input_loses_its_unindexed_defect(
    indexed_repository: Path,
    name: str,
) -> None:
    git(indexed_repository, 'rm', '--cached', name)
    with pytest.raises(ValueError, match='COV001'):
        gate.require_indexed_inputs()
    tree = ast.parse(dedent(inspect.getsource(gate.require_indexed_inputs)))
    selected = matching_literals(tree, name)
    assert len(selected) == 1
    selected[0].value = 'justfile'
    namespace = dict(gate.require_indexed_inputs.__globals__)
    exec(compile(tree, '<weakened-policy-index>', 'exec'), namespace)
    weakened = cast(Callable[[], None], namespace['require_indexed_inputs'])
    weakened()
