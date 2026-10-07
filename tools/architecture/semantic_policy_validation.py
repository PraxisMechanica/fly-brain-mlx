import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from types import MappingProxyType
from typing import NoReturn, get_args

from .semantic_policy_inputs import read_bytes, verify_anchor, verify_input
from .semantic_policy_records import Binding, NativeObservation, SymbolKey
from .semantic_policy_references import index, symbol_references, validate_relationships
from .semantic_policy_schema import CATALOG, SemanticPolicyDocument, require, unique
from .symbols import SemanticModel, Symbol, SymbolKind


@dataclass(frozen=True)
class ValidatedSemanticInputs:
    document: SemanticPolicyDocument
    bindings: Mapping[SymbolKey, Binding]
    input_hashes: Mapping[str, str]
    missing_capabilities: tuple[str, ...]

    def require_semantic_compliance(self) -> NoReturn:
        raise ValueError(
            'COV002: reviewed semantic inputs are not executed 37-rule analysis; '
            + ', '.join(self.missing_capabilities)
        )


def observed_bindings(context: str, model: SemanticModel) -> dict[SymbolKey, Symbol]:
    model.capabilities.require('declaration_identity')
    require(
        len(set(model.symbols)) == len(model.symbols),
        'duplicate observed native identity',
    )
    result: dict[SymbolKey, Symbol] = {}
    occurrences: dict[tuple[str, str, str], int] = {}
    for symbol in sorted(model.symbols, key=lambda s: s.location):
        require(
            symbol.kind in get_args(SymbolKind),
            'unsupported observed native kind: ' + str(symbol.kind),
        )
        path = symbol.provenance.project_path
        if path is None:
            path = symbol.provenance.path
        group = path, symbol.name, symbol.kind
        occurrence = occurrences.get(group, 0)
        occurrences[group] = occurrence + 1
        key = SymbolKey(
            context=context,
            path=path,
            qualified_name=symbol.name,
            native_kind=symbol.kind,
            occurrence=occurrence,
        )
        result[key] = symbol
    return result


