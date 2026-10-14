from pathlib import Path

import pytest

from tests.quality.native_type_support import PORT, STORE, report

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    'imports',
    (
        'from contract import Reader as Port\n',
        'from facade import Public as Port\n',
        'from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from facade import Public as Port\n',
    ),
)
def test_native_protocol_identity_resolves_import_alias_reexport_and_type_only_surface(
    tmp_path: Path, imports: str
) -> None:
    result = report(
        tmp_path,
        {
            'contract.py': PORT,
            'facade.py': 'from contract import Reader as Public\n',
            'service.py': imports
            + 'def use(port: Port) -> int:\n    return port.read("x")\n',
        },
        (('service.py', len(imports.splitlines()) + 1, 'port'),),
    )
    node = result.type_at(result.sites[0])
    assert (node.category, node.name, node.protocol) == (
        'class',
        'contract.Reader',
        True,
    )
    assert node.declaration is not None
    assert (
        node.declaration.kind,
        node.declaration.location.path,
        node.declaration.location.line,
    ) == (6, str(tmp_path / 'contract.py'), 2)
    result.require_precise(result.sites[0])


def test_native_protocol_flag_distinguishes_concrete_name_and_inheritance(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': PORT
            + 'class MisleadingProtocol:\n    def read(self, key: str) -> int:\n        return 1\nclass Concrete(Reader):\n    def read(self, key: str) -> int:\n        return 2\ndef use(port: Reader, bad: MisleadingProtocol, inherited: Concrete) -> int:\n    return port.read("x")\n'
        },
        (
            ('service.py', 10, 'port'),
            ('service.py', 10, 'bad'),
            ('service.py', 10, 'inherited'),
        ),
    )
    assert [result.type_at(site).protocol for site in result.sites] == [
        True,
        False,
        False,
    ]
    concrete = result.type_at(result.sites[2])
    assert [result.types[index].name for index in concrete.bases] == ['service.Reader']


def test_native_alias_capture_and_factory_inference_keep_actual_class_declaration(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': STORE
            + 'def factory():\n    return Store()\ndef use():\n    captured = factory()\n    def inner():\n        return captured.read("x")\n    return inner()\n'
        },
        (
            ('service.py', 7, 'captured'),
            ('service.py', 9, 'captured'),
            ('service.py', 4, 'factory'),
        ),
    )
    for site in result.sites[:2]:
        node = result.type_at(site)
        assert (node.category, node.name, node.protocol) == (
            'class',
            'service.Store',
            False,
        )
        assert node.declaration is not None and node.declaration.location.line == 1
    factory = result.type_at(result.sites[2])
    assert factory.category == 'function' and factory.declared_return is False
    assert (
        factory.return_type is not None
        and result.types[factory.return_type].name == 'service.Store'
    )


def test_native_generic_union_and_tuple_arguments_are_structured(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': STORE
            + 'def use(many: list[Store], mixed: int | str, fixed: tuple[Store, int]) -> int:\n    return 1\n'
        },
        (
            ('service.py', 4, 'many'),
            ('service.py', 4, 'mixed'),
            ('service.py', 4, 'fixed'),
        ),
    )
    many, mixed, fixed = (result.type_at(site) for site in result.sites)
    assert many.name == 'builtins.list' and [
        result.types[index].name for index in many.arguments
    ] == ['service.Store']
    assert mixed.category == 'union' and {
        result.types[index].name for index in mixed.members
    } == {'builtins.int', 'builtins.str'}
    assert [
        (result.types[arg.type].name, arg.unbounded) for arg in fixed.tuple_arguments
    ] == [('service.Store', False), ('builtins.int', False)]
    for site in result.sites:
        result.require_precise(site)


def test_native_unicode_fstring_method_type_uses_utf16_source_positions(
    tmp_path: Path,
) -> None:
    result = report(
        tmp_path,
        {
            'service.py': PORT
            + 'def use(port: Reader) -> str:\n    return f"🪰 {port.read(\'x\')}"\n'
        },
        (('service.py', 5, 'read'),),
    )
    site = result.sites[0]
    assert site.column == 22
    method = result.type_at(site)
    assert method.name == 'service.Reader.read' and method.declaration is not None
    assert method.declaration.location.line == 3
