from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import Field, field_validator

from .policy import Commit, Digest, Name, Record, Role, Text
from .policy import Owner as Owner
from .symbols import Capability, SemanticModel, SymbolKind

Nonnegative = Annotated[int, Field(ge=0)]
Positive = Annotated[int, Field(ge=1)]
Language = Literal[
    'python',
    'python_stub',
    'checked_javascript',
    'typescript_declaration',
    'cpp_fragment',
]
Phase = Literal['declaration', 'assembly', 'runtime', 'value_initialization']


class SymbolKey(Record):
    context: Name
    path: Text
    qualified_name: Text
    native_kind: SymbolKind
    occurrence: Nonnegative

    def __hash__(self) -> int:
        return hash(
            (
                self.context,
                self.path,
                self.qualified_name,
                self.native_kind,
                self.occurrence,
            )
        )


class NativeAnchor(Record):
    source_sha256: Digest
    artifact: Name
    line: Positive
    column: Nonnegative
    end_line: Positive
    end_column: Nonnegative


class Input(Record):
    path: Text
    sha256: Digest


class ObservedArtifact(Record):
    absolute_path: Text
    sha256: Digest
    distribution: Text
    version: Text


@dataclass(frozen=True)
class NativeObservation:
    model: SemanticModel
    configuration: tuple[Input, ...]
    artifacts: tuple[ObservedArtifact, ...]


class Context(Record):
    id: Name
    languages: Annotated[tuple[Language, ...], Field(min_length=1)]
    sources: Annotated[tuple[Input, ...], Field(min_length=1)]
    configuration: tuple[Input, ...] = ()
    artifacts: Annotated[tuple[Name, ...], Field(min_length=1)]
    expected_bindings: Annotated[tuple[SymbolKey, ...], Field(min_length=1)]
    build_variant: Text
    historical_revision: Commit | None = None


class Placement(Record):
    owner: Name
    roots: Annotated[tuple[Text, ...], Field(min_length=1)]
    outside_role: (
        Literal[
            'entrypoint',
            'composition',
            'infrastructure',
            'external_adapter',
            'tooling',
            'system_test',
            'typing_contract',
        ]
        | None
    ) = None


class Binding(Record):
    symbol: SymbolKey
    anchor: NativeAnchor
    owner: Name
    role: Role
    phase: Phase
    semantic_kind: Literal[
        'business_policy',
        'neutral_value',
        'consumer_port',
        'business_service',
        'owned_repository',
        'transport_mechanics',
        'provider_mechanics',
        'assembly',
        'generic_mechanics',
        'literal_configuration',
        'numerical_data',
        'runtime_storage',
        'test_or_analysis',
    ]
    evidence: Text


class Slot(Record):
    id: Name
    consumer: SymbolKey
    symbol: SymbolKey
    kind: Literal[
        'field', 'parameter', 'capture', 'default', 'global', 'context_lookup'
    ]
    nature: Literal[
        'collaborator',
        'immutable_configuration',
        'plain_value',
        'input_storage',
        'fresh_local_storage',
        'runtime_storage',
        'mechanical_provider_state',
    ]
    required: bool
    port: Name | None = None
    capabilities_used: tuple[SymbolKey, ...] = ()
    factory: Name | None = None
    lifetime_owner: Name | None = None
    value_owner: Name | None = None
    resource: Name | None = None
    alias_region: Name | None = None


class Port(Record):
    id: Name
    symbol: SymbolKey
    owner: Name
    members: Annotated[tuple[SymbolKey, ...], Field(min_length=1)]
    consumers: Annotated[tuple[SymbolKey, ...], Field(min_length=1)]
    public_types: tuple[Name, ...] = ()
    neutral_errors: tuple[Name, ...] = ()
    factory_lifetime: Name | None = None
    purity: Literal['effectful', 'pure_required', 'declaration']


class PublicContract(Record):
    id: Name
    owner: Name
    symbol: SymbolKey
    members: tuple[SymbolKey, ...] = ()
    kind: Literal['value', 'port']
    member_types: tuple[SymbolKey, ...] = ()
    foreign_types: tuple[Name, ...] = ()
    storage: Literal['immutable', 'readonly_borrow', 'ownership_unresolved']
    identifier_fields: tuple[Name, ...] = ()
    value_operations: tuple[SymbolKey, ...] = ()
    reexports: tuple[SymbolKey, ...] = ()


