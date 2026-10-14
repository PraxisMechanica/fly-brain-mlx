from pathlib import Path

import pytest

from tests.quality.native_type_support import (
    BRIDGE,
    PACKAGE,
    PORT,
    query,
    report,
    write,
)
from tools.architecture.native_types import inspect_types

pytestmark = pytest.mark.unit

VALUE = 'def use(value: int) -> int:\n    return value\n'
BRANDED = (
    'from typing import Generic, NewType, TypeAlias, TypeVar\n'
    'from dependency import Base\n'
    'Rows = NewType("Rows", Base)\n'
    'Wire = NewType("Wire", Base)\n'
    'Space = TypeVar("Space", Rows, Wire)\n'
    'class Box(Generic[Space]):\n    pass\n'
    'RowBox: TypeAlias = Box[Rows]\n'
    'WireBox: TypeAlias = Box[Wire]\n'
    'def use(rows: RowBox, wire: WireBox) -> None:\n    pass\n'
)


def altered_bridge(root: Path, replacement: str) -> Path:
    directory = root / 'bridge'
    directory.mkdir()
    for path in (
        *BRIDGE.parent.glob('native_types*.mjs'),
        BRIDGE.parent / 'native_types_node.d.ts',
    ):
        (directory / path.name).write_text(path.read_text())
    bridge = directory / BRIDGE.name
    text = bridge.read_text()
    assert text.count('verifyImports(source);') == 1
    bridge.write_text(text.replace('verifyImports(source);', replacement))
    return bridge


@pytest.mark.parametrize(
    'prefix,line,column',
    (
        ('import dependency\n', 1, 7),
        ('from dependency import Base\n', 1, 5),
        (
            'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    import dependency\n',
            3,
            11,
        ),
        (
            'import sys\nif sys.version_info >= (3, 10):\n    import dependency\n',
            3,
            11,
        ),
    ),
)
def test_active_native_import_failure_is_located_and_dependency_repair_is_precise(
    tmp_path: Path, prefix: str, line: int, column: int
) -> None:
    files = {'service.py': prefix + VALUE}
    locations = (('service.py', len(prefix.splitlines()) + 1, 'value'),)
    with pytest.raises(
        ValueError,
        match=f'COV002: native unresolved import dependency at .*service.py:{line}:{column}',
    ):
        report(tmp_path, files, locations)
    repaired = report(tmp_path, {**files, 'dependency.py': 'Base = int\n'}, locations)
    assert repaired.type_at(repaired.sites[0]).name == 'builtins.int'
    repaired.require_precise(repaired.sites[0])


def test_partly_resolved_native_prefix_rejects_then_resolves_actual_leaf(
    tmp_path: Path,
) -> None:
    files = {
        'dependency/__init__.py': 'value = 1\n',
        'service.py': 'import dependency.missing\n' + VALUE,
    }
    locations = (('service.py', 2, 'value'),)
    with pytest.raises(
        ValueError,
        match='COV002: native unresolved import dependency.missing at .*service.py:1:7',
    ):
        report(tmp_path, files, locations)
    repaired = report(
        tmp_path, {**files, 'dependency/missing.py': 'value = 1\n'}, locations
    )
    repaired.require_precise(repaired.sites[0])


def test_transitive_import_failure_is_bound_to_the_dependency_source(
    tmp_path: Path,
) -> None:
    files = {
        'service.py': 'import provider\n' + VALUE,
        'provider.py': 'from dependency import Base\n',
    }
    locations = (('service.py', 2, 'value'),)
    with pytest.raises(
        ValueError,
        match='COV002: native unresolved import dependency at .*provider.py:1:5',
    ):
        report(tmp_path, files, locations)
    repaired = report(tmp_path, {**files, 'dependency.py': 'Base = int\n'}, locations)
    repaired.require_precise(repaired.sites[0])


@pytest.mark.parametrize(
    'prefix',
    (
        'if False:\n    import missing_inactive\n',
        'import sys\nif sys.version_info >= (3, 14):\n    import missing_inactive\n',
    ),
)
def test_native_inactive_imports_and_pinned_stub_branches_keep_typed_port_precise(
    tmp_path: Path, prefix: str
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': prefix
            + PORT
            + 'def use(port: Reader) -> int:\n    return port.read("x")\n'
        },
        (('service.py', len(prefix.splitlines()) + 4, 'port'),),
    )
    node = result.type_at(result.sites[0])
    assert (node.category, node.name, node.protocol) == (
        'class',
        'service.Reader',
        True,
    )
    result.require_precise(result.sites[0])


def test_resolved_any_import_stays_observable_then_fails_existing_precision(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': 'from typing import Any\ndef use(value: Any):\n    return value\n'
        },
        (('service.py', 2, 'value'),),
    )
    assert result.type_at(result.sites[0]).category == 'any'
    with pytest.raises(ValueError, match='COV002: native any type at .*service.py:2:8'):
        result.require_precise(result.sites[0])


