from collections.abc import Callable, Mapping
from pathlib import Path

from tests.quality.native_type_support import PACKAGE, write
from tests.quality.support import PROJECT
from tools.architecture.native_calls import (
    NativeCallReport,
    inspect_calls,
)

BRIDGE = PROJECT / 'tools/architecture/native_calls.mjs'
FUNCTION = 'def score(value: int) -> int:\n    return value + 1\n'
OVERLOAD = (
    'from typing import overload\n'
    '@overload\ndef choose(value: int) -> str: ...\n'
    '@overload\ndef choose(value: str) -> int: ...\n'
    'def choose(value: int | str) -> int | str:\n    return value\n'
)


def calls(
    root: Path, files: Mapping[str, str], *, bridge: Path | None = None
) -> NativeCallReport:
    return inspect_calls(root, write(root, files), PACKAGE, bridge=bridge)


def modified_bridge(root: Path, edit: Callable[[str], str]) -> Path:
    root.mkdir()
    for path in BRIDGE.parent.glob('native_*'):
        if path.suffix == '.mjs' or path.name.endswith('.d.ts'):
            (root / path.name).write_bytes(path.read_bytes())
    for module in root.glob('native_calls*.mjs'):
        module.write_text(edit(module.read_text()))
    return root / BRIDGE.name
