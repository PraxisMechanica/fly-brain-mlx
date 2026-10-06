import ast
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import pytest

from tools.architecture import policy as policy_module
from tools.architecture.inventory import Source, discover
from tools.architecture.policy import (
    Policy,
    binding_fingerprint,
    declaration_fingerprint,
    load_policy,
    review_policy,
)

pytestmark = pytest.mark.unit
SOURCE = 'def run(value: int) -> int:\n    return value\n'


def source_record(root: Path, path: str, role: str = 'rules') -> dict[str, object]:
    source = discover(root, (path,))[0]
    return {
        'owner': 'calculation',
        'role': role,
        'declaration_count': len(source.declarations),
        'declaration_sha256': declaration_fingerprint(source.declarations),
        'binding_sha256': binding_fingerprint(ast.parse((root / path).read_bytes())),
    }


def document(root: Path) -> dict[str, object]:
    (root / 'service.py').write_text(SOURCE)
    return {
        'version': 1,
        'reviewed_commit': 'a' * 40,
        'coverage': 'named_declarations_and_syntactic_binding_review',
        'source_roots': ['.'],
        'owners': {
            'calculation': {
                'kind': 'domain',
                'responsibility': 'Pure input calculation',
            }
        },
        'files': {'service.py': source_record(root, 'service.py')},
        'resources': {},
        'identifiers': {},
        'absences': {
            name: {'evidence': ['service.py'], 'decision': 'Only source arithmetic'}
            for name in ('database', 'http_endpoints')
        },
        'limitations': ['COV002: resolved calls/effects are outside this component'],
    }


def save(root: Path, value: dict[str, object]) -> Policy:
    path = root / 'ownership.json'
    path.write_text(json.dumps(value))
    return load_policy(path)


def resource_record(**changes: object) -> dict[str, object]:
    return {
        'owner': 'calculation',
        'kind': 'input',
        'relationship': 'independent',
        'evidence': [{'path': 'service.py', 'name': 'run'}],
        'decision': 'Explicit source-fixture resource',
        **changes,
    }


def identifier_record(resource: str) -> dict[str, object]:
    return {
        'owner': 'calculation',
        'resource': resource,
        'representation': 'primitive',
        'evidence': [{'path': 'service.py', 'name': 'run'}],
        'decision': 'The source-fixture primitive is not a distinct identifier',
    }


def test_review_is_source_only_and_does_not_start_the_classified_program(
    tmp_path: Path,
) -> None:
    value = document(tmp_path)
    (tmp_path / 'service.py').write_text(SOURCE + 'raise AssertionError("startup")\n')
    policy = save(tmp_path, value)
    result = review_policy(tmp_path, policy)
    assert not result.findings
    assert result.ownership['service.py'].declarations == ('run',)
    assert result.limitations == (
        'COV002: resolved calls/effects are outside this component',
    )


def test_new_source_has_to_be_registered_and_empty_package_source_remains_visible(
    tmp_path: Path,
) -> None:
    value = document(tmp_path)
    policy = save(tmp_path, value)
    (tmp_path / 'new.py').write_text('')
    result = review_policy(tmp_path, policy)
    assert [(f.rule, f.path, f.line) for f in result.findings] == [
        ('COV001', 'new.py', 1)
    ]
    value['files'] = {
        'service.py': source_record(tmp_path, 'service.py'),
        'new.py': source_record(tmp_path, 'new.py', 'package'),
    }
    repaired = review_policy(tmp_path, save(tmp_path, value))
    assert not repaired.findings
    assert len(repaired.sources) == 2


def test_renamed_declaration_cannot_keep_a_matching_count_and_inherit_ownership(
    tmp_path: Path,
) -> None:
    value = document(tmp_path)
    policy = save(tmp_path, value)
    (tmp_path / 'service.py').write_text(SOURCE.replace('run(', 'other('))
    result = review_policy(tmp_path, policy)
    assert any(
        (f.rule, f.path, f.line, f.message)
        == ('COV001', 'service.py', 1, 'Reviewed declaration set changed')
        for f in result.findings
    )
    value['files'] = {'service.py': source_record(tmp_path, 'service.py')}
    assert not review_policy(tmp_path, save(tmp_path, value)).findings


