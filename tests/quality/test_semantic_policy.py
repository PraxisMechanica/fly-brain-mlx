import copy
import hashlib
import inspect
import json
from collections.abc import Callable
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path
from types import MappingProxyType
from typing import cast

import pytest

from tests.quality.support import PROJECT
from tests.quality.test_architecture_symbols import semantic_model
from tools.architecture import semantic_policy_inputs as input_integrity
from tools.architecture import semantic_policy_references as references
from tools.architecture import semantic_policy_validation as validation
from tools.architecture.semantic_policy_records import (
    Input,
    NativeObservation,
    ObservedArtifact,
)
from tools.architecture.semantic_policy_schema import (
    CATALOG,
    SemanticPolicyDocument,
    load_semantic_policy,
)
from tools.architecture.semantic_policy_validation import (
    observed_bindings,
    validate_semantic_inputs,
)

pytestmark = pytest.mark.unit
SOURCE = (
    'class Value: pass\n'
    'class Port:\n    def read(self): return 7\n'
    'def operate(port: Port) -> Value:\n    port.read()\n    return Value()\n'
    'def command(request: Value) -> Value:\n    return operate(Port())\n'
    'def build(): return Port()\n'
)


def document(root: Path) -> tuple[dict[str, object], NativeObservation]:
    model = semantic_model(root, {'domain/example.py': SOURCE})
    facts = observed_bindings('active', model)
    keys = {s.name: k.model_dump(mode='json') for k, s in facts.items()}
    bindings: list[dict[str, object]] = []
    roles = {
        'Value': 'types',
        'Port': 'ports',
        'Port.read': 'ports',
        'operate': 'service',
        'command': 'command_adapter',
        'build': 'module',
    }
    for key, symbol in facts.items():
        role = roles.get(symbol.name, 'types')
        location = symbol.location
        bindings.append(
            {
                'symbol': key.model_dump(mode='json'),
                'anchor': {
                    'source_sha256': symbol.provenance.sha256,
                    'artifact': 'compiler',
                    'line': location.line,
                    'column': location.column,
                    'end_line': location.end_line,
                    'end_column': location.end_column,
                },
                'owner': 'example',
                'role': role,
                'phase': 'declaration',
                'semantic_kind': 'test_or_analysis',
                'evidence': 'Native declaration fixture; role inputs are not semantic compliance.',
            }
        )
    executable = (PROJECT / '.venv/bin/pyright-langserver').resolve()
    value: dict[str, object] = {
        'version': 2,
        'owners': {'example': {'kind': 'domain', 'responsibility': 'Fixture workflow'}},
        'contexts': [
            {
                'id': 'active',
                'languages': ['python'],
                'sources': [
                    {'path': 'domain/example.py', 'sha256': model.sources[0].sha256}
                ],
                'artifacts': ['compiler'],
                'expected_bindings': list(keys.values()),
                'build_variant': 'source-only',
            }
        ],
        'placement': [{'owner': 'example', 'roots': ['domain']}],
        'semantic_bindings': bindings,
        'consumer_slots': [
            {
                'id': 'reader',
                'consumer': keys['operate'],
                'symbol': keys['operate.port'],
                'kind': 'parameter',
                'nature': 'collaborator',
                'required': True,
                'port': 'reader',
                'capabilities_used': [keys['Port.read']],
            }
        ],
        'ports': [
            {
                'id': 'reader',
                'symbol': keys['Port'],
                'owner': 'example',
                'members': [keys['Port.read']],
                'consumers': [keys['operate']],
                'purity': 'declaration',
            }
        ],
        'public_contracts': [
            {
                'id': 'value',
                'owner': 'example',
                'symbol': keys['Value'],
                'kind': 'value',
                'storage': 'ownership_unresolved',
            }
        ],
        'effects': [
            {
                'id': 'read',
                'target': keys['Port.read'],
                'artifact': 'compiler',
                'categories': ['unresolved'],
                'preconditions': 'Not a proved effect summary',
                'evidence': 'Review required',
            }
        ],
        'constructors_and_factories': [
            {
                'id': 'builder',
                'target': keys['build'],
                'category': 'collaborator',
                'produced_type': keys['Port'],
                'port': 'reader',
                'assembly_sites': [keys['build']],
                'lifetime_owner': 'example',
            }
        ],
        'use_cases_and_handlers': [
            {
                'id': 'work',
                'operation': keys['operate'],
                'owner': 'example',
                'request_contract': 'value',
                'result_contract': 'value',
                'handler': keys['command'],
                'operation_port': 'reader',
                'success_path_calls': 1,
            }
        ],
        'resources_and_storage': [
            {
                'id': 'work',
                'owner': 'example',
                'relationship': 'independent',
                'operations': [keys['operate']],
                'lifetime_owner': 'example',
                'evidence': 'Fixture workflow',
            }
        ],
        'identifiers': [
            {
                'id': 'identity',
                'resource': 'work',
                'owner': 'example',
                'distinct_type': keys['Value'],
                'representation': 'native value',
                'boundary_slots': ['reader'],
                'namespace_binding': 'fixture',
                'evidence': 'No identifier enforcement claimed',
            }
        ],
        'errors': [
            {
                'id': 'failure',
                'operation': keys['operate'],
                'model': 'exception',
                'disposition': 'propagate',
                'success_discriminant': 'return',
                'support': 'required_implementation',
            }
        ],
        'applicability': [
            {
                'rule': rule,
                'context': 'active',
                'scope': [keys['operate']],
                'required_capabilities': ['declaration_identity', 'control_flow'],
            }
            for rule in CATALOG
        ],
        'external_provenance': [
            {
                'id': 'compiler',
                'absolute_path': str(executable),
                'sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                'distribution': 'pyright',
                'version': '1.1.414',
                'binary_or_generated': 'Pinned existing native tool; no source permission',
                'summaries': ['read'],
            }
        ],
    }
    observed = NativeObservation(
        model,
        (),
        (
            ObservedArtifact(
                absolute_path=str(executable),
                sha256=hashlib.sha256(executable.read_bytes()).hexdigest(),
                distribution='pyright',
                version=version('pyright'),
            ),
        ),
    )
    return value, observed


