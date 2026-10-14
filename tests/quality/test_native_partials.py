import hashlib
from dataclasses import fields
from pathlib import Path

import pytest

from tests.quality.native_partial_support import DIRECT, partials
from tests.quality.native_type_support import PACKAGE, write
from tools.architecture.native_calls import inspect_calls
from tools.architecture.native_partials import PartialConstruction
from tools.architecture.native_types import TypedSite


def test_direct_construction_preserves_native_declarations_and_raw_flags(
    tmp_path: Path,
) -> None:
    report = partials(tmp_path, {'source.py': DIRECT})
    value = report.constructions[0]
    types = report.typing.types
    assert (value.location.line, value.location.column, value.node_id) == (4, 6, 33)
    assert value.is_incomplete is None and value.type_errors is None
    assert value.callee_is_incomplete is False and value.callee_type_errors is None
    assert types[value.constructor_signature].name == 'functools.partial.__new__'
    assert types[value.residual_signature].name == 'functools.partial.__call__'
    assert types[value.wrapped.type].name == 'source.score'
    assert value.wrapped.declarations[0].location.line == 2
    assert value.captures[0].name == 'scale'
    assert types[value.captures[0].expression.type].literal == 2
    constructor = types[value.constructor_signature]
    assert constructor.parameters[2].type is not None
    assert types[constructor.parameters[2].type].category == 'any'
    assert constructor.parameters[0].type is not None
    assert types[constructor.parameters[0].type].gradual_callable is True
    residual = types[value.residual_signature]
    assert residual.parameters[-1].default_type is not None
    assert types[residual.parameters[-1].default_type].ellipsis is True
    with pytest.raises(ValueError, match='COV002: native any type'):
        report.typing.require_precise(
            TypedSite(str(tmp_path / 'source.py'), 4, 6, value.residual_signature, ())
        )


def test_positional_capture_removes_bound_parameter_without_inventing_target(
    tmp_path: Path,
) -> None:
    report = partials(
        tmp_path,
        {
            'source.py': 'from functools import partial\ndef score(value: int, scale: int) -> int:\n    return value * scale\njob = partial(score, 3)\nresult = job(2)\n'
        },
    )
    value = report.constructions[0]
    residual = report.typing.types[value.residual_signature]
    assert [parameter.name for parameter in residual.parameters] == ['scale']
    assert value.captures[0].name is None
    assert report.typing.types[value.captures[0].expression.type].literal == 3
    assert not {'runtime_target', 'runtime_targets', 'effects', 'origins'} & {
        field.name for field in fields(PartialConstruction)
    }


def test_capture_order_and_native_utf16_spans_are_exact(tmp_path: Path) -> None:
    text = 'from functools import partial\ndef score(value: int, other: int, *, scale: int) -> int:\n    return (value + other) * scale\nlabel = "🐝"; job = partial(score, 3, scale=2)\n'
    report = partials(tmp_path, {'source.py': text})
    value = report.constructions[0]
    prefix = text.splitlines()[3].split('partial')[0]
    assert value.location.column == len(prefix.encode('utf-16-le')) // 2
    assert [capture.name for capture in value.captures] == [None, 'scale']
    assert [
        report.typing.types[capture.expression.type].literal
        for capture in value.captures
    ] == [3, 2]
    assert [capture.argument_node_id for capture in value.captures] == sorted(
        capture.argument_node_id for capture in value.captures
    )
    assert value.wrapped.location.column == value.location.column + len('partial(')
    assert value.sha256 == hashlib.sha256(text.encode()).hexdigest()


def test_native_any_result_is_preserved_and_existing_precision_still_rejects(
    tmp_path: Path,
) -> None:
    text = 'from functools import partial\nfrom typing import Any\ndef score(value: int) -> Any:\n    return value\njob = partial(score)\n'
    report = partials(tmp_path, {'source.py': text})
    residual = report.typing.types[report.constructions[0].residual_signature]
    assert residual.return_type is not None
    assert report.typing.types[residual.return_type].category == 'any'
    with pytest.raises(ValueError, match='COV002: native any type'):
        report.typing.require_precise(report.typing.sites[-1])
    with pytest.raises(ValueError, match='COV002: native unspecialized generic type'):
        inspect_calls(tmp_path, write(tmp_path, {'source.py': DIRECT}), PACKAGE)
