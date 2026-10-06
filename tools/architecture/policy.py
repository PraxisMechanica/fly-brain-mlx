import ast
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .inventory import Declaration, Finding, Ownership, Source, discover, reconcile

Role = Literal[
    'types',
    'ports',
    'rules',
    'service',
    'repository',
    'command_adapter',
    'module',
    'external_adapter',
    'composition',
    'entrypoint',
    'infrastructure',
    'tooling',
    'test',
    'system_test',
    'typing_contract',
    'package',
]
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
Commit = Annotated[str, Field(pattern=r'^[0-9a-f]{40}$')]
Name = Annotated[str, Field(pattern=r'^[A-Za-z][A-Za-z0-9_.-]*$')]
Text = Annotated[str, Field(min_length=1, pattern=r'\S')]
Rule = Annotated[
    str,
    Field(
        pattern=r'^(OWN00[1-6]|DEP00[1-4]|DI00[1-4]|ROLE00[1-7]|STATE00[1-3]|'
        r'(ISP|OCP|LSP|VALUE|COMP|ERR|TYPE|CODE|STYLE)001|COV00[1-4])$'
    ),
]


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


class Owner(Record):
    kind: Literal['domain', 'system', 'tooling', 'composition', 'external']
    responsibility: Text


class Classification(Record):
    owner: Name
    role: Role


class Symbol(Record):
    path: Text
    name: Text


class FrozenSource(Record):
    kind: Literal['historical_source', 'reference_source']
    sha256: Digest
    commit: Commit
    origin: Text


class FilePolicy(Classification):
    declaration_count: Annotated[int, Field(ge=0)]
    declaration_sha256: Digest
    binding_sha256: Digest
    symbols: dict[str, Classification] = Field(default_factory=dict)
    public: tuple[str, ...] = ()
    composition: tuple[str, ...] = ()
    frozen: FrozenSource | None = None


class Resource(Record):
    owner: Name
    kind: Literal['input', 'artifact', 'runtime', 'workflow', 'database_table']
    relationship: Literal['independent', 'storage_only', 'unresolved']
    parent: Name | None = None
    evidence: Annotated[tuple[Symbol, ...], Field(min_length=1)]
    decision: Text


class Identifier(Record):
    owner: Name
    resource: Name
    representation: Literal['distinct_value', 'closed_literal', 'primitive']
    evidence: Annotated[tuple[Symbol, ...], Field(min_length=1)]
    decision: Text


class Absence(Record):
    evidence: Annotated[tuple[str, ...], Field(min_length=1)]
    decision: Text


class RecordedFinding(Record):
    rule: Rule
    symbol: Symbol
    message: Text


class PolicyDocument(Record):
    version: Literal[1]
    reviewed_commit: Commit
    coverage: Literal['named_declarations_and_syntactic_binding_review']
    source_roots: Annotated[tuple[str, ...], Field(min_length=1)]
    owners: Annotated[dict[Name, Owner], Field(min_length=1)]
    files: Annotated[dict[str, FilePolicy], Field(min_length=1)]
    resources: dict[Name, Resource]
    identifiers: dict[Name, Identifier]
    absences: dict[Literal['database', 'http_endpoints'], Absence]
    limitations: Annotated[tuple[Text, ...], Field(min_length=1)]
    findings: tuple[RecordedFinding, ...] = ()

    @field_validator('version', mode='before')
    @classmethod
    def exact_version(cls, value: object) -> object:
        if type(value) is not int or value != 1:
            raise ValueError('Unsupported policy version')
        return value


@dataclass(frozen=True)
class Policy:
    document: PolicyDocument
    files: Mapping[str, FilePolicy]


@dataclass(frozen=True)
class Review:
    sources: tuple[Source, ...]
    ownership: Mapping[str, Ownership]
    symbols: Mapping[tuple[str, str], Classification]
    findings: tuple[Finding, ...]
    recorded_findings: tuple[Finding, ...]
    limitations: tuple[str, ...]


def declaration_fingerprint(items: Sequence[Declaration]) -> str:
    encoded = json.dumps(sorted((item.name, item.kind) for item in items)).encode()
    return hashlib.sha256(encoded).hexdigest()


