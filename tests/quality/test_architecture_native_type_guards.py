import ast
import inspect
import json
from collections.abc import Callable
from pathlib import Path
from textwrap import dedent
from typing import cast

import pytest

from tests.quality.native_type_support import (
    BRIDGE,
    PACKAGE,
    STORE,
    query,
    report,
    write,
)
from tests.quality.support import PROJECT, run
from tools.architecture.compiler import JsonValue
from tools.architecture.inventory import Source
from tools.architecture.native_types import (
    NativeTypeReport,
    TypedSite,
    inspect_types,
    parse_report,
)
from tools.architecture.symbols import Location

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    'source,spelling,message',
    (
        (
            'import typing\ndef use():\n    return typing\n',
            'typing',
            'unsupported native type category: 7',
        ),
        (
            'from typing import ParamSpec, Callable\nP = ParamSpec("P")\ndef use(value: Callable[P, int]):\n    return value\n',
            'value',
            'unsupported native ParamSpec, TypeVarTuple or recursive alias',
        ),
    ),
)
def test_unsupported_native_categories_never_become_guessed_types(
    tmp_path: Path, source: str, spelling: str, message: str
) -> None:
    line = 3 if spelling == 'typing' else 3
    with pytest.raises(ValueError, match='COV002: ' + message):
        report(tmp_path, {'service.py': source}, (('service.py', line, spelling),))


def test_empty_missing_tool_and_changed_source_fail_closed(tmp_path: Path) -> None:
    sources = write(tmp_path, {'service.py': 'value = 1\n'})
    location = query(tmp_path, 'service.py', 1, 'value')
    with pytest.raises(ValueError, match='COV002: native source/query scope is empty'):
        inspect_types(tmp_path, (), (location,), PACKAGE)
    with pytest.raises(
        ValueError, match='COV002: native evaluator bridge could not complete'
    ):
        inspect_types(
            tmp_path, sources, (location,), PACKAGE, node=str(tmp_path / 'missing-node')
        )
    with pytest.raises(ValueError, match='COV002: native evaluator bridge is missing'):
        inspect_types(
            tmp_path, sources, (location,), PACKAGE, bridge=tmp_path / 'missing.mjs'
        )
    (tmp_path / 'service.py').write_text('value = 2\n')
    with pytest.raises(ValueError, match='COV002: native discovery source changed:'):
        inspect_types(tmp_path, sources, (location,), PACKAGE)


def test_native_reached_first_party_dependency_must_be_in_discovery(
    tmp_path: Path,
) -> None:
    sources = write(
        tmp_path,
        {
            'store.py': STORE,
            'service.py': 'from store import Store\ndef use(value: Store) -> int:\n    return 1\n',
        },
    )
    with pytest.raises(
        ValueError, match='COV002: native type reached undiscovered first-party source:'
    ):
        inspect_types(
            tmp_path,
            tuple(source for source in sources if source.path == 'service.py'),
            (query(tmp_path, 'service.py', 2, 'value'),),
            PACKAGE,
        )


def test_invalid_source_locations_and_unqueried_parse_failure_fail_closed(
    tmp_path: Path,
) -> None:
    sources = write(tmp_path, {'service.py': 'value = 1\n'})
    for line, column in ((0, 0), (1, 200), (3, 0)):
        with pytest.raises(ValueError, match='COV002:'):
            inspect_types(
                tmp_path,
                sources,
                (Location(str(tmp_path / 'service.py'), line, column, line, column),),
                PACKAGE,
            )
    broken = tmp_path / 'broken.py'
    broken.write_text('def broken(')
    content = broken.read_bytes()
    import hashlib

    with pytest.raises(
        ValueError, match='COV002: native discovered source parse failed:'
    ):
        inspect_types(
            tmp_path,
            (*sources, Source('broken.py', hashlib.sha256(content).hexdigest(), ())),
            (query(tmp_path, 'service.py', 1, 'value'),),
            PACKAGE,
        )


def test_changed_native_bundle_and_version_are_rejected_without_installing(
    tmp_path: Path,
) -> None:
    sources = write(tmp_path, {'service.py': 'value = 1\n'})
    copy = tmp_path / 'native-package'
    copy.mkdir()
    metadata = json.loads((PACKAGE / 'package.json').read_text())
    metadata['version'] = '1.1.415'
    (copy / 'package.json').write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match='COV002: native package version differs'):
        inspect_types(
            tmp_path, sources, (query(tmp_path, 'service.py', 1, 'value'),), copy
        )
    (copy / 'package.json').write_bytes((PACKAGE / 'package.json').read_bytes())
    (copy / 'dist').mkdir()
    (copy / 'dist/pyright.js').write_text('changed native bundle')
    with pytest.raises(
        ValueError, match='COV002: native package artifact changed: dist/pyright.js'
    ):
        inspect_types(
            tmp_path, sources, (query(tmp_path, 'service.py', 1, 'value'),), copy
        )


