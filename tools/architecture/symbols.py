from dataclasses import dataclass
from typing import Literal

from tools.architecture.inventory import Source

SymbolKind = Literal[
    'module', 'class', 'function', 'parameter', 'variable', 'attribute', 'import'
]
ReferenceKind = Literal['read', 'type', 'base', 'import', 'decorator', 'declaration']
Capability = Literal[
    'declaration_identity',
    'explicit_call_targets',
    'nominal_type_locations',
    'structured_types',
    'alias_ownership',
    'control_flow',
    'implicit_calls',
    'runtime_dispatch',
    'effect_summaries',
    'dynamic_import_targets',
]


@dataclass(frozen=True, order=True)
class Location:
    """One-based lines and zero-based UTF-16 columns, with an exclusive end."""

    path: str
    line: int
    column: int
    end_line: int
    end_column: int


@dataclass(frozen=True)
class Provenance:
    path: str
    sha256: str
    project_path: str | None


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: SymbolKind
    location: Location
    provenance: Provenance
    container: Location | None


@dataclass(frozen=True)
class Reference:
    source: Symbol
    target: Symbol
    location: Location
    kind: ReferenceKind
    captured: bool = False


@dataclass(frozen=True)
class Call:
    """An explicit lexical call to a native declaration, without dispatch proof."""

    caller: Symbol
    target: Symbol
    location: Location
    kind: Literal['function', 'constructor']
    aliases: tuple[Reference, ...] = ()


@dataclass(frozen=True)
class NominalType:
    """A native type-definition location, without generic or flow-type claims."""

    location: Location
    target: Symbol


@dataclass(frozen=True)
class Capabilities:
    supported: tuple[Capability, ...]
    missing: tuple[Capability, ...]

    def require(self, capability: Capability) -> None:
        if capability not in self.supported:
            raise ValueError(
                'COV002: native semantic adapter lacks required capability: '
                + capability
            )


NATIVE_CAPABILITIES = Capabilities(
    ('declaration_identity', 'explicit_call_targets', 'nominal_type_locations'),
    (
        'structured_types',
        'alias_ownership',
        'control_flow',
        'implicit_calls',
        'runtime_dispatch',
        'effect_summaries',
        'dynamic_import_targets',
    ),
)


@dataclass(frozen=True)
class SemanticModel:
    sources: tuple[Source, ...]
    symbols: tuple[Symbol, ...]
    references: tuple[Reference, ...]
    calls: tuple[Call, ...]
    capabilities: Capabilities = NATIVE_CAPABILITIES
