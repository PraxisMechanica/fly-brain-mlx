from pathlib import Path

import pytest

from tests.quality.native_type_support import PORT, STORE, report

pytestmark = pytest.mark.unit


def test_native_callable_signatures_defaults_and_bound_methods_are_structured(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': 'from typing import Callable\n'
            + STORE
            + 'def use(port: Store, callback: Callable[[int], str]) -> str:\n    return callback(port.read("x"))\ndef operation(value: int, /, *, enabled: bool = True) -> str:\n    return str(value)\n'
        },
        (
            ('service.py', 5, 'callback'),
            ('service.py', 6, 'read'),
            ('service.py', 7, 'operation'),
        ),
    )
    callback, method, operation = (result.type_at(site) for site in result.sites)
    assert callback.category == 'function' and callback.return_type is not None
    assert result.types[callback.return_type].name == 'builtins.str'
    assert [
        result.types[param.type].name
        for param in callback.parameters
        if param.type is not None
    ] == ['builtins.int']
    assert [
        (param.name, result.types[param.type].name)
        for param in method.parameters
        if param.type is not None
    ] == [('key', 'builtins.str')]
    assert [param.kind for param in operation.parameters] == [
        'simple',
        'positional_separator',
        'keyword_separator',
        'simple',
    ]
    assert operation.parameters[-1].default_type is not None
    for site in result.sites:
        result.require_precise(site)


def test_native_overload_signatures_and_implementation_have_independent_identity(
    tmp_path: Path,
) -> None:
    source = 'from typing import overload\n@overload\ndef convert(value: int) -> int: ...\n@overload\ndef convert(value: str) -> str: ...\ndef convert(value: int | str) -> int | str:\n    return value\ndef use() -> int:\n    return convert(1)\n'
    result = report(tmp_path, {'service.py': source}, (('service.py', 9, 'convert'),))
    node = result.type_at(result.sites[0])
    assert (
        node.category == 'overloaded'
        and len(node.overloads) == 2
        and node.implementation is not None
    )
    overloads = [result.types[index] for index in node.overloads]
    assert {
        variant.declaration.location.line
        for variant in overloads
        if variant.declaration is not None
    } == {3, 5}
    assert {
        result.types[variant.return_type].name
        for variant in overloads
        if variant.return_type is not None
    } == {'builtins.int', 'builtins.str'}
    assert result.types[node.implementation].declaration is not None
    result.require_precise(result.sites[0])


def test_native_basic_type_variable_preserves_scope_and_bound(tmp_path: Path) -> None:
    result = report(
        tmp_path,
        {
            'service.py': 'from typing import TypeVar\nT = TypeVar("T", bound=int)\ndef identity(value: T) -> T:\n    return value\n'
        },
        (('service.py', 3, 'identity'),),
    )
    function = result.type_at(result.sites[0])
    assert function.parameters[0].type is not None
    variable = result.types[function.parameters[0].type]
    assert variable.category == 'typevar' and variable.name == 'T'
    assert variable.scope is not None and variable.bound is not None
    assert result.types[variable.bound].name == 'builtins.int'
    result.require_precise(result.sites[0])


def test_native_factory_returned_callable_has_original_signature_and_declaration(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': 'def target(value: int) -> str:\n    return str(value)\ndef factory():\n    return target\nreturned = factory()\n'
        },
        (('service.py', 5, 'returned'),),
    )
    returned = result.type_at(result.sites[0])
    assert returned.category == 'function' and returned.name == 'service.target'
    assert returned.declaration is not None and returned.declaration.location.line == 1
    assert returned.return_type is not None
    assert result.types[returned.return_type].name == 'builtins.str'
    result.require_precise(result.sites[0])


def test_native_never_and_unbound_are_distinct_categories(tmp_path: Path) -> None:
    result = report(
        tmp_path,
        {
            'service.py': 'from typing import NoReturn\ndef stop(value: NoReturn) -> NoReturn:\n    raise RuntimeError()\ndef use():\n    unbound: int\n    return unbound\n'
        },
        (('service.py', 2, 'value'), ('service.py', 6, 'unbound')),
    )
    assert [result.type_at(site).category for site in result.sites] == [
        'never',
        'unbound',
    ]
    result.require_precise(result.sites[0])
    with pytest.raises(ValueError, match='COV002: native unbound type'):
        result.require_precise(result.sites[1])


@pytest.mark.parametrize(
    'annotation,category',
    (
        ('Any', 'any'),
        ('list[Any]', 'any'),
        ('int | Any', 'any'),
        ('Callable[[Any], int]', 'any'),
        ('Callable[[int], Any]', 'any'),
        ('', 'unknown'),
    ),
)
def test_native_nested_any_and_unknown_are_located_analysis_failures(
    tmp_path: Path, annotation: str, category: str
) -> None:
    slot = 'value' + (': ' + annotation if annotation else '')
    result = report(
        tmp_path,
        {
            'service.py': 'from typing import Any, Callable\ndef use('
            + slot
            + '):\n    return value\n'
        },
        (('service.py', 2, 'value'),),
    )
    with pytest.raises(
        ValueError, match='COV002: native ' + category + ' type at .*service.py:2:8'
    ):
        result.require_precise(result.sites[0])


def test_repaired_typed_port_and_close_plain_value_are_precise(tmp_path: Path) -> None:
    result = report(
        tmp_path,
        {
            'service.py': PORT
            + 'def use(port: Reader, value: int) -> int:\n    return port.read(str(value))\n'
        },
        (('service.py', 4, 'port'), ('service.py', 4, 'value')),
    )
    assert [result.type_at(site).protocol for site in result.sites] == [True, False]
    for site in result.sites:
        result.require_precise(site)
