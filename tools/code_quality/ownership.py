"""Protect reviewed scientific source bytes without policing ordinary structure."""

import argparse
import hashlib
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

POLICY = 'tools/code_quality/scientific_sources.json'
PROTECTED = (
    'src/fly_brain/qualification/adapters/brian_reference.py',
    'src/fly_brain/qualification/adapters/torch_reference.py',
    'src/fly_brain/qualification/reference_parameters.py',
    'tests/support/legacy_mlx_ledger.py',
    'tests/support/legacy_mlx_observer.py',
)


class SourceIdentity(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    kind: Literal['reference_source', 'historical_source']
    sha256: Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
    commit: Annotated[str, Field(pattern=r'^[a-f0-9]{40}$')]
    origin: Annotated[str, Field(min_length=1)]


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    version: Literal[1]
    sources: dict[str, SourceIdentity]


def review(root: Path) -> tuple[str, ...]:
    manifest = SourceManifest.model_validate_json((root / POLICY).read_text())
    if set(manifest.sources) != set(PROTECTED):
        raise ValueError('COV002: protected scientific source inventory changed')
    for path in manifest.sources:
        source = root / path
        if source.resolve() != source or not source.is_file():
            raise ValueError('COV002: protected source is missing or linked: ' + path)
    changed = tuple(
        path
        for path, identity in manifest.sources.items()
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != identity.sha256
    )
    print(
        f'Source integrity: {len(manifest.sources)} protected scientific sources checked.'
    )
    return changed


def main(arguments: Sequence[str] | None = None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(arguments)
    try:
        changed = review(Path.cwd().resolve())
    except (OSError, ValueError) as error:
        print('ANALYSIS FAILED: ' + str(error), file=sys.stderr)
        return 2
    for path in changed:
        print(
            f'COV001: {path}:1: Protected scientific source hash changed',
            file=sys.stderr,
        )
    return int(bool(changed))


if __name__ == '__main__':
    sys.exit(main())