def binding_fingerprint(tree: ast.Module) -> str:
    facts: list[tuple[str, str, str]] = []

    def visit(node: ast.AST, scope: str = '') -> None:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            facts.append((scope, 'declaration', node.name))
            scope = scope + '.' + node.name
        if isinstance(node, ast.arg):
            facts.append((scope, 'parameter', node.arg))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            facts.append((scope, type(node.ctx).__name__, node.id))
        elif isinstance(node, ast.Attribute) and isinstance(
            node.ctx, (ast.Store, ast.Del)
        ):
            facts.append((scope, type(node.ctx).__name__, ast.unparse(node)))
        elif isinstance(node, ast.Import):
            facts.extend(
                (scope, 'import', alias.name + ':' + (alias.asname or ''))
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            facts.extend(
                (
                    scope,
                    'from_import',
                    '.' * node.level
                    + (node.module or '')
                    + ':'
                    + alias.name
                    + ':'
                    + (alias.asname or ''),
                )
                for alias in node.names
            )
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            facts.extend((scope, type(node).__name__, name) for name in node.names)
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
            if node.name is not None:
                facts.append((scope, type(node).__name__, node.name))
        elif isinstance(node, ast.MatchMapping) and node.rest is not None:
            facts.append((scope, 'MatchMapping', node.rest))
        for child in ast.iter_child_nodes(node):
            visit(child, scope)

    visit(tree)
    return hashlib.sha256(json.dumps(sorted(facts)).encode()).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('COV002: duplicate policy key: ' + name)
        result[name] = value
    return result


def _path(value: str) -> None:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or path.as_posix() != value
        or '..' in path.parts
        or any(character in value for character in '\\*?[]\x00')
    ):
        raise ValueError('COV002: policy path is not exact and relative: ' + value)


def _classification(value: Classification, document: PolicyDocument) -> None:
    if value.owner not in document.owners:
        raise ValueError('COV002: unknown classified owner: ' + value.owner)


def _symbol(value: Symbol, document: PolicyDocument) -> None:
    if value.path not in document.files or not re.fullmatch(
        r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', value.name
    ):
        raise ValueError(
            'COV002: invalid policy symbol: ' + value.path + ':' + value.name
        )


def _validate_file(path: str, record: FilePolicy, document: PolicyDocument) -> None:
    if PurePosixPath(path).suffix not in ('.py', '.pyi'):
        raise ValueError('COV002: unsupported policy source: ' + path)
    _classification(record, document)
    for name, override in record.symbols.items():
        _symbol(Symbol(path=path, name=name), document)
        _classification(override, document)
    for group in (record.public, record.composition):
        if len(set(group)) != len(group):
            raise ValueError('COV002: ambiguous symbol classification: ' + path)
        for name in group:
            _symbol(Symbol(path=path, name=name), document)
    for name in record.public:
        role = record.symbols.get(name, record).role
        if role not in ('types', 'ports'):
            raise ValueError('COV002: public neutral export has implementation role')
    for name in record.composition:
        role = record.symbols.get(name, record).role
        if role not in ('composition', 'module'):
            raise ValueError('COV002: composition site has non-assembly role')


def _validate_resources(document: PolicyDocument) -> None:
    for name, resource in document.resources.items():
        if resource.owner not in document.owners:
            raise ValueError('COV002: unknown resource owner: ' + name)
        if (resource.relationship == 'storage_only') != (resource.parent is not None):
            raise ValueError('COV002: invalid resource parent relationship: ' + name)
        if resource.parent is not None:
            parent = document.resources.get(resource.parent)
            if (
                parent is None
                or parent.owner != resource.owner
                or resource.parent == name
            ):
                raise ValueError('COV002: invalid storage-only parent: ' + name)
        for evidence in resource.evidence:
            _symbol(evidence, document)
        visited = {name}
        current = resource
        while current.parent is not None:
            if current.parent in visited:
                raise ValueError('COV002: resource parent cycle: ' + name)
            visited.add(current.parent)
            parent = document.resources.get(current.parent)
            if parent is None:
                raise ValueError('COV002: resource parent is absent: ' + name)
            current = parent


def _validate_identifiers(document: PolicyDocument) -> None:
    for name, identifier in document.identifiers.items():
        resource = document.resources.get(identifier.resource)
        if resource is None or resource.owner != identifier.owner:
            raise ValueError('COV002: identifier resource ownership differs: ' + name)
        for evidence in identifier.evidence:
            _symbol(evidence, document)


def _validate_absences(document: PolicyDocument) -> None:
    if set(document.absences) != {'database', 'http_endpoints'}:
        raise ValueError('COV002: responsibility inventory is incomplete')
    for name, absence in document.absences.items():
        if name == 'database' and any(
            resource.kind == 'database_table'
            for resource in document.resources.values()
        ):
            raise ValueError('COV002: database absence contradicts an owned table')
        if not set(absence.evidence) <= document.files.keys():
            raise ValueError('COV002: absence evidence is outside source inventory')


