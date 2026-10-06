import ast
import hashlib
import inspect
from collections.abc import Callable, Mapping
from pathlib import Path
from textwrap import dedent
from typing import cast

import pytest

from tests.quality.support import PROJECT
from tools.architecture import resolution
from tools.architecture.compiler import Compiler, JsonValue
from tools.architecture.coordinates import Coordinates
from tools.architecture.inventory import discover
from tools.architecture.resolution import Resolver, analyze, native_location
from tools.architecture.semantic_index import Document
from tools.architecture.symbols import (
    NATIVE_CAPABILITIES,
    Location,
    Reference,
    SemanticModel,
    Symbol,
)

pytestmark = pytest.mark.unit

CONTRACT = (
    'from typing import Protocol\n'
    'class Port(Protocol):\n'
    '    def read(self) -> int: ...\n'
)
STORE = 'class Store:\n    def read(self) -> int:\n        return 7\n'


def write_sources(root: Path, files: Mapping[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def semantic_model(root: Path, files: Mapping[str, str]) -> SemanticModel:
    write_sources(root, files)
    with Compiler(root, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        return analyze(root, discover(root, tuple(files)), compiler)


def symbol_named(model: SemanticModel, path: str, name: str) -> Symbol:
    matches = [
        symbol
        for symbol in model.symbols
        if symbol.provenance.project_path == path and symbol.name == name
    ]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize(
    'imports,annotation',
    (
        ('from contract import Port\n', 'Port'),
        ('from facade import Reader as Alias\n', 'Alias'),
        (
            'from typing import TYPE_CHECKING\n'
            'if TYPE_CHECKING:\n    from facade import Reader as Alias\n',
            'Alias',
        ),
    ),
)
def test_native_method_identity_survives_alias_reexport_and_type_only_source(
    tmp_path: Path, imports: str, annotation: str
) -> None:
    model = semantic_model(
        tmp_path,
        {
            'contract.py': CONTRACT,
            'facade.py': 'from contract import Port as Reader\n',
            'service.py': imports + f'def execute(port: {annotation}) -> int:\n'
            '    alias = port\n    return alias.read()\n',
        },
    )
    call = next(item for item in model.calls if item.caller.name == 'execute')
    assert (call.target, call.location.line, call.location.column) == (
        symbol_named(model, 'contract.py', 'Port.read'),
        len(imports.splitlines()) + 3,
        17,
    )
    assert any(
        item.kind == 'type' and item.target.name == 'Port' for item in model.references
    )


def test_same_module_callable_aliases_keep_each_native_assignment_link(
    tmp_path: Path,
) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': 'def effect() -> int:\n    return 1\n'
            'alias = effect\nsecond = alias\n'
            'def execute() -> int:\n    return second()\n'
        },
    )
    call = next(item for item in model.calls if item.caller.name == 'execute')
    assert call.target == symbol_named(model, 'service.py', 'effect')
    assert [
        (item.source.name, item.target.name, item.location.line)
        for item in call.aliases
    ] == [('second', 'alias', 4), ('alias', 'effect', 3)]


@pytest.mark.parametrize('annotation', ('Store', 'Port'))
def test_captured_receiver_preserves_native_binding_and_nominal_class(
    tmp_path: Path, annotation: str
) -> None:
    files = {
        'service.py': CONTRACT + STORE + f'def execute(port: {annotation}) -> int:\n'
        '    def inner() -> int:\n        return port.read()\n'
        '    return inner()\n'
    }
    write_sources(tmp_path, files)
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        resolver = Resolver(tmp_path, discover(tmp_path, tuple(files)), compiler)
        model = resolver.analyze()
        capture = next(item for item in model.references if item.captured)
        nominal = resolver.nominal_type(capture.location)
    assert (capture.source.name, capture.target.name, capture.location.line) == (
        'execute.inner',
        'execute.port',
        9,
    )
    assert nominal.target == symbol_named(model, 'service.py', annotation)
    inner_call = next(
        item for item in model.calls if item.caller.name == 'execute.inner'
    )
    assert inner_call.target == symbol_named(model, 'service.py', annotation + '.read')


@pytest.mark.parametrize('annotation', ('Store', 'Port'))
def test_factory_result_receiver_has_a_native_nominal_and_method_surface(
    tmp_path: Path, annotation: str
) -> None:
    files = {
        'service.py': CONTRACT
        + STORE
        + f'def factory() -> {annotation}:\n    return Store()\n'
        'def execute() -> int:\n    returned = factory()\n'
        '    return returned.read()\n'
    }
    write_sources(tmp_path, files)
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        resolver = Resolver(tmp_path, discover(tmp_path, tuple(files)), compiler)
        model = resolver.analyze()
        receiver = next(
            item
            for item in model.references
            if item.source.name == 'execute' and item.target.name == 'execute.returned'
        )
        nominal = resolver.nominal_type(receiver.location)
    assert nominal.target.name == annotation
    assert [
        (item.caller.name, item.target.name, item.kind) for item in model.calls
    ] == [
        ('factory', 'Store', 'constructor'),
        ('execute', 'factory', 'function'),
        ('execute', annotation + '.read', 'function'),
    ]


def test_utf8_ast_offsets_convert_to_native_utf16_coordinates(tmp_path: Path) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': CONTRACT + 'def execute(port: Port) -> int:\n'
            '    text = "🪰é"; return port.read()\n'
        },
    )
    call = model.calls[0]
    assert (call.location.line, call.location.column, call.location.end_column) == (
        5,
        30,
        34,
    )
    assert call.target == symbol_named(model, 'service.py', 'Port.read')
    coordinates = Coordinates(tmp_path / 'line.py', 'é🪰x\n')
    assert coordinates.ast_column(1, 6) == 2
    assert coordinates.utf16_column(1, 2) == 3
    with pytest.raises(ValueError, match='COV002: AST position splits a UTF-8'):
        coordinates.ast_column(1, 3)


