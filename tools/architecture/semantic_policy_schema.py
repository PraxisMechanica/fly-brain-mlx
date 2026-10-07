import json
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, ValidationError, field_validator

from .semantic_policy_records import (
    Applicability,
    Binding,
    Constructor,
    Context,
    Effect,
    ErrorContract,
    ExternalProvenance,
    Identifier,
    Name,
    Owner,
    Placement,
    Port,
    PublicContract,
    Record,
    Resource,
    Slot,
    UseCase,
)

CATALOG = (
    'OWN001',
    'OWN002',
    'OWN003',
    'OWN004',
    'OWN005',
    'OWN006',
    'DEP001',
    'DEP002',
    'DEP003',
    'DEP004',
    'DI001',
    'DI002',
    'DI003',
    'DI004',
    'ROLE001',
    'ROLE002',
    'ROLE003',
    'ROLE004',
    'ROLE005',
    'ROLE006',
    'ROLE007',
    'STATE001',
    'STATE002',
    'STATE003',
    'ISP001',
    'OCP001',
    'LSP001',
    'VALUE001',
    'COMP001',
    'ERR001',
    'TYPE001',
    'CODE001',
    'STYLE001',
    'COV001',
    'COV002',
    'COV003',
    'COV004',
)


class SemanticPolicyDocument(Record):
    version: Literal[2]
    owners: Annotated[dict[Name, Owner], Field(min_length=1)]
    contexts: Annotated[tuple[Context, ...], Field(min_length=1)]
    placement: Annotated[tuple[Placement, ...], Field(min_length=1)]
    semantic_bindings: Annotated[tuple[Binding, ...], Field(min_length=1)]
    consumer_slots: tuple[Slot, ...]
    ports: tuple[Port, ...]
    public_contracts: tuple[PublicContract, ...]
    effects: tuple[Effect, ...]
    constructors_and_factories: tuple[Constructor, ...]
    use_cases_and_handlers: tuple[UseCase, ...]
    resources_and_storage: tuple[Resource, ...]
    identifiers: tuple[Identifier, ...]
    errors: tuple[ErrorContract, ...]
    applicability: Annotated[tuple[Applicability, ...], Field(min_length=1)]
    external_provenance: Annotated[tuple[ExternalProvenance, ...], Field(min_length=1)]

    @field_validator('version', mode='before')
    @classmethod
    def exact_version(cls, value: object) -> object:
        if type(value) is not int or value != 2:
            raise ValueError('COV002: semantic policy requires integer version 2')
        return value


def unique_keys(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError('COV002: duplicate semantic policy key: ' + key)
        result[key] = value
    return result


def load_semantic_policy(path: Path) -> SemanticPolicyDocument:
    try:
        content = path.read_text()
        json.loads(content, object_pairs_hook=unique_keys)
        return SemanticPolicyDocument.model_validate_json(content)
    except (OSError, UnicodeError, ValidationError, json.JSONDecodeError) as error:
        raise ValueError(
            'COV002: semantic policy could not be loaded: ' + str(error)
        ) from error


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError('COV002: semantic policy ' + message)


def unique(items: Sequence[str], label: str) -> None:
    require(len(items) == len(set(items)), 'duplicate ' + label)
