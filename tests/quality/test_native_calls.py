import hashlib
from pathlib import Path

import pytest

from tests.quality.native_call_support import BRIDGE, FUNCTION, OVERLOAD, calls
from tests.quality.native_type_support import PACKAGE


@pytest.mark.parametrize(
    'form', ['ordinary', 'alias', 'import_alias', 'reexport', 'type_only']
)
def test_native_selected_target_survives_source_indirection(
    tmp_path: Path, form: str
) -> None:
    files = {'target.py': FUNCTION}
    entry = {
        'ordinary': 'from target import score\nresult = score(1)\n',
        'alias': 'from target import score\nalias = score\nresult = alias(1)\n',
        'import_alias': 'from target import score as calculate\nresult = calculate(1)\n',
        'reexport': 'from facade import calculate\nresult = calculate(1)\n',
        'type_only': 'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from target import score\ndef run() -> int:\n    return score(1)\n',
    }[form]
    if form == 'reexport':
        files['facade.py'] = 'from target import score as calculate\n'
    files['entry.py'] = entry
    report = calls(tmp_path, files)
    signature = report.signature(report.calls[0])
    assert signature.declaration is not None
    assert signature.declaration.location.path == str(tmp_path / 'target.py')
    assert signature.declaration.location.line == 1
    assert signature.name == 'target.score'
    assert report.typing.types[report.calls[0].result_type].name == 'builtins.int'
    assert {source.path for source in report.sources} == {
        str(tmp_path / name) for name in files
    }


def test_native_capture_and_inferred_factory_keep_declarations_and_nested_calls(
    tmp_path: Path,
) -> None:
    report = calls(
        tmp_path,
        {
            'source.py': FUNCTION + 'def factory():\n    return score\n'
            'def capture() -> int:\n    alias = score\n    def inner() -> int:\n        return alias(2)\n    return inner()\n'
            'result = factory()(3)\n'
        },
    )
    selected = [report.signature(call).name for call in report.calls]
    assert selected == [
        'source.score',
        'source.capture.inner',
        'source.factory',
        'source.score',
    ]
    assert len({call.node_id for call in report.calls}) == 4
    factory, returned = report.calls[-2:]
    assert factory.location.column == returned.location.column
    assert factory.location.end_column < returned.location.end_column
    assert (
        report.signature(returned).declaration
        == report.signature(report.calls[0]).declaration
    )


def test_native_function_construction_callable_value_and_declared_protocol_are_distinct(
    tmp_path: Path,
) -> None:
    report = calls(
        tmp_path,
        {
            'source.py': 'from typing import Protocol\n'
            'class Value:\n    def __init__(self, number: int) -> None:\n        self.number = number\n'
            '    def __call__(self, key: str) -> int:\n        return self.number\n'
            'class Reader(Protocol):\n    def read(self, key: str) -> int: ...\n'
            'class Callback(Protocol):\n    def __call__(self, key: str) -> int: ...\n'
            'def run(reader: Reader, callback: Callback) -> int:\n'
            '    value = Value(3)\n    first = value("x")\n'
            '    second = reader.read("y")\n    return callback("z")\n'
        },
    )
    assert [(call.kind, call.protocol) for call in report.calls] == [
        ('construction', False),
        ('callable_value', False),
        ('function', True),
        ('callable_value', True),
    ]
    assert [report.signature(call).name for call in report.calls] == [
        'source.Value.__init__',
        'source.Value.__call__',
        'source.Reader.read',
        'source.Callback.__call__',
    ]
    assert [
        parameter.name for parameter in report.signature(report.calls[2]).parameters
    ] == ['key']
    receiver = report.calls[2].receiver_type
    assert (
        receiver is not None and report.typing.types[receiver].name == 'source.Reader'
    )


def test_native_overload_selection_uses_actual_declarations_and_result_types(
    tmp_path: Path,
) -> None:
    report = calls(
        tmp_path, {'source.py': OVERLOAD + 'first = choose(1)\nsecond = choose("s")\n'}
    )
    assert [call.overload_index for call in report.calls] == [0, 1]
    assert [
        declaration.location.line
        for call in report.calls
        if (declaration := report.signature(call).declaration) is not None
    ] == [3, 5]
    assert [report.typing.types[call.result_type].name for call in report.calls] == [
        'builtins.str',
        'builtins.int',
    ]
    assert [
        report.typing.types[call.arguments[0].type].literal for call in report.calls
    ] == [1, 's']


def test_alias_of_overload_selects_same_native_variant(tmp_path: Path) -> None:
    report = calls(
        tmp_path, {'source.py': OVERLOAD + 'renamed = choose\nresult = renamed("s")\n'}
    )
    assert report.calls[0].overload_index == 1
    assert report.signature(report.calls[0]).name == 'source.choose'


def test_valid_arguments_and_utf16_ranges_are_source_bound(tmp_path: Path) -> None:
    report = calls(
        tmp_path,
        {
            'source.py': 'def combine(a: int, *, b: str) -> str:\n    return b\nmarker = "💡"; result = combine(2, b="x")\n'
        },
    )
    call = report.calls[0]
    assert (call.location.line, call.location.column, call.location.end_column) == (
        3,
        24,
        41,
    )
    assert [(arg.category, arg.name) for arg in call.arguments] == [
        ('simple', None),
        ('simple', 'b'),
    ]
    assert report.typing.types[call.arguments[1].type].literal == 'x'
    assert all(
        source.sha256 == dict(report.typing.inputs)[source.path]
        for source in report.sources
    )
    assert len(report.request_sha256) == 64
    assert str(BRIDGE) in dict(report.bridge_sources)
    assert str(BRIDGE.with_name('native_calls_api.d.ts')) in dict(report.bridge_sources)


def test_builtin_target_uses_exact_native_stub_identity(tmp_path: Path) -> None:
    report = calls(tmp_path, {'source.py': 'result = len("x")\n'})
    signature = report.signature(report.calls[0])
    declaration = signature.declaration
    assert declaration is not None
    path = PACKAGE.resolve() / 'dist/typeshed-fallback/stdlib/builtins.pyi'
    assert (signature.name, declaration.location.path, declaration.kind) == (
        'builtins.len',
        str(path),
        5,
    )
    assert declaration.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert dict(report.typing.inputs)[str(path)] == declaration.sha256


@pytest.mark.parametrize(
    'category,source',
    [
        (
            'star',
            'def combine(a: int, b: str) -> str:\n    return b\nresult = combine(*(2, "x"))\n',
        ),
        (
            'double_star',
            'from typing import TypedDict\nclass Values(TypedDict):\n    a: int\n    b: str\ndef combine(a: int, b: str) -> str:\n    return b\nvalues: Values = {"a": 2, "b": "x"}\nresult = combine(**values)\n',
        ),
    ],
)
def test_unpack_arguments_keep_native_expression_types(
    tmp_path: Path, category: str, source: str
) -> None:
    report = calls(tmp_path, {'source.py': source})
    argument = report.calls[0].arguments[0]
    assert (argument.category, argument.name) == (category, None)
    assert report.typing.types[argument.type].name == (
        'builtins.tuple' if category == 'star' else 'source.Values'
    )
    assert report.signature(report.calls[0]).name == 'source.combine'
