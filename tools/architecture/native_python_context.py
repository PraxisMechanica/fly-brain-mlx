"""Native configuration/source observations; no declaration or type verdict."""

import hashlib
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError

from tools.architecture.inventory import Source, discover
from tools.architecture.native_python_context_records import (
    ContextEnvironment as ContextEnvironment,
)
from tools.architecture.native_python_context_records import (
    ContextInput as ContextInput,
)
from tools.architecture.native_python_context_records import (
    ContextOrigin as ContextOrigin,
)
from tools.architecture.native_python_context_records import (
    NativePythonContextReport as NativePythonContextReport,
)
from tools.architecture.native_sources import NativeInput, source_inputs


def inspect_python_context(
    root: Path,
    sources: Sequence[Source],
    package: Path,
    *,
    scopes: Sequence[str],
    configuration: Sequence[NativeInput],
    node: str = 'node',
    bridge: Path | None = None,
) -> NativePythonContextReport:
    root = root.resolve()
    expected = tuple((source.path, source.sha256) for source in sources)
    if expected != tuple(
        (source.path, source.sha256) for source in discover(root, scopes)
    ):
        raise ValueError('COV002: independent context discovery differs')
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
    parent = root / 'logs/python-context'
    parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=parent, prefix='native-') as temporary:
        request = json.dumps(
            {
                'schema': 1,
                'root': str(root),
                'package': str(package.resolve()),
                'temporary': temporary,
                'sources': [
                    {
                        'path': str((root / source.path).resolve()),
                        'sha256': source.sha256,
                    }
                    for source in sources
                ],
                'configuration': [
                    {'path': value.path, 'sha256': value.sha256}
                    for value in configuration
                ],
                'bridge_sources': [
                    {'path': value.path, 'sha256': value.sha256} for value in artifacts
                ],
            },
            separators=(',', ':'),
        )
        try:
            result = subprocess.run(
                [node, str(selected)],
                input=request,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=90,
                check=False,
            )
            if result.returncode:
                raise ValueError(
                    'COV002: native context rejected: ' + result.stdout + result.stderr
                )
            report = NativePythonContextReport.model_validate_json(result.stdout)
        except (OSError, subprocess.TimeoutExpired, ValidationError) as error:
            raise ValueError('COV002: native context could not complete') from error
    required = tuple(
        (str((root / source.path).resolve()), source.sha256) for source in sources
    )
    if (
        report.request_sha256 != hashlib.sha256(request.encode()).hexdigest()
        or tuple((entry.path, entry.sha256) for entry in report.sources) != required
        or tuple((entry.path, entry.sha256) for entry in report.bridge_sources)
        != tuple((entry.path, entry.sha256) for entry in artifacts)
        or tuple((entry.path, entry.sha256) for entry in report.configuration)
        != tuple((entry.path, entry.sha256) for entry in configuration)
        or set(report.tracked) | set(report.stub_inputs)
        != {path for path, _ in required}
        or {entry.path for entry in report.compiler_artifacts}
        != {
            str(package.resolve() / path)
            for path in (
                'package.json',
                'dist/pyright.js',
                'dist/pyright-internal.js',
                'dist/vendor.js',
            )
        }
        or not {report.primary_config, *report.tracked}
        <= {entry.path for entry in report.read_inputs}
        or len(report.environments) != len(report.tracked)
    ):
        raise ValueError('COV002: native context discovery/request provenance differs')
    try:
        for entry in (
            *report.sources,
            *report.configuration,
            *report.loaded,
            *report.read_inputs,
            *report.bridge_sources,
            *report.compiler_artifacts,
        ):
            if (
                hashlib.sha256(Path(entry.path).read_bytes()).hexdigest()
                != entry.sha256
            ):
                raise ValueError('COV002: native context input changed: ' + entry.path)
    except OSError as error:
        raise ValueError('COV002: native context input disappeared') from error
    if expected != tuple(
        (source.path, source.sha256) for source in discover(root, scopes)
    ):
        raise ValueError('COV002: independent context discovery changed')
    return report
