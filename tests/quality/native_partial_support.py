from collections.abc import Mapping
from pathlib import Path

from tests.quality.native_call_support import modified_bridge
from tests.quality.native_type_support import PACKAGE, write
from tools.architecture.native_partials import (
    PartialConstructionReport,
    inspect_partials,
)

SCORE = 'def score(value: int, *, scale: int) -> int:\n    return value * scale\n'
DIRECT = (
    'from functools import partial\n'
    + SCORE
    + 'job = partial(score, scale=2)\nresult = job(3)\n'
)


def partials(
    root: Path, files: Mapping[str, str], *, bridge: Path | None = None
) -> PartialConstructionReport:
    return inspect_partials(root, write(root, files), PACKAGE, bridge=bridge)


def changed_bridge(root: Path, module: str, before: str, after: str) -> Path:
    modified_bridge(root, lambda source: source)
    path = root / module
    text = path.read_text()
    assert before in text
    path.write_text(text.replace(before, after))
    return root / 'native_partials.mjs'
