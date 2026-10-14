from contextlib import nullcontext
from pathlib import Path

import pytest

from tests.quality.support import git
from tests.quality.test_output_retention import managed_markers, retention_repository
from tools.code_quality.retention import POLICY, clean_outputs


@pytest.mark.parametrize(
    'arguments, error',
    (
        (('rm', '--cached', POLICY), 'indexed'),
        (('add', 'executions/marker.txt'), 'versioned'),
        (('status', '--porcelain'), None),
    ),
)
def test_cleanup_uses_requested_repository_under_foreign_git_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    arguments: tuple[str, ...],
    error: str | None,
) -> None:
    foreign = tmp_path / 'foreign'
    foreign.mkdir()
    retention_repository(foreign)
    target = tmp_path / 'target'
    target.mkdir()
    retention_repository(target)
    markers = managed_markers(target)
    git(target, *arguments)
    monkeypatch.setenv('GIT_DIR', str(foreign / '.git'))
    monkeypatch.setenv('GIT_WORK_TREE', str(foreign))
    monkeypatch.setenv('GIT_INDEX_FILE', str(foreign / '.git/index'))
    with pytest.raises(ValueError, match=error) if error else nullcontext():
        clean_outputs(target)
    assert all(marker.is_file() == bool(error) for marker in markers)
    assert (foreign / POLICY).is_file()
