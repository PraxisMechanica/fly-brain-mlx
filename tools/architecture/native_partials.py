import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.inventory import Source
from tools.architecture.native_partials_provenance import verify_partial_provenance
from tools.architecture.native_partials_records import PartialCapture as PartialCapture
from tools.architecture.native_partials_records import (
    PartialConstruction as PartialConstruction,
)
from tools.architecture.native_partials_records import (
    PartialConstructionReport as PartialConstructionReport,
)
from tools.architecture.native_partials_records import (
    PartialExpression as PartialExpression,
)
from tools.architecture.native_partials_records import PartialSource as PartialSource
from tools.architecture.native_partials_schema import (
    parse_partial_report as parse_partial_report,
)
from tools.architecture.native_sources import source_inputs
from tools.architecture.native_types import string


def inspect_partials(
    root: Path,
    sources: Sequence[Source],
    package: Path,
    *,
    extra_paths: Sequence[Path] = (),
    stub_path: Path | None = None,
    node: str = 'node',
    bridge: Path | None = None,
) -> PartialConstructionReport:
    """Export static native partial constructions without certifying dispatch or purity."""
    root = root.resolve()
    selected = (bridge or Path(__file__).with_suffix('.mjs')).resolve()
    artifacts = source_inputs(
        selected.parent,
        tuple(
            sorted(
                {
                    selected.name,
                    'native_partials_api.d.ts',
                    'native_calls_api.d.ts',
                    'native_types_node.d.ts',
                }
                | {
                    path.name
                    for pattern in ('native_*.mjs', 'native_*.d.ts')
                    for path in selected.parent.glob(pattern)
                }
            )
        ),
    )
    request = json.dumps(
        {
            'schema': 1,
            'root': str(root),
            'package': str(package.resolve()),
            'sources': [
                {'path': str((root / source.path).resolve()), 'sha256': source.sha256}
                for source in sources
            ],
            'bridge_sources': [
                {'path': value.path, 'sha256': value.sha256} for value in artifacts
            ],
            'settings': {
                'extra_paths': [str(path.resolve()) for path in extra_paths],
                'stub_path': None if stub_path is None else str(stub_path.resolve()),
            },
        },
        separators=(',', ':'),
    )
    try:
        result = subprocess.run(
            [node, str(selected)],
            input=request,
            text=True,
            capture_output=True,
            cwd=root,
            timeout=90,
            check=False,
        )
        response = object_value(cast(JsonValue, json.loads(result.stdout)))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise ValueError('COV002: native partial bridge could not complete') from error
    if result.returncode != 0 or 'error' in response:
        raise ValueError(
            string(response.get('error'))
            if 'error' in response
            else 'COV002: native partial bridge failed'
        )
    report = parse_partial_report(response)
    verify_partial_provenance(report, root, sources, package, artifacts, request)
    return report
