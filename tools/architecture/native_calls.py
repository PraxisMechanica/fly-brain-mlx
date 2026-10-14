import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.inventory import Source
from tools.architecture.native_calls_records import ArgumentKind as ArgumentKind
from tools.architecture.native_calls_records import CallKind as CallKind
from tools.architecture.native_calls_records import NativeCall as NativeCall
from tools.architecture.native_calls_records import (
    NativeCallArgument as NativeCallArgument,
)
from tools.architecture.native_calls_records import NativeCallReport as NativeCallReport
from tools.architecture.native_calls_records import NativeCallSource as NativeCallSource
from tools.architecture.native_calls_schema import call_argument as call_argument
from tools.architecture.native_calls_schema import call_record as call_record
from tools.architecture.native_calls_schema import (
    parse_call_report as parse_call_report,
)
from tools.architecture.native_sources import source_inputs
from tools.architecture.native_types import string


def inspect_calls(
    root: Path,
    sources: Sequence[Source],
    package: Path,
    *,
    extra_paths: Sequence[Path] = (),
    stub_path: Path | None = None,
    node: str = 'node',
    bridge: Path | None = None,
) -> NativeCallReport:
    """Inspect all native explicit calls; reject erased or ambiguous static targets."""
    root = root.resolve()
    selected = (bridge or Path(__file__).with_suffix('.mjs')).resolve()
    artifacts = source_inputs(
        selected.parent,
        tuple(
            sorted(
                {selected.name}
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
        raise ValueError('COV002: native call bridge could not complete') from error
    if result.returncode != 0 or 'error' in response:
        raise ValueError(
            string(response.get('error'))
            if 'error' in response
            else 'COV002: native call bridge failed'
        )
    report = parse_call_report(response)
    if report.request_sha256 != hashlib.sha256(request.encode()).hexdigest():
        raise ValueError('COV002: native call request identity changed')
    observed = tuple((source.path, source.sha256) for source in report.sources)
    expected = tuple(
        (str((root / source.path).resolve()), source.sha256) for source in sources
    )
    if observed != expected or report.bridge_sources != tuple(
        (value.path, value.sha256) for value in artifacts
    ):
        raise ValueError('COV002: native call source/artifact discovery differs')
    inputs = dict(report.typing.inputs)
    if any(inputs.get(path) != digest for path, digest in observed):
        raise ValueError('COV002: native call source input was not evaluated')
    for path, digest in (*report.typing.inputs, *report.bridge_sources):
        try:
            actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError(
                'COV002: native call input disappeared: ' + path
            ) from error
        if actual != digest:
            raise ValueError('COV002: native call input changed: ' + path)
    return report
