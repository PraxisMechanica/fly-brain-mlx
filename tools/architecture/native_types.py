import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.inventory import Source
from tools.architecture.native_types_records import Category as Category
from tools.architecture.native_types_records import (
    NativeDeclaration as NativeDeclaration,
)
from tools.architecture.native_types_records import NativeParameter as NativeParameter
from tools.architecture.native_types_records import (
    NativeTupleArgument as NativeTupleArgument,
)
from tools.architecture.native_types_records import NativeType as NativeType
from tools.architecture.native_types_records import ParameterKind as ParameterKind
from tools.architecture.native_types_records import TypedSite as TypedSite
from tools.architecture.native_types_report import NativeTypeReport as NativeTypeReport
from tools.architecture.native_types_schema import boolean as boolean
from tools.architecture.native_types_schema import declaration as declaration
from tools.architecture.native_types_schema import indices as indices
from tools.architecture.native_types_schema import integer as integer
from tools.architecture.native_types_schema import optional_integer as optional_integer
from tools.architecture.native_types_schema import optional_string as optional_string
from tools.architecture.native_types_schema import parameter as parameter
from tools.architecture.native_types_schema import parse_report as parse_report
from tools.architecture.native_types_schema import string as string
from tools.architecture.native_types_schema import type_node as type_node
from tools.architecture.native_types_schema import values as values
from tools.architecture.symbols import Location


def inspect_types(
    root: Path,
    sources: Sequence[Source],
    queries: Sequence[Location],
    package: Path,
    *,
    extra_paths: Sequence[Path] = (),
    stub_path: Path | None = None,
    node: str = 'node',
    bridge: Path | None = None,
) -> NativeTypeReport:
    root = root.resolve()
    if not sources or not queries:
        raise ValueError('COV002: native source/query scope is empty')
    request = {
        'schema': 1,
        'root': str(root),
        'package': str(package.resolve()),
        'sources': [
            {'path': str((root / source.path).resolve()), 'sha256': source.sha256}
            for source in sources
        ],
        'queries': [
            {
                'path': str(Path(query.path).resolve()),
                'line': query.line,
                'column': query.column,
            }
            for query in queries
        ],
        'settings': {
            'extra_paths': [str(path.resolve()) for path in extra_paths],
            'stub_path': None if stub_path is None else str(stub_path.resolve()),
        },
    }
    selected = bridge or Path(__file__).with_suffix('.mjs')
    if not selected.is_file():
        raise ValueError('COV002: native evaluator bridge is missing')
    try:
        result = subprocess.run(
            [node, str(selected)],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            cwd=root,
            timeout=90,
            check=False,
        )
        value = cast(JsonValue, json.loads(result.stdout))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise ValueError(
            'COV002: native evaluator bridge could not complete'
        ) from error
    response = object_value(value)
    if result.returncode != 0 or 'error' in response:
        raise ValueError(
            string(response.get('error'))
            if 'error' in response
            else 'COV002: native evaluator bridge failed'
        )
    report = parse_report(response)
    expected = tuple(
        (str(Path(query.path).resolve()), query.line, query.column) for query in queries
    )
    observed = tuple((site.path, site.line, site.column) for site in report.sites)
    if observed != expected:
        raise ValueError('COV002: native type query discovery differs from request')
    actual: Mapping[str, str] = dict(report.inputs)
    for path, expected_hash in actual.items():
        try:
            digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError(
                'COV002: native type input disappeared: ' + path
            ) from error
        if digest != expected_hash:
            raise ValueError('COV002: native type input changed: ' + path)
    for source in sources:
        path = (root / source.path).resolve()
        if (
            actual.get(str(path)) != source.sha256
            or hashlib.sha256(path.read_bytes()).hexdigest() != source.sha256
        ):
            raise ValueError(
                'COV002: native type source provenance changed: ' + source.path
            )
    return report
