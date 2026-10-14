import ast
import hashlib
from collections.abc import Sequence
from pathlib import Path
from types import MappingProxyType

from .inventory import Finding, Ownership, Source, discover, reconcile, source_paths
from .policy import (
    Classification,
    Policy,
    Review,
    binding_fingerprint,
    declaration_fingerprint,
)


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


def review_policy(
    root: Path, policy: Policy, *, source_scope: Sequence[str] | None = None
) -> Review:
    root = root.resolve()
    if source_scope is None:
        sources = discover(root, policy.document.source_roots)
        paths = {source.path for source in sources}
    else:
        paths = {
            path.relative_to(root).as_posix()
            for path in source_paths(root, policy.document.source_roots)
        }
        selected = tuple(sorted(set(source_scope) & paths))
        sources = discover(root, selected) if selected else ()
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
    if sources:
        findings.extend(reconcile(sources, ownership))
    for path in sorted(policy.files.keys() - paths):
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
    if source_scope is not None:
        referenced = [symbol for symbol in referenced if symbol.path in source_scope]
    for path in sorted(paths - policy.files.keys()):
        if source_scope is not None:
            findings.append(
                Finding('COV001', path, 1, 'Source has no reviewed owner/role')
            )
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
