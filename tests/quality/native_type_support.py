from collections.abc import Mapping, Sequence
from pathlib import Path

from tests.quality.support import PROJECT
from tools.architecture.inventory import Source, discover
from tools.architecture.native_types import NativeTypeReport, inspect_types
from tools.architecture.symbols import Location

PACKAGE = PROJECT / '.venv/lib/python3.10/site-packages/pyright/dist'

BRIDGE = PROJECT / 'tools/architecture/native_types.mjs'

PORT = 'from typing import Protocol\nclass Reader(Protocol):\n    def read(self, key: str) -> int: ...\n'

STORE = 'class Store:\n    def read(self, key: str) -> int:\n        return 7\n'


def write(root: Path, files: Mapping[str, str]) -> tuple[Source, ...]:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return discover(root, tuple(files))


def query(root: Path, name: str, line: int, spelling: str) -> Location:
    path = root / name
    text = path.read_text().splitlines()[line - 1]
    column = len(text[: text.index(spelling)].encode('utf-16-le')) // 2
    return Location(str(path), line, column, line, column + len(spelling))


def report(
    root: Path, files: Mapping[str, str], queries: Sequence[tuple[str, int, str]]
) -> NativeTypeReport:
    sources = write(root, files)
    return inspect_types(
        root, sources, tuple(query(root, *location) for location in queries), PACKAGE
    )