def load(root: Path, value: dict[str, object]) -> SemanticPolicyDocument:
    path = root / 'semantic.json'
    path.write_text(json.dumps(value))
    return load_semantic_policy(path)


@pytest.fixture
def inputs(tmp_path: Path) -> tuple[dict[str, object], NativeObservation]:
    return document(tmp_path)


def table(value: dict[str, object], name: str) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], value[name])


def test_native_join_validates_reviewed_inputs_but_never_semantic_pass(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation]
) -> None:
    value, model = inputs
    result = validate_semantic_inputs(
        tmp_path, load(tmp_path, value), {'active': model}
    )
    assert (len(result.bindings), 'control_flow' in result.missing_capabilities) == (
        len(model.model.symbols),
        True,
    )
    with pytest.raises(ValueError, match='COV002:.*not executed 37-rule'):
        result.require_semantic_compliance()
    assert type(result.input_hashes) is MappingProxyType


@pytest.mark.parametrize(
    'field', ('version', 'occurrence', 'column', 'success_path_calls')
)
def test_bool_integer_aliases_are_not_native_identity_values(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation], field: str
) -> None:
    value, _ = inputs
    targets = {
        'version': value,
        'occurrence': table(value, 'semantic_bindings')[0]['symbol'],
        'column': table(value, 'semantic_bindings')[0]['anchor'],
        'success_path_calls': table(value, 'use_cases_and_handlers')[0],
    }
    cast(dict[str, object], targets[field])[field] = True
    with pytest.raises(ValueError, match='COV002'):
        load(tmp_path, value)


@pytest.mark.parametrize('section', ('contexts', 'semantic_bindings', 'applicability'))
def test_required_nonempty_scopes_cannot_be_omitted(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation], section: str
) -> None:
    value, _ = inputs
    value[section] = []
    with pytest.raises(ValueError, match='COV002'):
        load(tmp_path, value)


@pytest.mark.parametrize(
    'category,field,bad',
    (
        ('consumer_slots', 'port', 'absent'),
        ('consumer_slots', 'required', False),
        ('ports', 'owner', 'absent'),
        ('public_contracts', 'kind', 'port'),
        ('effects', 'artifact', 'absent'),
        ('effects', 'reads', ['absent']),
        ('constructors_and_factories', 'assembly_sites', []),
        ('resources_and_storage', 'parent', 'absent'),
        ('identifiers', 'resource', 'absent'),
        ('errors', 'disposition', 'infallible'),
        ('external_provenance', 'summaries', ['absent']),
        ('applicability', 'context', 'absent'),
        ('applicability', 'rule', 'COV999'),
    ),
)
def test_unresolved_and_incompatible_reference_contracts_fail_and_repair(
    tmp_path: Path,
    inputs: tuple[dict[str, object], NativeObservation],
    category: str,
    field: str,
    bad: object,
) -> None:
    value, model = inputs
    damaged = copy.deepcopy(value)
    table(damaged, category)[0][field] = bad
    with pytest.raises(ValueError, match='COV002'):
        validate_semantic_inputs(tmp_path, load(tmp_path, damaged), {'active': model})
    assert (
        validate_semantic_inputs(
            tmp_path, load(tmp_path, value), {'active': model}
        ).document.version
        == 2
    )


