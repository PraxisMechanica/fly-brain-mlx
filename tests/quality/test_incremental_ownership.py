import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from tests.quality.support import git, repository
from tests.quality.test_architecture_policy import document, source_record
from tools.architecture import policy_review as policy_module
from tools.architecture.inventory import Source
from tools.code_quality import ownership


def save_policy(root: Path, value: dict[str, object]) -> None:
    path = root / ownership.POLICY
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def fixture(root: Path) -> str:
    repository(root)
    value = document(root)
    (root / 'calculation.py').write_text(
        'def calculate(value: int) -> int:\n    return value\n'
    )
    value['files'] = {
        'service.py': source_record(root, 'service.py'),
        'calculation.py': source_record(root, 'calculation.py'),
    }
    save_policy(root, value)
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'Register source fixture owners')
    return git(root, 'rev-parse', 'HEAD')


def test_only_changed_source_is_parsed_while_complete_inventory_is_accounted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'service.py').write_text(
        'def run(value: int) -> int:\n    return -value\n'
    )
    actual = policy_module.discover
    calls: list[tuple[str, ...]] = []

    def observed(root: Path, scopes: Sequence[str]) -> tuple[Source, ...]:
        calls.append(tuple(scopes))
        return actual(root, scopes)

    monkeypatch.setattr(policy_module, 'discover', observed)
    assert ownership.review(tmp_path, base, ('service.py',)) == ()
    assert calls == [('service.py',)]


def test_new_unowned_source_fails_even_when_other_sources_are_unchanged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'unowned.py').write_text('VALUE = 1\n')
    findings = ownership.review(tmp_path, base, ('unowned.py',))
    assert [(item.rule, item.path) for item in findings] == [('COV001', 'unowned.py')]


def test_changed_metadata_rechecks_unchanged_source_member_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    value = document(tmp_path)
    service = source_record(tmp_path, 'service.py')
    service['symbols'] = {'absent': {'owner': 'calculation', 'role': 'rules'}}
    value['files'] = {
        'service.py': service,
        'calculation.py': source_record(tmp_path, 'calculation.py'),
    }
    save_policy(tmp_path, value)
    findings = ownership.review(tmp_path, base, ('tools/architecture/ownership.json',))
    assert any(
        item.rule == 'COV001'
        and item.path == 'service.py'
        and item.message == 'Mapped declaration is absent: absent'
        for item in findings
    )


def test_metadata_evidence_cannot_reference_an_absent_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    value = json.loads((tmp_path / ownership.POLICY).read_text())
    value['resources'] = {
        'input': {
            'owner': 'calculation',
            'kind': 'input',
            'relationship': 'independent',
            'evidence': [{'path': 'service.py', 'name': 'absent'}],
            'decision': 'Exact fixture evidence',
        },
    }
    save_policy(tmp_path, value)
    findings = ownership.review(tmp_path, base, (ownership.POLICY,))
    assert any(
        item.path == 'service.py'
        and item.message == 'Unresolved policy evidence: absent'
        for item in findings
    )