def test_builtin_and_library_calls_have_exact_source_provenance(tmp_path: Path) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': 'from pathlib import Path\n'
            'def execute(path: Path) -> int:\n'
            '    return len(path.read_text())\n'
        },
    )
    assert [item.target.name for item in model.calls] == ['len', 'Path.read_text']
    for call in model.calls:
        provenance = call.target.provenance
        assert provenance.project_path is None
        assert provenance.path == call.target.location.path
        assert (
            provenance.sha256
            == hashlib.sha256(Path(provenance.path).read_bytes()).hexdigest()
        )
    assert len(model.symbols) < 20


def test_native_fstring_references_and_calls_keep_inner_expression_coordinates(
    tmp_path: Path,
) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': CONTRACT
            + 'def execute(port: Port) -> str:\n    return f"🪰 {port.read()}"\n'
        },
    )
    call = model.calls[0]
    assert (call.target.name, call.location.line, call.location.column) == (
        'Port.read',
        5,
        22,
    )
    receiver = next(
        item for item in model.references if item.target.name == 'execute.port'
    )
    assert (receiver.location.line, receiver.location.column) == (5, 17)


def test_local_names_and_literals_do_not_become_library_effects(tmp_path: Path) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': 'def len(value: int) -> int:\n    return value\n'
            'def execute() -> int:\n    text = "read_text and Store"\n'
            '    return len(1)\n'
        },
    )
    assert model.calls[0].target == symbol_named(model, 'service.py', 'len')
    assert all(
        item.target.name not in ('read_text', 'Store') for item in model.references
    )


def test_defaults_fields_and_variadic_parameters_have_exact_native_mappings(
    tmp_path: Path,
) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': STORE
            + 'class Service:\n    def __init__(self, port: Store = Store()) -> None:\n        self.port = port\n    def execute(self) -> int:\n        return self.port.read()\ndef run(*args: int, **kwargs: int) -> int:\n    return args[0] + kwargs["a"]\n'
        },
    )
    assert [
        (item.caller.name, item.target.name, item.location.line) for item in model.calls
    ] == [('Service', 'Store', 5), ('Service.execute', 'Store.read', 8)]
    assert any(
        item.target.name == 'Service.__init__.port' and item.target.kind == 'attribute'
        for item in model.references
    )
    assert {
        item.target.name for item in model.references if item.location.line == 10
    } == {'run.args', 'run.kwargs'}


def test_nominal_type_does_not_claim_generic_argument_or_any_type_coverage(
    tmp_path: Path,
) -> None:
    files = {
        'service.py': STORE
        + 'def execute(values: list[Store]) -> int:\n    return len(values)\n'
    }
    write_sources(tmp_path, files)
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        resolver = Resolver(tmp_path, discover(tmp_path, tuple(files)), compiler)
        model = resolver.analyze()
        receiver = next(
            item for item in model.references if item.target.name == 'execute.values'
        )
        nominal = resolver.nominal_type(receiver.location)
        assert nominal.target.name == 'list'
        assert any(
            item.kind == 'type' and item.target.name == 'Store'
            for item in model.references
        )
        with pytest.raises(
            ValueError,
            match='COV002: native semantic adapter lacks required capability: structured_types',
        ):
            model.capabilities.require('structured_types')


