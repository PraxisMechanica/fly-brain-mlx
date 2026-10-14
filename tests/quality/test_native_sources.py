import hashlib
from pathlib import Path

import pytest

from tests.quality.support import PROJECT
from tools.architecture.native_sources import (
    NativeInput,
    inspect_native_sources,
    parse_inventory,
    source_inputs,
)

pytestmark = pytest.mark.unit
PACKAGE = PROJECT / 'node_modules/.pnpm/typescript@5.9.3/node_modules/typescript'
BRIDGE = PROJECT / 'tools/architecture/native_sources.mjs'


def inputs(root: Path, files: dict[str, str]) -> tuple[NativeInput, ...]:
    for name, text in files.items():
        (root / name).write_text(text)
    return source_inputs(root, tuple(files))


def test_native_static_alias_exports_bindings_and_type_only_import_identity(
    tmp_path: Path,
) -> None:
    files = inputs(
        tmp_path,
        {
            'contract.d.ts': 'export interface Reader {read(): number;}\n',
            'source.mjs': 'export function read() {return 1;}\n',
            'facade.mjs': 'export {read as renamed} from "./source.mjs";\n',
            'consumer.mjs': 'import {renamed as call} from "./facade.mjs";\n/** @type {import("./contract.d.ts").Reader} */\nconst reader = {read: call};\nexport {reader};\n',
        },
    )
    result = inspect_native_sources(tmp_path, files, PACKAGE)
    consumer = result.files[-1]
    imported = next(value for value in consumer.bindings if value.name == 'call')
    assert imported.target.name == 'read'
    assert imported.target.declarations[0].path == str(tmp_path / 'source.mjs')
    assert any(value.type_only for value in consumer.imports)
    assert consumer.exports[0].name == 'reader'
    assert {file.input for file in result.files} == set(files)


def test_native_parser_and_checker_reject_repair_and_nearby_string(
    tmp_path: Path,
) -> None:
    files = inputs(
        tmp_path,
        {'source.mjs': 'import {read} from "./missing.mjs";\nexport {read};\n'},
    )
    with pytest.raises(ValueError, match='COV002: native source rejected: .*TS2307'):
        inspect_native_sources(tmp_path, files, PACKAGE)
    repaired = inputs(
        tmp_path, {'source.mjs': 'export const read = "./missing.mjs";\n'}
    )
    result = inspect_native_sources(tmp_path, repaired, PACKAGE)
    assert not result.files[0].imports and result.files[0].exports[0].name == 'read'


@pytest.mark.parametrize(
    'source', ('export function broken( {', '// no populated declaration\n')
)
def test_native_parser_rejects_invalid_and_intentionally_empty_source(
    tmp_path: Path,
    source: str,
) -> None:
    files = inputs(tmp_path, {'source.mjs': source})
    with pytest.raises(
        ValueError, match='COV002: native (source rejected|populated source is empty)'
    ):
        inspect_native_sources(tmp_path, files, PACKAGE)


def test_uninventoried_loaded_source_and_changed_input_are_rejected(
    tmp_path: Path,
) -> None:
    (tmp_path / 'hidden.mjs').write_text('export const read = 1;\n')
    files = inputs(tmp_path, {'source.mjs': 'export {read} from "./hidden.mjs";\n'})
    with pytest.raises(
        ValueError, match='COV002: native parser reached undiscovered source'
    ):
        inspect_native_sources(tmp_path, files, PACKAGE)
    (tmp_path / 'source.mjs').write_text('export const read = 2;\n')
    with pytest.raises(ValueError, match='COV002: native source changed'):
        inspect_native_sources(tmp_path, files, PACKAGE)


def test_missing_empty_escaping_and_tool_inputs_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='COV002: native input scope is empty'):
        source_inputs(tmp_path, ())
    with pytest.raises(ValueError, match='COV002: native input is missing'):
        source_inputs(tmp_path, ('missing.mjs',))
    with pytest.raises(ValueError, match='COV002: native input escapes scope'):
        source_inputs(tmp_path, ('../outside.mjs',))
    files = inputs(tmp_path, {'source.mjs': 'export const read = 1;\n'})
    with pytest.raises(
        ValueError, match='COV002: native source inventory could not complete'
    ):
        inspect_native_sources(tmp_path, files, PACKAGE, node='missing-native-node')


