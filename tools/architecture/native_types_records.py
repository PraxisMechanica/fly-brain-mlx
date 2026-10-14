from dataclasses import dataclass
from typing import Literal, TypeAlias

from tools.architecture.symbols import Location

Category: TypeAlias = Literal[
    'unbound',
    'unknown',
    'any',
    'never',
    'class',
    'function',
    'overloaded',
    'union',
    'typevar',
]


ParameterKind: TypeAlias = Literal[
    'simple', 'args', 'kwargs', 'positional_separator', 'keyword_separator'
]


@dataclass(frozen=True)
class NativeDeclaration:
    location: Location
    kind: int
    sha256: str


@dataclass(frozen=True)
class NativeParameter:
    name: str | None
    kind: ParameterKind
    flags: int
    type: int | None
    default_type: int | None


@dataclass(frozen=True)
class NativeTupleArgument:
    type: int
    unbounded: bool


@dataclass(frozen=True)
class NativeType:
    id: int
    category: Category
    flags: int
    name: str | None = None
    declaration: NativeDeclaration | None = None
    protocol: bool | None = None
    unspecialized: bool | None = None
    native_source_id: int | None = None
    details_flags: int | None = None
    arguments: tuple[int, ...] = ()
    type_parameters: tuple[int, ...] = ()
    bases: tuple[int, ...] = ()
    tuple_arguments: tuple[NativeTupleArgument, ...] = ()
    members: tuple[int, ...] = ()
    parameters: tuple[NativeParameter, ...] = ()
    return_type: int | None = None
    declared_return: bool | None = None
    gradual_callable: bool | None = None
    overloads: tuple[int, ...] = ()
    implementation: int | None = None
    scope: str | None = None
    variance: int | None = None
    constraints: tuple[int, ...] = ()
    bound: int | None = None
    default_type: int | None = None
    default_explicit: bool | None = None
    ellipsis: bool | None = None
    literal: str | bool | int | float | None = None

    def references(self) -> tuple[int, ...]:
        optional = (
            self.return_type,
            self.implementation,
            self.bound,
            self.default_type,
        )
        return (
            *self.arguments,
            *self.type_parameters,
            *self.bases,
            *self.members,
            *self.overloads,
            *self.constraints,
            *(item.type for item in self.tuple_arguments),
            *(
                index
                for item in self.parameters
                for index in (item.type, item.default_type)
                if index is not None
            ),
            *(index for index in optional if index is not None),
        )


@dataclass(frozen=True)
class TypedSite:
    path: str
    line: int
    column: int
    type: int
    declarations: tuple[NativeDeclaration, ...]