class Region(Record):
    id: Name
    symbol: SymbolKey
    kind: Literal[
        'input',
        'fresh_local',
        'unescaped_initialization',
        'captured',
        'global',
        'runtime',
    ]


class Effect(Record):
    id: Name
    target: SymbolKey
    artifact: Name
    categories: Annotated[
        tuple[
            Literal[
                'pure',
                'storage_read',
                'storage_write',
                'clock',
                'random',
                'environment',
                'logger',
                'process',
                'device_allocation',
                'device_stream',
                'device_evaluation',
                'dependency_lookup',
                'connection_lifecycle',
                'provider_lifecycle',
                'unresolved',
            ],
            ...,
        ],
        Field(min_length=1),
    ]
    preconditions: Text
    regions: tuple[Region, ...] = ()
    reads: tuple[Name, ...] = ()
    writes: tuple[Name, ...] = ()
    aliases: tuple[Name, ...] = ()
    escapes: tuple[Name, ...] = ()
    returns: tuple[Name, ...] = ()
    raises: tuple[Name, ...] = ()
    implicit_operations: tuple[SymbolKey, ...] = ()
    callbacks: tuple[Name, ...] = ()
    evidence: Text


class Constructor(Record):
    id: Name
    target: SymbolKey
    category: Literal[
        'owned_value',
        'collaborator',
        'representation_conversion',
        'generic_resource',
        'unresolved',
    ]
    produced_type: SymbolKey
    port: Name | None = None
    assembly_sites: tuple[SymbolKey, ...] = ()
    factory_slot: Name | None = None
    lifetime_owner: Name | None = None
    initialization_regions: tuple[Name, ...] = ()


class UseCase(Record):
    id: Name
    operation: SymbolKey
    owner: Name
    request_contract: Name
    result_contract: Name
    handler: SymbolKey
    operation_port: Name
    success_path_calls: Literal[1]
    transport_operations: tuple[SymbolKey, ...] = ()
    runtime_entrypoint: SymbolKey | None = None
    provider_discriminators: tuple[SymbolKey, ...] = ()

    @field_validator('success_path_calls', mode='before')
    @classmethod
    def exact_call_count(cls, value: object) -> object:
        if type(value) is not int or value != 1:
            raise ValueError('COV002: handler call count must be integer one')
        return value


class Resource(Record):
    id: Name
    owner: Name
    relationship: Literal['independent', 'storage_only', 'unresolved']
    parent: Name | None = None
    operations: tuple[SymbolKey, ...] = ()
    persistence: tuple[SymbolKey, ...] = ()
    storage_targets: tuple[Text, ...] = ()
    protocol_targets: tuple[Text, ...] = ()
    schema_targets: tuple[Text, ...] = ()
    lifetime_owner: Name
    public_contracts: tuple[Name, ...] = ()
    evidence: Text


class Identifier(Record):
    id: Name
    resource: Name
    owner: Name
    distinct_type: SymbolKey
    representation: Text
    boundary_slots: tuple[Name, ...] = ()
    public_key_paths: tuple[Text, ...] = ()
    producer_conversions: tuple[SymbolKey, ...] = ()
    serialization_conversions: tuple[SymbolKey, ...] = ()
    namespace_binding: Text
    evidence: Text


class ErrorContract(Record):
    id: Name
    operation: SymbolKey
    model: Literal['exception', 'result', 'exit_status', 'infallible', 'generator']
    error_types: tuple[SymbolKey, ...] = ()
    neutral_mapping: tuple[SymbolKey, ...] = ()
    disposition: Literal['propagate', 'recover', 'translate', 'infallible']
    success_discriminant: Text
    context_exit: SymbolKey | None = None
    exhaustion: SymbolKey | None = None
    support: Literal['abstract_declaration', 'required_implementation']


class Applicability(Record):
    rule: Name
    context: Name
    scope: Annotated[tuple[SymbolKey, ...], Field(min_length=1)]
    required_capabilities: Annotated[tuple[Capability, ...], Field(min_length=1)]
    absence_evidence: tuple[SymbolKey, ...] = ()
    mechanism: Text | None = None
    fixtures: tuple[Input, ...] = ()
    gate_binding: Text | None = None


class ExternalProvenance(Record):
    id: Name
    absolute_path: Text
    sha256: Digest
    distribution: Text
    version: Text
    declaration_hashes: tuple[Input, ...] = ()
    binary_or_generated: Text
    used_symbols: tuple[SymbolKey, ...] = ()
    checked_stubs: tuple[Input, ...] = ()
    summaries: tuple[Name, ...] = ()
