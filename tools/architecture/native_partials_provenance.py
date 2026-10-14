import hashlib
from collections.abc import Sequence
from pathlib import Path
from typing import cast

from tools.architecture.inventory import Source
from tools.architecture.native_partials_records import PartialConstructionReport
from tools.architecture.native_sources import NativeInput
from tools.architecture.native_types import NativeDeclaration


def verify_partial_provenance(
    report: PartialConstructionReport,
    root: Path,
    sources: Sequence[Source],
    package: Path,
    artifacts: Sequence[NativeInput],
    request: str,
) -> None:
    expected = tuple(
        (str((root / source.path).resolve()), source.sha256) for source in sources
    )
    if (
        report.request_sha256 != hashlib.sha256(request.encode()).hexdigest()
        or tuple((source.path, source.sha256) for source in report.sources) != expected
        or report.bridge_sources
        != tuple((value.path, value.sha256) for value in artifacts)
    ):
        raise ValueError(
            'COV002: native partial source/request/artifact discovery differs'
        )
    inputs = dict(report.typing.inputs)
    native_artifacts = tuple(
        (str(package.resolve() / path), digest)
        for path, digest in report.typing.artifacts
    )
    if len(inputs) != len(report.typing.inputs) or {
        path for path, _ in report.typing.artifacts
    } != {
        'package.json',
        'dist/pyright.js',
        'dist/pyright-internal.js',
        'dist/vendor.js',
    }:
        raise ValueError('COV002: native partial input/artifact manifest differs')
    if any(inputs.get(path) != digest for path, digest in expected):
        raise ValueError('COV002: native partial source was not evaluated')
    stub = str(package.resolve() / 'dist/typeshed-fallback/stdlib/functools.pyi')
    for value in report.constructions:
        # The decoder independently proved each library declaration is present.
        declaration = cast(
            NativeDeclaration,
            report.typing.types[value.constructor_signature].declaration,
        )
        if declaration.location.path != stub:
            raise ValueError('COV002: native partial constructor library path differs')
    for path, digest in (
        *report.typing.inputs,
        *report.bridge_sources,
        *native_artifacts,
    ):
        try:
            actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError(
                'COV002: native partial input disappeared: ' + path
            ) from error
        if actual != digest:
            raise ValueError('COV002: native partial input changed: ' + path)