@pytest.mark.parametrize(
    'change',
    (
        'unknown_field',
        'native_kind',
        'missing_evidence',
        'language',
        'symbol_context',
        'hash',
        'anchor',
        'occurrence',
        'duplicate_rule',
    ),
)
def test_unknown_policy_native_scope_and_anchor_cannot_be_claimed_compliant(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation], change: str
) -> None:
    value, model = inputs
    bindings = table(value, 'semantic_bindings')
    native = {'active': model}
    changes: dict[str, Callable[[], None]] = {
        'unknown_field': lambda: value.update(trusted=True),
        'native_kind': lambda: cast(dict[str, object], bindings[0]['symbol']).update(
            native_kind='invented'
        ),
        'language': lambda: table(value, 'contexts')[0].update(
            languages=['checked_javascript']
        ),
        'symbol_context': lambda: cast(dict[str, object], bindings[0]['symbol']).update(
            context='absent'
        ),
        'hash': lambda: cast(
            list[dict[str, object]], table(value, 'contexts')[0]['sources']
        )[0].update(sha256='0' * 64),
        'anchor': lambda: cast(dict[str, object], bindings[0]['anchor']).update(
            column=1
        ),
        'occurrence': lambda: cast(dict[str, object], bindings[0]['symbol']).update(
            occurrence=17
        ),
        'duplicate_rule': lambda: table(value, 'applicability').append(
            table(value, 'applicability')[0]
        ),
        'missing_evidence': native.clear,
    }
    changes[change]()
    with pytest.raises(ValueError, match='COV002'):
        validate_semantic_inputs(
            tmp_path,
            load(tmp_path, value),
            native,
        )


def test_duplicate_json_keys_and_unknown_schema_types_fail_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / 'bad.json'
    path.write_text('{"version":2,"version":2}')
    with pytest.raises(ValueError, match='COV002: duplicate'):
        load_semantic_policy(path)
    path.write_text('{"version":"2"}')
    with pytest.raises(ValueError, match='COV002'):
        load_semantic_policy(path)


@pytest.mark.parametrize('name', ('../outside.py', '/tmp/outside.py', 'domain/*.py'))
def test_input_paths_cannot_escape_or_grant_whole_tree_permission(
    tmp_path: Path, name: str
) -> None:
    with pytest.raises(ValueError, match='COV002'):
        input_integrity.exact_path(tmp_path, name)


def test_native_source_changes_and_external_artifacts_are_independent_provenance(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation]
) -> None:
    value, model = inputs
    (tmp_path / 'domain/example.py').write_text(SOURCE + 'changed = 7\n')
    with pytest.raises(ValueError, match='COV002:.*hash changed'):
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})
    (tmp_path / 'domain/example.py').write_text(SOURCE)
    table(value, 'external_provenance')[0]['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='COV002:.*artifact hash'):
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})


@pytest.mark.parametrize(
    'guard',
    (
        'actual == item.sha256',
        'bindings[export.symbol].role == role',
        'constructor.lifetime_owner is not None',
        'len(inventory) == len(document.applicability)',
        'native_artifacts == expected_artifacts',
    ),
)
def test_weakening_each_independent_contract_guard_loses_its_defect(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation], guard: str
) -> None:
    value, model = inputs
    targets = {
        'actual == item.sha256': (input_integrity, 'verify_input'),
        'bindings[export.symbol].role == role': (references, 'validate_relationships'),
        'constructor.lifetime_owner is not None': (
            references,
            'validate_relationships',
        ),
        'len(inventory) == len(document.applicability)': (
            validation,
            'validate_semantic_inputs',
        ),
        'native_artifacts == expected_artifacts': (
            validation,
            'validate_semantic_inputs',
        ),
    }
    module, function = targets[guard]
    source = inspect.getsource(module)
    assert guard in source
    if guard == 'actual == item.sha256':
        configuration = tmp_path / 'config.json'
        configuration.write_text('{}')
        fact = Input(
            path='config.json',
            sha256=hashlib.sha256(configuration.read_bytes()).hexdigest(),
        )
        table(value, 'contexts')[0]['configuration'] = [fact.model_dump(mode='json')]
        model = replace(model, configuration=(fact,))
        configuration.write_text('[]')
    else:
        mutations = {
            'bindings[export.symbol].role == role': lambda: table(
                value, 'public_contracts'
            )[0].update(kind='port'),
            'constructor.lifetime_owner is not None': lambda: table(
                value, 'constructors_and_factories'
            )[0].update(lifetime_owner=None),
            'len(inventory) == len(document.applicability)': lambda: table(
                value, 'applicability'
            ).append(table(value, 'applicability')[0]),
            'native_artifacts == expected_artifacts': lambda: table(
                value, 'external_provenance'
            )[0].update(version='invented'),
        }
        mutations[guard]()
    with pytest.raises(ValueError, match='COV002'):
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})
    namespace = dict(module.__dict__)
    exec(source.replace(guard, 'True'), namespace)
    driver = dict(validation.__dict__)
    driver[function] = namespace[function]
    exec(
        inspect.getsource(validation.validate_semantic_inputs).replace(guard, 'True'),
        driver,
    )
    weakened = cast(Callable[..., object], driver['validate_semantic_inputs'])
    assert weakened(tmp_path, load(tmp_path, value), {'active': model}) is not None


