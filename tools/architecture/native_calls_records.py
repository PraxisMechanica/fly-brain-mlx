from dataclasses import dataclass
from typing import Literal

from tools.architecture.native_types import NativeType, NativeTypeReport
from tools.architecture.symbols import Location

CallKind = Literal['function', 'construction', 'callable_value']
ArgumentKind = Literal['simple', 'star', 'double_star']


@dataclass(frozen=True)
class NativeCallArgument:
    node_id: int
    location: Location
    category: ArgumentKind
    name: str | None
    type: int


@dataclass(frozen=True)
class NativeCall:
    node_id: int
    location: Location
    sha256: str
    kind: CallKind
    callee_type: int
    receiver_type: int | None
    protocol: bool
    selected_signature: int
    overload_index: int | None
    arguments: tuple[NativeCallArgument, ...]
    result_type: int


@dataclass(frozen=True)
class NativeCallSource:
    path: str
    sha256: str
    calls: tuple[NativeCall, ...]


@dataclass(frozen=True)
class NativeCallReport:
    typing: NativeTypeReport
    sources: tuple[NativeCallSource, ...]
    bridge_sources: tuple[tuple[str, str], ...]
    request_sha256: str

    @property
    def calls(self) -> tuple[NativeCall, ...]:
        return tuple(call for source in self.sources for call in source.calls)

    def signature(self, call: NativeCall) -> NativeType:
        if call not in self.calls:
            raise ValueError('COV002: native call is outside this report')
        return self.typing.types[call.selected_signature]