@pytest.mark.parametrize(
    'replacement',
    (
        'def run(other: int) -> int:\n    return other\n',
        'def run(value: int) -> int:\n    scratch = value\n    return scratch\n',
        'import math as hidden\n' + SOURCE,
        'from math import sqrt as hidden\n' + SOURCE,
        'def run(value: int) -> int:\n    value.extra = 1\n    return value\n',
        'def run(value: int) -> int:\n    global dependency\n    return value\n',
        'def run(value: int) -> int:\n    try:\n        return value\n'
        '    except ValueError as failure:\n        raise failure\n',
        'def run(value: int) -> int:\n    match value:\n'
        '        case {"id": identifier, **other}:\n            return identifier\n',
    ),
)
def test_new_non_declaration_bindings_require_explicit_source_review(
    tmp_path: Path, replacement: str
) -> None:
    value = document(tmp_path)
    policy = save(tmp_path, value)
    (tmp_path / 'service.py').write_text(replacement)
    result = review_policy(tmp_path, policy)
    assert any(
        (f.rule, f.path, f.line, f.message)
        == ('COV001', 'service.py', 1, 'Unreviewed source bindings')
        for f in result.findings
    )
    value['files'] = {'service.py': source_record(tmp_path, 'service.py')}
    assert not review_policy(tmp_path, save(tmp_path, value)).findings


def test_near_compliant_line_movement_and_local_arithmetic_do_not_change_binding_sets(
    tmp_path: Path,
) -> None:
    value = document(tmp_path)
    policy = save(tmp_path, value)
    (tmp_path / 'service.py').write_text(
        '\n' + SOURCE.replace('return value', 'return value + 1')
    )
    assert not review_policy(tmp_path, policy).findings


def test_frozen_source_hash_rejects_changed_arithmetic_with_the_same_bindings(
    tmp_path: Path,
) -> None:
    value = document(tmp_path)
    record = source_record(tmp_path, 'service.py')
    record['frozen'] = {
        'kind': 'historical_source',
        'commit': 'a' * 40,
        'origin': 'Retained executed source in its original revision',
        'sha256': discover(tmp_path, ('.',))[0].sha256,
    }
    value['files'] = {'service.py': record}
    policy = save(tmp_path, value)
    (tmp_path / 'service.py').write_text(
        SOURCE.replace('return value', 'return value + 1')
    )
    assert [f.message for f in review_policy(tmp_path, policy).findings] == [
        'Frozen artifact provenance changed'
    ]
    (tmp_path / 'service.py').write_text(SOURCE)
    assert not review_policy(tmp_path, policy).findings


@pytest.mark.parametrize('kind', ('symbols', 'public', 'composition', 'resources'))
def test_exact_symbol_references_must_resolve_to_reviewed_declarations(
    tmp_path: Path, kind: str
) -> None:
    value = document(tmp_path)
    record = source_record(tmp_path, 'service.py', 'types')
    if kind == 'symbols':
        record[kind] = {'absent': {'owner': 'calculation', 'role': 'types'}}
    elif kind == 'composition':
        record['role'] = 'composition'
        record[kind] = ['absent']
    elif kind == 'resources':
        value[kind] = {
            'input': resource_record(
                evidence=[{'path': 'service.py', 'name': 'absent'}]
            )
        }
    else:
        record[kind] = ['absent']
    value['files'] = {'service.py': record}
    assert any(
        f.rule == 'COV001'
        and f.path == 'service.py'
        and f.line == 1
        and 'absent' in f.message
        for f in review_policy(tmp_path, save(tmp_path, value)).findings
    )


@pytest.mark.parametrize(
    'key,replacement',
    (
        ('version', True),
        ('version', 2),
        ('source_roots', []),
        ('source_roots', ['.', '.']),
        ('source_roots', ['../escape']),
        ('owners', {}),
        ('files', {}),
        ('absences', {}),
        ('limitations', []),
        ('exclude', ['src/**']),
        ('findings', [{'rule': 'COV001'}]),
        (
            'findings',
            [
                {
                    'rule': 'NOT_A_RULE',
                    'symbol': {'path': 'service.py', 'name': 'run'},
                    'message': 'Unrecognized finding',
                }
            ],
        ),
    ),
)
def test_invalid_or_weakened_policy_cannot_be_loaded(
    tmp_path: Path, key: str, replacement: object
) -> None:
    value = document(tmp_path)
    value[key] = replacement
    with pytest.raises(ValueError, match='COV002'):
        save(tmp_path, value)


