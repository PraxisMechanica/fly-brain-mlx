from dataclasses import dataclass

from tools.architecture.symbols import Location


@dataclass(frozen=True)
class NativeInput:
    path: str
    sha256: str


@dataclass(frozen=True)
class NativeTarget:
    name: str
    flags: int
    declarations: tuple[Location, ...]


@dataclass(frozen=True)
class NativeBinding:
    name: str
    kind: str
    location: Location
    target: NativeTarget


@dataclass(frozen=True)
class NativeImport:
    specifier: str
    location: Location
    target: NativeTarget
    type_only: bool


@dataclass(frozen=True)
class NativeExport:
    name: str
    target: NativeTarget


@dataclass(frozen=True)
class NativeSource:
    input: NativeInput
    declarations: tuple[NativeBinding, ...]
    bindings: tuple[NativeBinding, ...]
    imports: tuple[NativeImport, ...]
    exports: tuple[NativeExport, ...]


@dataclass(frozen=True)
class NativeSourceInventory:
    version: str
    files: tuple[NativeSource, ...]
    inputs: tuple[NativeInput, ...]
    artifacts: tuple[tuple[str, str], ...]