def validate_semantic_inputs(
    root: Path,
    document: SemanticPolicyDocument,
    observed: Mapping[str, NativeObservation],
) -> ValidatedSemanticInputs:
    root = root.resolve()
    contexts = {item.id: item for item in document.contexts}
    require(len(contexts) == len(document.contexts), 'duplicate context')
    require(set(contexts) == set(observed), 'observed native context inventory differs')
    artifacts = {item.id: item for item in document.external_provenance}
    require(len(artifacts) == len(document.external_provenance), 'duplicate artifact')
    hashes: dict[str, str] = {}
    for artifact in artifacts.values():
        path = Path(artifact.absolute_path)
        require(
            all((path.is_absolute(), str(path.resolve()) == artifact.absolute_path)),
            'external artifact path is not canonical absolute',
        )
        actual = hashlib.sha256(read_bytes(path)).hexdigest()
        require(
            actual == artifact.sha256, 'external artifact hash changed: ' + artifact.id
        )
        hashes[artifact.absolute_path] = actual
        for item in (*artifact.declaration_hashes, *artifact.checked_stubs):
            hashes[item.path] = verify_input(root, item)
    native: dict[SymbolKey, Symbol] = {}
    for name, context in contexts.items():
        observation = observed[name]
        model = observation.model
        require(
            set(context.languages) <= {'python', 'python_stub'},
            'unsupported native language context: ' + name,
        )
        unique(context.languages, 'language')
        unique(context.artifacts, 'context artifact')
        require(
            not set(model.capabilities.supported) & set(model.capabilities.missing),
            'native capability evidence is contradictory',
        )
        require(set(context.artifacts) <= set(artifacts), 'unknown context artifact')
        expected_artifacts = {
            artifacts[a].absolute_path: (
                artifacts[a].sha256,
                artifacts[a].distribution,
                artifacts[a].version,
            )
            for a in context.artifacts
        }
        native_artifacts = {
            a.absolute_path: (a.sha256, a.distribution, a.version)
            for a in observation.artifacts
        }
        require(
            all(
                (
                    len(native_artifacts) == len(observation.artifacts),
                    len(expected_artifacts) == len(context.artifacts),
                    native_artifacts == expected_artifacts,
                )
            ),
            'observed artifact inventory/version/hash differs: ' + name,
        )
        sources = {item.path: item.sha256 for item in context.sources}
        require(len(sources) == len(context.sources), 'duplicate source input')
        unique(
            tuple(item.path for item in context.configuration), 'configuration input'
        )
        require(
            all(
                (
                    len(sources) == len(model.sources),
                    sources == {s.path: s.sha256 for s in model.sources},
                )
            ),
            'observed source inventory/hash differs: ' + name,
        )
        require(
            {i.path: i.sha256 for i in context.configuration}
            == {i.path: i.sha256 for i in observation.configuration},
            'observed configuration inventory/hash differs: ' + name,
        )
        unique(
            tuple(i.path for i in observation.configuration), 'observed configuration'
        )
        require(
            set(context.languages)
            == {
                {'.py': 'python', '.pyi': 'python_stub'}.get(Path(s.path).suffix)
                for s in model.sources
            },
            'observed native language inventory differs: ' + name,
        )
        for item in (*context.sources, *context.configuration):
            hashes[item.path] = verify_input(root, item)
        facts = observed_bindings(name, model)
        require(
            set(context.expected_bindings) == set(facts),
            'expected native binding inventory differs: ' + name,
        )
        unique(tuple(str(s) for s in context.expected_bindings), 'expected binding')
        native.update(facts)
    bindings: dict[SymbolKey, Binding] = {}
    for item in document.semantic_bindings:
        require(item.symbol not in bindings, 'duplicate semantic binding')
        require(
            item.symbol in native,
            'unknown native binding: ' + item.symbol.qualified_name,
        )
        require(item.owner in document.owners, 'unknown binding owner')
        require(
            item.anchor.artifact in contexts[item.symbol.context].artifacts,
            'binding artifact is outside its context',
        )
        verify_anchor(root, item, native[item.symbol])
        if native[item.symbol].provenance.project_path is None:
            artifact = artifacts[item.anchor.artifact]
            require(
                (item.symbol.path, item.anchor.source_sha256)
                == (artifact.absolute_path, artifact.sha256),
                'external symbol is not its pinned artifact',
            )
        bindings[item.symbol] = item
    require(set(bindings) == set(native), 'semantic binding coverage differs')
    for ref in symbol_references(document):
        require(ref in bindings, 'unresolved symbol reference: ' + ref.qualified_name)
    tables = {
        'port': index(document.ports, 'port'),
        'slot': index(document.consumer_slots, 'slot'),
        'export': index(document.public_contracts, 'export'),
        'effect': index(document.effects, 'effect'),
        'constructor': index(document.constructors_and_factories, 'constructor'),
        'resource': index(document.resources_and_storage, 'resource'),
        'identifier': index(document.identifiers, 'identifier'),
        'error': index(document.errors, 'error'),
        'use_case': index(document.use_cases_and_handlers, 'use_case'),
    }
    validate_relationships(document, bindings, tables)
    inventory = {(item.context, item.rule) for item in document.applicability}
    require(
        all(
            (
                inventory == set(product(contexts, CATALOG)),
                len(inventory) == len(document.applicability),
            )
        ),
        'rule/context inventory is not exact37',
    )
    missing: set[str] = set()
    for rule in document.applicability:
        unique(rule.required_capabilities, 'required capability')
        for item in rule.fixtures:
            hashes[item.path] = verify_input(root, item)
        missing.update(
            set(rule.required_capabilities)
            - set(observed[rule.context].model.capabilities.supported)
        )
        if rule.mechanism is None:
            missing.add('unexecuted predicate: ' + rule.rule)
    for path, expected in hashes.items():
        actual = root / path
        require(
            hashlib.sha256(read_bytes(actual)).hexdigest() == expected,
            'input changed during semantic join: ' + path,
        )
    return ValidatedSemanticInputs(
        document,
        MappingProxyType(bindings),
        MappingProxyType(hashes),
        tuple(sorted(missing)),
    )
