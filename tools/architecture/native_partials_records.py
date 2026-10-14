from dataclasses import dataclass

from tools.architecture.native_types import NativeDeclaration, NativeTypeReport
from tools.architecture.symbols import Location


@dataclass(frozen=True)
class PartialExpression:
    node_id: int
    native_kind: int
    location: Location
    type: int
    declarations: tuple[NativeDeclaration, ...]
    is_incomplete: bool | None
    type_errors: bool | None


@dataclass(frozen=True)
class PartialCapture:
    argument_node_id: int
    name: str | None
    expression: PartialExpression


@dataclass(frozen=True)
class PartialConstruction:
    """Static native construction evidence; not a runtime target or effect proof."""

    node_id: int
    location: Location
    sha256: str
    callee_type: int
    constructor_signature: int
    wrapped: PartialExpression
    captures: tuple[PartialCapture, ...]
    result_type: int
    residual_signature: int
    is_incomplete: bool | None
    type_errors: bool | None
    callee_is_incomplete: bool | None
    callee_type_errors: bool | None


@dataclass(frozen=True)
class PartialSource:
    path: str
    sha256: str
    constructions: tuple[PartialConstruction, ...]


@dataclass(frozen=True)
class PartialConstructionReport:
    typing: NativeTypeReport
    sources: tuple[PartialSource, ...]
    bridge_sources: tuple[tuple[str, str], ...]
    request_sha256: str

    @property
    def constructions(self) -> tuple[PartialConstruction, ...]:
        return tuple(value for source in self.sources for value in source.constructions)
