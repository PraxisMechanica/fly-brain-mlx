import ast
import inspect
from collections.abc import Callable
from pathlib import Path
from textwrap import dedent
from typing import cast

import pytest

from tests.quality.support import PROJECT
from tools.architecture.compiler import (
    Compiler,
    JsonValue,
    content_length,
    object_value,
)

pytestmark = pytest.mark.unit


def test_missing_native_resolver_is_an_analysis_failure(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError, match='COV002: native compiler language server is missing'
    ):
        with Compiler(tmp_path, tmp_path / 'missing'):
            pass


def test_native_compiler_resolves_an_aliased_consumer_port_method(
    tmp_path: Path,
) -> None:
    contract = tmp_path / 'contract.py'
    contract.write_text(
        'from typing import Protocol\n'
        'class Port(Protocol):\n'
        '    def read(self) -> int: ...\n'
    )
    service = tmp_path / 'service.py'
    service.write_text(
        'from contract import Port\n'
        'def execute(port: Port) -> int:\n'
        '    alias = port\n'
        '    return alias.read()\n'
    )
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        evidence = compiler.resolve(service, 4, 17)
    definitions = evidence['definitions']
    assert isinstance(definitions, list) and definitions
    target = object_value(definitions[0])
    assert target['uri'] == contract.as_uri()
    location = object_value(object_value(target['range'])['start'])
    assert location['line'] == 2
    signature = object_value(evidence['signature'])
    assert '() -> int' in str(object_value(signature['contents'])['value'])


def test_compiler_nonobject_response_is_not_a_resolved_symbol() -> None:
    with pytest.raises(ValueError, match='COV002: compiler response is not an object'):
        object_value(None)


@pytest.mark.parametrize(
    'header',
    (
        b'',
        b'Content-Type: application/json',
        b'Content-Length: -1',
        b'Content-Length: 0',
        b'Content-Length: nope',
        b'Content-Length 10',
        b'Content-Length: 2\r\nContent-Length: 3',
    ),
)
def test_invalid_native_message_lengths_fail_analysis(header: bytes) -> None:
    with pytest.raises(
        ValueError, match='COV002: compiler response framing is invalid'
    ):
        content_length(header)
    assert content_length(b'Content-Type: application/json\r\nContent-Length: 2') == 2


def test_buffered_native_responses_keep_their_individual_frames(tmp_path: Path) -> None:
    compiler = Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver')
    compiler.buffer.extend(b'Content-Length: 2\r\n\r\n{}Content-Length: 2\r\n\r\n{}')
    assert compiler.receive() == {}
    assert compiler.receive() == {}
    assert not compiler.buffer


def test_malformed_native_json_is_not_symbol_evidence(tmp_path: Path) -> None:
    compiler = Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver')
    compiler.buffer.extend(b'Content-Length: 1\r\n\r\n{')
    with pytest.raises(ValueError, match='COV002: compiler response JSON is invalid'):
        compiler.receive()


def test_present_but_nonexecutable_native_tool_fails_analysis(tmp_path: Path) -> None:
    executable = tmp_path / 'not-executable'
    executable.write_text('not a compiler')
    executable.chmod(0o600)
    with pytest.raises(ValueError, match='COV002: native compiler could not start'):
        with Compiler(tmp_path, executable):
            pass


def test_native_unknown_method_fails_instead_of_returning_empty_evidence(
    tmp_path: Path,
) -> None:
    service = tmp_path / 'service.py'
    service.write_text('def execute(port: object) -> int:\n    return port.missing()\n')
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        with pytest.raises(
            ValueError, match='COV002: unresolved source symbol'
        ) as error:
            compiler.resolve(service, 2, 16)
    assert str(error.value).endswith('service.py:2:16')


def test_native_resolution_cannot_reuse_a_document_after_its_source_changes(
    tmp_path: Path,
) -> None:
    service = tmp_path / 'service.py'
    service.write_text('def value() -> int:\n    return 1\nvalue()\n')
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        compiler.resolve(service, 3, 1)
        service.write_text('def value() -> str:\n    return "changed"\nvalue()\n')
        with pytest.raises(
            ValueError, match='COV002: source changed during compiler analysis'
        ):
            compiler.resolve(service, 3, 1)


@pytest.mark.parametrize(
    'imports,annotation',
    (
        ('from facade import Reader\n', 'Reader'),
        ('from facade import Reader as Alias\n', 'Alias'),
        (
            'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from facade import Reader\n',
            'Reader',
        ),
    ),
)
def test_native_resolution_follows_reexports_aliases_and_type_only_ports(
    tmp_path: Path,
    imports: str,
    annotation: str,
) -> None:
    contract = tmp_path / 'contract.py'
    contract.write_text(
        'from typing import Protocol\nclass Port(Protocol):\n    def read(self) -> int: ...\n'
    )
    (tmp_path / 'facade.py').write_text('from contract import Port as Reader\n')
    service = tmp_path / 'service.py'
    service.write_text(
        imports
        + f'def execute(port: {annotation}) -> int:\n    alias = port\n    return alias.read()\n'
    )
    line = len(imports.splitlines()) + 3
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        evidence = compiler.resolve(service, line, 17)
    definitions = evidence['definitions']
    assert isinstance(definitions, list) and definitions
    assert object_value(definitions[0])['uri'] == contract.as_uri()


def test_disabling_unresolved_symbol_rejection_hides_the_same_native_failure(
    tmp_path: Path,
) -> None:
    service = tmp_path / 'service.py'
    service.write_text('def execute(port: object) -> int:\n    return port.missing()\n')
    tree = ast.parse(dedent(inspect.getsource(Compiler.resolve)))

    class DisableResolutionGuard(ast.NodeTransformer):
        def visit_Raise(self, node: ast.Raise) -> ast.AST:
            if any(
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and value.value.startswith('COV002: unresolved source symbol:')
                for value in ast.walk(node)
            ):
                return ast.copy_location(ast.Pass(), node)
            return node

    tree = ast.fix_missing_locations(DisableResolutionGuard().visit(tree))
    namespace = dict(Compiler.resolve.__globals__)
    exec(compile(tree, '<weakened-native-resolution>', 'exec'), namespace)
    weakened = cast(
        Callable[[Compiler, Path, int, int], dict[str, JsonValue]], namespace['resolve']
    )
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        with pytest.raises(ValueError, match='COV002: unresolved source symbol'):
            compiler.resolve(service, 2, 16)
        assert not weakened(compiler, service, 2, 16)['definitions']


def test_disabling_invalid_length_rejection_accepts_the_same_broken_frame() -> None:
    tree = ast.parse(inspect.getsource(content_length))

    class DisableLengthGuard(ast.NodeTransformer):
        def visit_If(self, node: ast.If) -> ast.AST:
            if any(
                isinstance(value, ast.Constant) and value.value == 'empty response'
                for value in ast.walk(node)
            ):
                return ast.copy_location(ast.Pass(), node)
            return node

    tree = ast.fix_missing_locations(DisableLengthGuard().visit(tree))
    namespace = dict(content_length.__globals__)
    exec(compile(tree, '<weakened-frame-length>', 'exec'), namespace)
    weakened = cast(Callable[[bytes], int], namespace['content_length'])
    broken = b'Content-Length: -1'
    with pytest.raises(
        ValueError, match='COV002: compiler response framing is invalid'
    ):
        content_length(broken)
    assert weakened(broken) == -1