@pytest.mark.parametrize(
    'change',
    (
        {'owner': 'unknown'},
        {'owner': ' '},
        {'owner': ['calculation', 'other']},
        {'role': 'generated_exempt'},
        {'declaration_count': True},
        {'declaration_sha256': 'bad'},
        {'public': ['run', 'run']},
        {'public': ['run']},
        {'composition': ['run']},
    ),
)
def test_invalid_ambiguous_or_privileged_file_classification_is_rejected(
    tmp_path: Path, change: dict[str, object]
) -> None:
    value = document(tmp_path)
    value['files'] = {'service.py': {**source_record(tmp_path, 'service.py'), **change}}
    with pytest.raises(ValueError, match='COV002'):
        save(tmp_path, value)


@pytest.mark.parametrize(
    'path', ('/service.py', './service.py', 'src/*.py', 'src\\service.py', 'source.js')
)
def test_source_mapping_is_exact_and_cannot_whitelist_a_tree(
    tmp_path: Path, path: str
) -> None:
    value = document(tmp_path)
    value['files'] = {path: source_record(tmp_path, 'service.py')}
    with pytest.raises(ValueError, match='COV002'):
        save(tmp_path, value)


def test_absent_and_empty_source_scopes_are_analysis_failures(tmp_path: Path) -> None:
    value = document(tmp_path)
    policy = save(tmp_path, value)
    (tmp_path / 'service.py').rename(tmp_path / 'service.retained')
    with pytest.raises(ValueError, match='COV002: intended source scope is empty'):
        review_policy(tmp_path, policy)
    value['source_roots'] = ['missing']
    with pytest.raises(ValueError, match='COV002: missing source root'):
        review_policy(tmp_path, save(tmp_path, value))


def test_duplicate_json_keys_cannot_choose_the_last_classification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = document(tmp_path)
    path = tmp_path / 'ownership.json'
    path.write_text(
        json.dumps(value).replace('"version": 1', '"version": 2, "version": 1')
    )
    with pytest.raises(ValueError, match='COV002: duplicate policy key: version'):
        load_policy(path)
    monkeypatch.setattr(policy_module, '_unique_object', dict)
    assert not review_policy(tmp_path, load_policy(path)).findings


@pytest.mark.parametrize('mechanism', ('declaration', 'binding'))
def test_weakening_each_review_tripwire_loses_the_same_real_source_defect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mechanism: Literal['declaration', 'binding'],
) -> None:
    value = document(tmp_path)
    policy = save(tmp_path, value)
    record = policy.files['service.py']
    if mechanism == 'declaration':
        replacement = SOURCE.replace('def run', 'async def run')
        function = 'declaration_fingerprint'
        expected = record.declaration_sha256
    else:
        replacement = SOURCE.replace(
            '    return value', '    hidden = value\n    return hidden'
        )
        function = 'binding_fingerprint'
        expected = record.binding_sha256
    (tmp_path / 'service.py').write_text(replacement)
    assert review_policy(tmp_path, policy).findings

    def weakened(_: object) -> str:
        return expected

    monkeypatch.setattr(policy_module, function, weakened)
    assert not review_policy(tmp_path, policy).findings


def test_neutral_exports_and_assembly_permissions_require_exact_compatible_roles(
    tmp_path: Path,
) -> None:
    value = document(tmp_path)
    (tmp_path / 'service.py').write_text(
        'from dataclasses import dataclass\n@dataclass(frozen=True)\n'
        'class Value:\n    number: int\n'
        'def assemble(number: int) -> Value:\n    return Value(number)\n'
    )
    record = source_record(tmp_path, 'service.py', 'module')
    record['symbols'] = {
        name: {'owner': 'calculation', 'role': 'types'}
        for name in ('Value', 'Value.number')
    }
    record['public'] = ['Value', 'Value.number']
    record['composition'] = ['assemble']
    value['files'] = {'service.py': record}
    policy = save(tmp_path, value)
    assert not review_policy(tmp_path, policy).findings
    assert (
        review_policy(tmp_path, policy).symbols['service.py', 'assemble'].role
        == 'module'
    )


def test_source_drift_during_review_is_an_analysis_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = document(tmp_path)
    policy = save(tmp_path, value)
    original = policy_module.discover

    def changed(root: Path, roots: Sequence[str]) -> tuple[Source, ...]:
        result = original(root, roots)
        (root / 'service.py').write_text(SOURCE + '# changed during analysis\n')
        return result

    monkeypatch.setattr(policy_module, 'discover', changed)
    with pytest.raises(
        ValueError, match='COV002: source changed during ownership review'
    ):
        review_policy(tmp_path, policy)