def test_missing_base_import_cannot_return_falsely_specialized_nominal_types(
    tmp_path: Path,
) -> None:
    locations = (('service.py', 10, 'rows'), ('service.py', 10, 'wire'))
    with pytest.raises(
        ValueError,
        match='COV002: native unresolved import dependency at .*service.py:2:5',
    ):
        report(tmp_path, {'service.py': BRANDED}, locations)
    result = report(
        tmp_path, {'service.py': BRANDED, 'dependency.py': 'Base = int\n'}, locations
    )
    rows, wire = (result.type_at(site) for site in result.sites)
    assert (
        tuple(result.types[index].name for index in rows.arguments),
        tuple(result.types[index].name for index in wire.arguments),
    ) == (('service.Rows',), ('service.Wire',))
    result.require_precise(result.sites[0])
    result.require_precise(result.sites[1])


@pytest.mark.parametrize(
    'replacement,message',
    (
        (
            "Object.defineProperty(context.program, 'analyzerNodeInfoReader', {value: null}); verifyImports(source);",
            'native analyzer reader is not an object',
        ),
        (
            'context.native(1920).getImportInfo = undefined; verifyImports(source);',
            'native import node API or analyzer reader is missing',
        ),
        (
            'context.native(1920).getImportInfo = () => undefined; verifyImports(source);',
            'native import record at .*service.py:1:5 is not an object',
        ),
        (
            "context.native(1920).getImportInfo = () => ({importName: 'typing', resolvedUris: [], isImportFound: 'yes', isPartlyResolved: false}); verifyImports(source);",
            'native import found flag at .*service.py:1:5 is not a boolean',
        ),
        (
            'context.native(1920).isCodeUnreachable = () => 1; verifyImports(source);',
            'native import reachability at .*service.py:1:5 is not a boolean',
        ),
        (
            "context.native(1920).getImportInfo = () => ({importName: 'typing', resolvedUris: [], isImportFound: true, isPartlyResolved: true}); verifyImports(source);",
            'native unresolved import typing at .*service.py:1:5',
        ),
        (
            "const actual = context.program.getSourceFileInfoList(); context.program.getSourceFileInfoList = () => [...actual, {uri: {getFilePath: () => ''}}]; verifyImports(source);",
            'native loaded source path is empty',
        ),
        (
            'const parsed = context.program.getParseResults(context.Uri.file([...sources.keys()][0], context.services)); parsed.parserOutput.importedModules = null; verifyImports(source);',
            'native parsed imports is not an array',
        ),
        (
            'context.native(1920).getImportInfo = () => ({resolvedUris: [], isImportFound: true, isPartlyResolved: false}); verifyImports(source);',
            'native import name at .*service.py:1:5 is not a string',
        ),
        (
            "context.native(1920).getImportInfo = () => ({importName: 'typing', isImportFound: true, isPartlyResolved: false}); verifyImports(source);",
            'native import paths at .*service.py:1:5 is not an array',
        ),
        (
            "context.native(1920).getImportInfo = () => ({importName: 'typing', resolvedUris: ['bad'], isImportFound: true, isPartlyResolved: false}); verifyImports(source);",
            'native import URI at .*service.py:1:5 is not an object',
        ),
        (
            'context.program.getParseResults = () => undefined; verifyImports(source);',
            'native required source parse is missing: .*service.py',
        ),
    ),
)
def test_invalid_native_import_api_record_or_input_never_returns_a_report(
    tmp_path: Path, replacement: str, message: str
) -> None:
    sources = write(tmp_path, {'service.py': 'from typing import Any\n' + VALUE})
    bridge = altered_bridge(tmp_path, replacement)
    with pytest.raises(ValueError, match='COV002: ' + message):
        inspect_types(
            tmp_path,
            sources,
            (query(tmp_path, 'service.py', 2, 'value'),),
            PACKAGE,
            bridge=bridge,
        )


def test_disabling_active_import_guard_restores_same_wrong_native_specialization(
    tmp_path: Path,
) -> None:
    sources = write(tmp_path, {'service.py': BRANDED})
    locations = (
        query(tmp_path, 'service.py', 10, 'rows'),
        query(tmp_path, 'service.py', 10, 'wire'),
    )
    with pytest.raises(ValueError, match='COV002: native unresolved import dependency'):
        inspect_types(tmp_path, sources, locations, PACKAGE)
    bridge = altered_bridge(tmp_path, '')
    weakened = inspect_types(tmp_path, sources, locations, PACKAGE, bridge=bridge)
    assert tuple(
        tuple(weakened.types[index].name for index in weakened.type_at(site).arguments)
        for site in weakened.sites
    ) == (('service.Wire',), ('service.Wire',))
    weakened.require_precise(weakened.sites[0])


@pytest.mark.parametrize(
    'filename,imports',
    (
        ('service.py', 'from package.provider import Reader\n'),
        ('package/service.py', 'from .provider import Reader\n'),
    ),
)
def test_real_namespace_package_without_initializer_preserves_source_identity(
    tmp_path: Path, filename: str, imports: str
) -> None:
    result = report(
        tmp_path,
        {
            'package/provider.py': 'class Reader:\n    pass\n',
            filename: imports + 'def use(value: Reader) -> None:\n    pass\n',
        },
        ((filename, 2, 'value'),),
    )
    node = result.type_at(result.sites[0])
    assert node.declaration is not None
    assert (node.name, node.declaration.location.path) == (
        'package.provider.Reader',
        str(tmp_path / 'package/provider.py'),
    )
    result.require_precise(result.sites[0])