def test_missing_and_symlinked_first_party_inputs_never_use_external_artifact_permission(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation]
) -> None:
    value, model = inputs
    source = tmp_path / 'domain/example.py'
    retained = tmp_path / 'retained.py'
    source.rename(retained)
    with pytest.raises(ValueError, match='COV002:.*missing'):
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})
    outside = tmp_path.parent / (tmp_path.name + '-external.py')
    outside.write_text(SOURCE)
    source.symlink_to(outside)
    with pytest.raises(ValueError, match='COV002:.*escapes'):
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})


def test_empty_native_binding_inventory_and_unresolved_member_scope_are_not_metadata_passes(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation]
) -> None:
    value, _ = inputs
    table(value, 'contexts')[0]['expected_bindings'] = []
    with pytest.raises(ValueError, match='COV002'):
        load(tmp_path, value)
    with pytest.raises(ValueError, match='COV002'):
        semantic_model(
            tmp_path / 'unknown',
            {'broken.py': 'def use(value):\n    return value.missing()\n'},
        )


def test_summary_purity_and_lifetime_slot_cannot_waive_mutation_or_construction(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation]
) -> None:
    value, model = inputs
    effect = table(value, 'effects')[0]
    symbol = effect['target']
    effect.update(
        categories=['pure'],
        regions=[{'id': 'input', 'symbol': symbol, 'kind': 'input'}],
        writes=['input'],
    )
    with pytest.raises(ValueError, match='COV002:.*pure summary'):
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})
    effect['writes'] = []
    result = validate_semantic_inputs(
        tmp_path, load(tmp_path, value), {'active': model}
    )
    with pytest.raises(ValueError, match='COV002'):
        result.require_semantic_compliance()


def test_native_anchor_diagnostic_uses_observed_source_location(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation]
) -> None:
    value, model = inputs
    anchor = cast(dict[str, object], table(value, 'semantic_bindings')[0]['anchor'])
    expected = f'domain/example.py:{anchor["line"]}:{anchor["column"]}'
    anchor['column'] = 99
    with pytest.raises(ValueError, match='COV002') as failure:
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})
    assert expected in str(failure.value)


def test_first_party_internal_symlink_is_not_an_exact_input(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation]
) -> None:
    value, model = inputs
    source = tmp_path / 'domain/example.py'
    retained = source.with_name('retained.py')
    source.rename(retained)
    source.symlink_to(retained)
    with pytest.raises(ValueError, match='COV002:.*symlink'):
        validate_semantic_inputs(tmp_path, load(tmp_path, value), {'active': model})


@pytest.mark.parametrize(
    'defect',
    ('absent', 'hash', 'version', 'configuration', 'language', 'kind', 'duplicate'),
)
def test_reviewed_provenance_cannot_replace_independent_native_observations(
    tmp_path: Path, inputs: tuple[dict[str, object], NativeObservation], defect: str
) -> None:
    value, observed = inputs
    value = copy.deepcopy(value)
    artifact = observed.artifacts[0]
    variants = {
        'absent': replace(observed, artifacts=()),
        'hash': replace(
            observed, artifacts=(artifact.model_copy(update={'sha256': '0' * 64}),)
        ),
        'version': replace(
            observed, artifacts=(artifact.model_copy(update={'version': 'invented'}),)
        ),
        'configuration': replace(
            observed, configuration=(Input(path='unobserved.json', sha256='0' * 64),)
        ),
        'language': observed,
        'kind': replace(
            observed,
            model=replace(
                observed.model,
                symbols=(
                    replace(observed.model.symbols[0], kind='native_type_alias'),
                    *observed.model.symbols[1:],
                ),
            ),
        ),
        'duplicate': replace(
            observed,
            model=replace(
                observed.model,
                symbols=(*observed.model.symbols, observed.model.symbols[0]),
            ),
        ),
    }
    languages = {'language': ['python_stub']}
    table(value, 'contexts')[0]['languages'] = languages.get(defect, ['python'])
    with pytest.raises(ValueError, match='COV002:.*observed'):
        validate_semantic_inputs(
            tmp_path, load(tmp_path, value), {'active': variants[defect]}
        )
    assert (
        validate_semantic_inputs(
            tmp_path, load(tmp_path, inputs[0]), {'active': observed}
        ).document.version
        == 2
    )
