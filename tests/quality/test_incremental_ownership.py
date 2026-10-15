import hashlib
import json
from pathlib import Path

import pytest

from tests.quality.support import PROJECT
from tools.code_quality import ownership


@pytest.fixture
def protected_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / 'service.py').write_text('VALUE = 1\n')
    records: dict[str, dict[str, str]] = {}
    for name in ownership.PROTECTED:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('VALUE = 1\n')
        records[name] = {
            'kind': 'reference_source',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'commit': 'a' * 40,
            'origin': 'Independent source-identity fixture',
        }
    value = {'version': 1, 'sources': records}
    policy = tmp_path / ownership.POLICY
    policy.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text(json.dumps(value))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_ordinary_names_bindings_and_modules_need_no_registry_approval(
    protected_project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (protected_project / 'service.py').write_text(
        'from math import sqrt as root\ndef renamed(other: float) -> float:\n'
        '    completed = root(other)\n    return completed\n'
    )
    (protected_project / 'new_module.py').write_text('NEW_VALUE = 2\n')
    assert ownership.main([]) == 0
    output = capsys.readouterr().out
    assert '3 protected scientific sources checked' in output
    assert '37-rule' not in output and 'recorded findings' not in output


@pytest.mark.parametrize('operation', ('change', 'remove', 'link'))
def test_protected_source_changes_and_missing_files_fail(
    protected_project: Path, operation: str, capsys: pytest.CaptureFixture[str]
) -> None:
    path = protected_project / ownership.PROTECTED[0]
    if operation == 'change':
        path.write_text('VALUE = 2\n')
    else:
        path.unlink()
        if operation == 'link':
            replacement = protected_project / 'replacement.py'
            replacement.write_text('VALUE = 1\n')
            path.symlink_to(replacement)
    assert ownership.main([]) == (1 if operation == 'change' else 2)
    assert ownership.PROTECTED[0] in capsys.readouterr().err


@pytest.mark.parametrize('operation', ('remove_guard', 'invalid_hash'))
def test_removed_or_invalid_protection_records_fail(
    protected_project: Path, operation: str
) -> None:
    path = protected_project / ownership.POLICY
    value = json.loads(path.read_text())
    record = value['sources'][ownership.PROTECTED[0]]
    if operation == 'remove_guard':
        del value['sources'][ownership.PROTECTED[0]]
    else:
        record['sha256'] = 'invalid'
    path.write_text(json.dumps(value))
    assert ownership.main([]) == 2


def test_actual_scientific_source_guards_still_match() -> None:
    assert ownership.review(PROJECT) == ()