def test_disabling_precision_rejection_hides_the_same_native_nested_any(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': 'from typing import Any\ndef use(value: list[Any]):\n    return value\n'
        },
        (('service.py', 2, 'value'),),
    )
    with pytest.raises(ValueError, match='COV002: native any type'):
        result.require_precise(result.sites[0])
    tree = ast.parse(dedent(inspect.getsource(NativeTypeReport.require_precise)))

    class RemoveDynamicGuard(ast.NodeTransformer):
        def visit_Raise(self, node: ast.Raise) -> ast.AST:
            return ast.copy_location(ast.Pass(), node)

    tree = ast.fix_missing_locations(RemoveDynamicGuard().visit(tree))
    namespace = dict(NativeTypeReport.require_precise.__globals__)
    exec(compile(tree, '<weakened-native-dynamic-type-guard>', 'exec'), namespace)
    weakened = cast(
        Callable[[NativeTypeReport, TypedSite], None], namespace['require_precise']
    )
    weakened(result, result.sites[0])


def test_disabling_native_protocol_flag_hides_the_same_concrete_collaborator(
    tmp_path: Path,
) -> None:
    files = {
        'service.py': STORE
        + 'def use(value: Store) -> int:\n    return value.read("x")\n'
    }
    sources = write(tmp_path, files)
    location = query(tmp_path, 'service.py', 4, 'value')
    normal = inspect_types(tmp_path, sources, (location,), PACKAGE)
    assert normal.type_at(normal.sites[0]).protocol is False
    for module in BRIDGE.parent.glob('native_types*.mjs'):
        (tmp_path / module.name).write_text(module.read_text())
    projection = tmp_path / 'native_types_class.mjs'
    text = projection.read_text()
    native_flag = 'exporter.types.ClassType.isProtocolClass(value)'
    assert native_flag in text
    projection.write_text(text.replace(native_flag, 'true'))
    modified = tmp_path / BRIDGE.name
    weakened = inspect_types(tmp_path, sources, (location,), PACKAGE, bridge=modified)
    assert weakened.type_at(weakened.sites[0]).protocol is True


def test_checked_javascript_rejects_public_type_defect_and_weakening_hides_it(
    tmp_path: Path,
) -> None:
    compiler = (
        PROJECT / 'node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/bin/tsc'
    )
    declarations = PROJECT / 'tools/architecture/native_types_node.d.ts'
    arguments = [
        'node',
        str(compiler),
        '--allowJs',
        '--checkJs',
        '--noEmit',
        '--strict',
        '--noUncheckedIndexedAccess',
        '--exactOptionalPropertyTypes',
        '--target',
        'ES2022',
        '--module',
        'NodeNext',
        '--moduleResolution',
        'NodeNext',
    ]
    checked = run([*arguments, str(BRIDGE), str(declarations)], PROJECT)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    for module in BRIDGE.parent.glob('native_types*.mjs'):
        (tmp_path / module.name).write_text(module.read_text())
    copied = tmp_path / declarations.name
    copied.write_text(declarations.read_text())
    broken = tmp_path / 'broken.mjs'
    source = BRIDGE.read_text()
    signature = '/** @param {unknown} value @returns {NativeTypes.RecordValue} */\nfunction inspect'
    assert signature in source
    source = source.replace(
        signature, '/** @param {unknown} value @returns {string} */\nfunction inspect'
    )
    broken.write_text(source)
    rejected = run([*arguments, str(broken), str(copied)], tmp_path)
    assert rejected.returncode != 0 and 'TS2322' in rejected.stdout
    broken.write_text(source.replace('// @ts-check\n', ''))
    weakened = run(
        [value for value in arguments if value != '--checkJs']
        + [str(broken), str(copied)],
        tmp_path,
    )
    assert weakened.returncode == 0, weakened.stdout + weakened.stderr


@pytest.mark.parametrize(
    'value',
    (
        None,
        {'schema': 2, 'version': '1.1.414'},
        {'schema': 1, 'version': '1.1.414', 'types': []},
        {
            'schema': 1,
            'version': '1.1.414',
            'types': [{'id': 0, 'category': 'class', 'flags': 2}],
        },
        {
            'schema': 1,
            'version': '1.1.414',
            'types': [{'id': 0, 'category': 'unknown', 'flags': 2, 'guessed': 'safe'}],
        },
    ),
)
def test_missing_or_changed_native_response_schema_fails_closed(
    value: JsonValue,
) -> None:
    with pytest.raises(ValueError, match='COV002:'):
        parse_report(value)