def test_native_ambiguous_method_resolution_is_a_located_analysis_failure(
    tmp_path: Path,
) -> None:
    files = {
        'service.py': STORE
        + 'class Other:\n    def read(self) -> int:\n        return 8\n'
        'def execute(port: Store | Other) -> int:\n    return port.read()\n'
    }
    write_sources(tmp_path, files)
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        resolver = Resolver(tmp_path, discover(tmp_path, tuple(files)), compiler)
        site = next(
            item
            for item in next(iter(resolver.documents.values())).sites
            if item.location.line == 8 and item.location.column == 16
        )
        with pytest.raises(
            ValueError, match='COV002: native declaration is ambiguous'
        ) as error:
            resolver.reference(site)
        assert str(error.value).endswith('service.py:8:16')
        with pytest.raises(
            ValueError, match='COV002: native type definition is ambiguous'
        ):
            receiver = next(
                item
                for item in next(iter(resolver.documents.values())).sites
                if item.location.line == 8 and item.location.column == 11
            )
            resolver.nominal_type(receiver.location)


@pytest.mark.parametrize(
    'source,message',
    (
        (
            'def run(port: object) -> int:\n    return port.missing()\n',
            'unresolved source symbol',
        ),
        (
            'def run() -> int:\n    return (lambda: 1)()\n',
            'unsupported computed call target',
        ),
        ('callback = lambda: 1\n', 'lambda scope needs native callable resolution'),
        (
            'class Value: ...\ndef run(value: "Value") -> int:\n    return 1\n',
            'string annotation needs native token resolution',
        ),
        ('from contract import *\n', 'wildcard import has no exact symbol coverage'),
        (
            'def target() -> int:\n    return 1\ndef run(flag: bool) -> int:\n    if flag:\n        alias = target\n    return alias()\n',
            'callable binding is not one unconditional assignment',
        ),
        (
            'def factory():\n    return target\ndef target() -> int:\n    return 1\ndef run() -> int:\n    callback = factory()\n    return callback()\n',
            'callable factory or computed alias needs structured native types',
        ),
    ),
)
def test_unsupported_source_is_not_a_clean_semantic_model(
    tmp_path: Path, source: str, message: str
) -> None:
    with pytest.raises(ValueError, match='COV002:.*' + message):
        semantic_model(tmp_path, {'service.py': source, 'contract.py': CONTRACT})


def test_resolution_cannot_silently_add_an_undiscovered_first_party_file(
    tmp_path: Path,
) -> None:
    write_sources(
        tmp_path,
        {
            'hidden.py': 'class Hidden: ...\n',
            'service.py': 'from hidden import Hidden\n',
        },
    )
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        with pytest.raises(
            ValueError, match='COV002: native resolution reached undiscovered source'
        ):
            analyze(tmp_path, discover(tmp_path, ('service.py',)), compiler)


def test_empty_or_changed_discovery_cannot_start_resolution(tmp_path: Path) -> None:
    source = tmp_path / 'service.py'
    source.write_text('value = 1\n')
    sources = discover(tmp_path, ('service.py',))
    source.write_text('value = 2\n')
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        with pytest.raises(
            ValueError, match='COV002: semantic discovery scope is empty'
        ):
            Resolver(tmp_path, (), compiler)
        with pytest.raises(
            ValueError, match='COV002: semantic discovery changed: service.py'
        ):
            Resolver(tmp_path, sources, compiler)


def test_missing_structured_type_capability_is_native_and_fail_closed(
    tmp_path: Path,
) -> None:
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        assert compiler.capabilities['callHierarchyProvider'] is True
        assert 'experimental' not in compiler.capabilities
        with pytest.raises(
            ValueError,
            match='COV002: compiler error:.*-32601.*Unhandled method pyright/typeInfo',
        ):
            compiler.request('pyright/typeInfo', {})
    for capability in NATIVE_CAPABILITIES.missing:
        with pytest.raises(
            ValueError,
            match='COV002: native semantic adapter lacks required capability: '
            + capability,
        ):
            NATIVE_CAPABILITIES.require(capability)