def test_disabling_native_diagnostics_loses_type_contract_rejection(
    tmp_path: Path,
) -> None:
    files = inputs(
        tmp_path,
        {'source.mjs': '/** @type {number} */\nexport const value = "wrong";\n'},
    )
    with pytest.raises(ValueError, match='COV002: native source rejected: .*TS2322'):
        inspect_native_sources(tmp_path, files, PACKAGE)
    for path in BRIDGE.parent.glob('native_*.mjs'):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    weakened = tmp_path / BRIDGE.name
    context = tmp_path / 'native_sources_context.mjs'
    source = context.read_text()
    assert 'ts.getPreEmitDiagnostics(program)' in source
    context.write_text(source.replace('ts.getPreEmitDiagnostics(program)', '[]'))
    result = inspect_native_sources(tmp_path, files, PACKAGE, bridge=weakened)
    assert result.files[0].exports[0].name == 'value'


def test_each_actual_bridge_typing_and_inventory_driver_is_parsed_and_hashed() -> None:
    root = PROJECT
    paths = [
        str(path.relative_to(root))
        for path in sorted((root / 'tools/architecture').glob('native_*.mjs'))
    ]
    paths.append('tools/architecture/native_types_node.d.ts')
    source = source_inputs(root, paths)
    config = NativeInput(
        str(root / 'package.json'),
        hashlib.sha256((root / 'package.json').read_bytes()).hexdigest(),
    )
    result = inspect_native_sources(root, source, PACKAGE, configuration=(config,))
    assert {file.input for file in result.files} == set(source)
    assert all(file.declarations for file in result.files)
    assert str(BRIDGE) in {file.input.path for file in result.files}


def test_disabling_source_scope_guard_accepts_same_uninventoried_dependency(
    tmp_path: Path,
) -> None:
    (tmp_path / 'hidden.mjs').write_text('export const value = 1;\n')
    files = inputs(tmp_path, {'source.mjs': 'export {value} from "./hidden.mjs";\n'})
    with pytest.raises(
        ValueError, match='COV002: native parser reached undiscovered source'
    ):
        inspect_native_sources(tmp_path, files, PACKAGE)
    for path in BRIDGE.parent.glob('native_*.mjs'):
        (tmp_path / path.name).write_bytes(path.read_bytes())
    weakened = tmp_path / BRIDGE.name
    context = tmp_path / 'native_sources_context.mjs'
    source = context.read_text()
    guard = 'if (inside(root, path) && !sources.has(path) && !configuration.has(path))'
    assert guard in source
    context.write_text(source.replace(guard, 'if (false)'))
    result = inspect_native_sources(tmp_path, files, PACKAGE, bridge=weakened)
    assert result.files[0].exports[0].target.declarations[0].path == str(
        tmp_path / 'hidden.mjs'
    )


def test_native_unicode_location_and_namespace_declarations_are_not_text_guesses(
    tmp_path: Path,
) -> None:
    files = inputs(
        tmp_path,
        {
            'source.mjs': 'export const marker = "💡"; export function call() {return marker;}\n',
            'types.d.ts': 'declare namespace Inputs {interface Value {name: string;}}\n',
        },
    )
    result = inspect_native_sources(tmp_path, files, PACKAGE)
    call = next(value for value in result.files[0].declarations if value.name == 'call')
    assert call.location.column == 44
    assert {'Inputs', 'Value', 'name'} <= {
        value.name for value in result.files[1].declarations
    }


def test_changed_native_compiler_package_and_response_schema_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match='COV002: native inventory schema/version changed'
    ):
        parse_inventory({'schema': True, 'version': '5.9.3'})
    files = inputs(tmp_path, {'source.mjs': 'export const value = 1;\n'})
    package = tmp_path / 'compiler'
    package.mkdir()
    (package / 'package.json').write_text('{"version":"unknown"}')
    with pytest.raises(
        ValueError, match='COV002: TypeScript artifact changed: package.json'
    ):
        inspect_native_sources(tmp_path, files, package)