def _validate(document: PolicyDocument) -> None:
    if len(set(document.source_roots)) != len(document.source_roots):
        raise ValueError('COV002: duplicate source root')
    for path in (*document.source_roots, *document.files):
        _path(path)
    for path, record in document.files.items():
        _validate_file(path, record, document)
    _validate_resources(document)
    _validate_identifiers(document)
    _validate_absences(document)
    for finding in document.findings:
        _symbol(finding.symbol, document)


def load_policy(path: Path) -> Policy:
    try:
        text = path.read_text()
        json.loads(text, object_pairs_hook=_unique_object)
        document = PolicyDocument.model_validate_json(text)
    except (OSError, UnicodeError, ValidationError, json.JSONDecodeError) as error:
        raise ValueError(
            'COV002: architecture policy could not be loaded: ' + str(error)
        ) from error
    _validate(document)
    return Policy(document, MappingProxyType(dict(document.files)))


def _binding_review(root: Path, source: Source) -> str:
    try:
        content = (root / source.path).read_bytes()
    except OSError as error:
        raise ValueError(
            'COV002: ownership source could not be read: ' + source.path
        ) from error
    if hashlib.sha256(content).hexdigest() != source.sha256:
        raise ValueError(
            'COV002: source changed during ownership review: ' + source.path
        )
    return binding_fingerprint(ast.parse(content))


def _recorded_findings(
    policy: Policy, sources: Sequence[Source]
) -> tuple[Finding, ...]:
    locations = {
        (source.path, item.name): item.line
        for source in sources
        for item in source.declarations
    }
    result = [
        Finding(
            item.rule,
            item.symbol.path,
            locations.get((item.symbol.path, item.symbol.name), 1),
            item.message,
        )
        for item in policy.document.findings
    ]
    for name, resource in policy.document.resources.items():
        if resource.relationship == 'unresolved':
            symbol = resource.evidence[0]
            result.append(
                Finding(
                    'COV001',
                    symbol.path,
                    locations.get((symbol.path, symbol.name), 1),
                    'Unresolved resource ownership: ' + name + '. ' + resource.decision,
                )
            )
    for name, identifier in policy.document.identifiers.items():
        if identifier.representation == 'primitive':
            symbol = identifier.evidence[0]
            result.append(
                Finding(
                    'VALUE001',
                    symbol.path,
                    locations.get((symbol.path, symbol.name), 1),
                    'Reviewed primitive resource identifier: '
                    + name
                    + '. '
                    + identifier.decision,
                )
            )
    return tuple(result)


def review_policy(root: Path, policy: Policy) -> Review:
    root = root.resolve()
    sources = discover(root, policy.document.source_roots)
    ownership: dict[str, Ownership] = {}
    symbols: dict[tuple[str, str], Classification] = {}
    findings: list[Finding] = []
    for source in sources:
        record = policy.files.get(source.path)
        if record is None:
            continue
        names = tuple(item.name for item in source.declarations)
        if (
            len(source.declarations) != record.declaration_count
            or declaration_fingerprint(source.declarations) != record.declaration_sha256
        ):
            findings.append(
                Finding('COV001', source.path, 1, 'Reviewed declaration set changed')
            )
            continue
        if _binding_review(root, source) != record.binding_sha256:
            findings.append(
                Finding('COV001', source.path, 1, 'Unreviewed source bindings')
            )
            continue
        explicit = set(record.symbols) | set(record.public) | set(record.composition)
        for name in sorted(explicit - set(names)):
            findings.append(
                Finding(
                    'COV001', source.path, 1, 'Mapped declaration is absent: ' + name
                )
            )
        ownership[source.path] = Ownership(
            record.owner,
            record.role,
            names,
            record.frozen.sha256 if record.frozen is not None else None,
        )
        for item in source.declarations:
            symbols[source.path, item.name] = record.symbols.get(
                item.name, Classification(owner=record.owner, role=record.role)
            )
    findings.extend(reconcile(sources, ownership))
    for path in sorted(policy.files.keys() - {source.path for source in sources}):
        findings.append(
            Finding('COV001', path, 1, 'Policy source is absent from discovery')
        )
    referenced = [
        symbol
        for record in (
            *policy.document.resources.values(),
            *policy.document.identifiers.values(),
        )
        for symbol in record.evidence
    ]
    referenced.extend(finding.symbol for finding in policy.document.findings)
    for symbol in referenced:
        if (symbol.path, symbol.name) not in symbols:
            findings.append(
                Finding(
                    'COV001',
                    symbol.path,
                    1,
                    'Unresolved policy evidence: ' + symbol.name,
                )
            )
    return Review(
        sources,
        MappingProxyType(ownership),
        MappingProxyType(symbols),
        tuple(findings),
        _recorded_findings(policy, sources),
        policy.document.limitations,
    )