@pytest.mark.parametrize(
    'change',
    (
        {'owner': 'unknown'},
        {'relationship': 'storage_only'},
        {'relationship': 'storage_only', 'parent': 'absent'},
        {'relationship': 'storage_only', 'parent': 'input'},
        {'relationship': 'blanket_exemption'},
        {'evidence': []},
        {'kind': 'database_table'},
        {'evidence': [{'path': 'foreign.py', 'name': 'run'}]},
    ),
)
def test_invalid_or_unowned_resources_and_false_absence_claims_are_rejected(
    tmp_path: Path, change: dict[str, object]
) -> None:
    value = document(tmp_path)
    value['resources'] = {'input': resource_record(**change)}
    with pytest.raises(ValueError, match='COV002'):
        save(tmp_path, value)


def test_storage_children_cannot_form_an_owner_cycle(tmp_path: Path) -> None:
    value = document(tmp_path)
    value['resources'] = {
        'first': resource_record(relationship='storage_only', parent='second'),
        'second': resource_record(relationship='storage_only', parent='first'),
    }
    with pytest.raises(ValueError, match='COV002: resource parent cycle'):
        save(tmp_path, value)
    value['resources'] = {
        'first': resource_record(relationship='storage_only', parent='second'),
        'second': resource_record(),
    }
    assert not review_policy(tmp_path, save(tmp_path, value)).findings


def test_identifier_contract_cannot_name_an_unowned_resource(tmp_path: Path) -> None:
    value = document(tmp_path)
    value['identifiers'] = {'identity': identifier_record('absent')}
    with pytest.raises(
        ValueError, match='COV002: identifier resource ownership differs'
    ):
        save(tmp_path, value)


@pytest.mark.parametrize(
    'guard',
    (
        '_validate_file',
        '_validate_resources',
        '_validate_identifiers',
        '_validate_absences',
    ),
)
def test_disabling_each_metadata_link_guard_accepts_its_invalid_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: str
) -> None:
    value = document(tmp_path)
    if guard == '_validate_file':
        value['files'] = {
            'service.py': {**source_record(tmp_path, 'service.py'), 'public': ['run']}
        }
    elif guard == '_validate_resources':
        value['resources'] = {
            'input': resource_record(relationship='storage_only', parent='absent')
        }
    elif guard == '_validate_identifiers':
        value['identifiers'] = {'identity': identifier_record('absent')}
    else:
        value['absences'] = {}
    with pytest.raises(ValueError, match='COV002'):
        save(tmp_path, value)

    def disabled(*_: object) -> None:
        return None

    monkeypatch.setattr(policy_module, guard, disabled)
    assert load_policy(tmp_path / 'ownership.json')


def test_unresolved_resources_and_primitive_identities_remain_recorded_findings(
    tmp_path: Path,
) -> None:
    value = document(tmp_path)
    value['resources'] = {
        'producer': resource_record(kind='runtime', relationship='unresolved')
    }
    value['identifiers'] = {'producer_identity': identifier_record('producer')}
    result = review_policy(tmp_path, save(tmp_path, value))
    assert not result.findings
    assert [(f.rule, f.path, f.line) for f in result.recorded_findings] == [
        ('COV001', 'service.py', 1),
        ('VALUE001', 'service.py', 1),
    ]


def test_live_registry_reconciles_all_source_and_retains_actual_debt_and_limits() -> (
    None
):
    root = Path(__file__).resolve().parents[2]
    policy = load_policy(root / 'tools/architecture/ownership.json')
    result = review_policy(root, policy)
    assert not result.findings
    assert set(policy.files) == {s.path for s in result.sources}
    assert len([s for s in result.sources if s.path.startswith('docs/evidence/')]) == 60
    assert policy.document.identifiers['flywire_neuron'].representation == 'primitive'
    assert result.recorded_findings
    assert any('COV002' in limitation for limitation in result.limitations)
    assert (
        'Advance'
        not in policy.files['src/fly_brain/simulation/backend/engines.py'].public
    )


@pytest.mark.parametrize(
    'name,parent',
    (
        ('reference_build_execution', 'qualification_case'),
        ('native_execution_state', 'simulation_run'),
    ),
)
def test_runtime_resource_is_a_child_of_its_producing_workflow(
    name: str,
    parent: str,
) -> None:
    root = Path(__file__).resolve().parents[2]
    resource = load_policy(
        root / 'tools/architecture/ownership.json'
    ).document.resources[name]
    assert (resource.relationship, resource.parent) == ('storage_only', parent)