def test_missing_advertised_native_call_hierarchy_fails_before_analysis(
    tmp_path: Path,
) -> None:
    write_sources(tmp_path, {'service.py': 'value = 1\n'})
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        compiler.capabilities.pop('callHierarchyProvider')
        with pytest.raises(
            ValueError, match='COV002: native compiler lacks callHierarchyProvider'
        ):
            Resolver(tmp_path, discover(tmp_path, ('service.py',)), compiler)


def test_disabling_assignment_guard_accepts_the_same_conditional_callable_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {
        'service.py': 'def target() -> int:\n    return 1\ndef run(flag: bool) -> int:\n    if flag:\n        alias = target\n    return alias()\n'
    }
    write_sources(tmp_path, files)
    tree = ast.parse(dedent(inspect.getsource(Resolver.callable_alias)))

    class DisableAssignmentGuard(ast.NodeTransformer):
        def visit_If(self, node: ast.If) -> ast.AST:
            if any(
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and value.value.startswith(
                    'COV002: callable binding is not one unconditional assignment:'
                )
                for value in ast.walk(node)
            ):
                return ast.copy_location(ast.Pass(), node)
            return node

    tree = ast.fix_missing_locations(DisableAssignmentGuard().visit(tree))
    namespace = dict(Resolver.callable_alias.__globals__)
    exec(compile(tree, '<weakened-callable-assignment>', 'exec'), namespace)
    weakened = cast(
        Callable[
            [Resolver, Location, frozenset[Symbol]],
            tuple[Symbol, tuple[Reference, ...]],
        ],
        namespace['callable_alias'],
    )
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        resolver = Resolver(tmp_path, discover(tmp_path, tuple(files)), compiler)
        with pytest.raises(
            ValueError,
            match='COV002: callable binding is not one unconditional assignment',
        ):
            resolver.analyze()
        monkeypatch.setattr(Resolver, 'callable_alias', weakened)
        assert resolver.analyze().calls[0].target.name == 'target'


def test_disabling_source_guard_reuses_the_same_stale_native_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_sources(
        tmp_path,
        {
            'service.py': 'def target() -> int:\n    return 1\ndef run() -> int:\n    return target()\n'
        },
    )
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        resolver = Resolver(tmp_path, discover(tmp_path, ('service.py',)), compiler)
        document = next(iter(resolver.documents.values()))
        site = next(item for item in document.sites if item.location.line == 4)
        before = resolver.reference(site)
        (tmp_path / 'service.py').write_text(
            'def target() -> int:\n    return 99\ndef run() -> int:\n    return target()\n'
        )
        with pytest.raises(
            ValueError, match='COV002: source changed during semantic analysis'
        ):
            resolver.reference(site)

        def no_verification(self: Document, root: Path) -> None:
            pass

        monkeypatch.setattr(Document, 'verify', no_verification)
        assert resolver.reference(site) == before


def test_disabling_ambiguity_guard_accepts_one_of_the_same_native_method_targets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {
        'service.py': STORE
        + 'class Other:\n    def read(self) -> int:\n        return 8\ndef execute(port: Store | Other) -> int:\n    return port.read()\n'
    }
    write_sources(tmp_path, files)
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        resolver = Resolver(tmp_path, discover(tmp_path, tuple(files)), compiler)
        site = next(
            item
            for item in next(iter(resolver.documents.values())).sites
            if item.location.line == 8 and item.location.column == 16
        )
        with pytest.raises(ValueError, match='COV002: native declaration is ambiguous'):
            resolver.reference(site)

        def first_location(value: JsonValue, label: str) -> Location:
            assert isinstance(value, list) and value
            return native_location(value[0])

        monkeypatch.setattr(resolution, 'unique_location', first_location)
        assert resolver.reference(site).target.name == 'Store.read'


@pytest.mark.parametrize(
    'value',
    (
        None,
        {'uri': 'file://[', 'range': {}},
        {
            'uri': 'file:///tmp/%00.py',
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 0, 'character': 1},
            },
        },
        {'uri': 'https://example.invalid/source.py', 'range': {}},
        {
            'uri': 'file:///tmp/source.py',
            'range': {
                'start': {'line': True, 'character': 0},
                'end': {'line': 0, 'character': 1},
            },
        },
        {
            'uri': 'file:///tmp/source.py',
            'range': {
                'start': {'line': 1, 'character': 0},
                'end': {'line': 0, 'character': 1},
            },
        },
    ),
)
def test_invalid_native_identity_cannot_be_library_provenance(value: JsonValue) -> None:
    with pytest.raises(ValueError, match='COV002:'):
        native_location(value)
