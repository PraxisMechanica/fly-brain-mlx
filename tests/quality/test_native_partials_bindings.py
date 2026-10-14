from pathlib import Path

import pytest

from tests.quality.native_partial_support import DIRECT, SCORE, partials


def test_aliased_reexport_and_type_only_original_are_native_linked(
    tmp_path: Path,
) -> None:
    report = partials(
        tmp_path,
        {
            'exports.py': 'from functools import partial as bind\n' + SCORE,
            'source.py': 'from typing import TYPE_CHECKING\nfrom exports import bind\nif TYPE_CHECKING:\n    from exports import score as operation\ndef wire():\n    return bind(operation, scale=2)\n',
        },
    )
    value = report.constructions[0]
    declaration = value.wrapped.declarations[0]
    assert declaration.location.path == str(tmp_path / 'exports.py')
    assert declaration.location.line == 2
    assert report.typing.types[value.wrapped.type].name == 'exports.score'
    assert (
        report.typing.types[value.constructor_signature].name
        == 'functools.partial.__new__'
    )


def test_bound_method_retains_static_method_declaration(tmp_path: Path) -> None:
    report = partials(
        tmp_path,
        {
            'source.py': 'from functools import partial\nclass Store:\n    def score(self, value: int, *, scale: int) -> int:\n        return value * scale\nstore = Store()\njob = partial(store.score, scale=2)\nresult = job(3)\n'
        },
    )
    value = report.constructions[0]
    assert value.wrapped.native_kind == 35
    assert report.typing.types[value.wrapped.type].name == 'source.Store.score'
    assert value.wrapped.declarations[0].location.line == 3
    assert [
        parameter.name
        for parameter in report.typing.types[value.residual_signature].parameters
    ] == ['value', None, 'scale']


def test_injected_protocol_keeps_parameter_evidence_separate_from_declaration(
    tmp_path: Path,
) -> None:
    report = partials(
        tmp_path,
        {
            'source.py': 'from functools import partial\nfrom typing import Protocol\nclass Score(Protocol):\n    def __call__(self, value: int, *, scale: int) -> int: ...\ndef wire(score: Score):\n    return partial(score, scale=2)\n'
        },
    )
    value = report.constructions[0]
    assert report.typing.types[value.wrapped.type].protocol is True
    assert value.wrapped.declarations[0].kind == 2
    assert value.wrapped.declarations[0].location.line == 5
    assert (
        report.typing.types[value.residual_signature].name
        == 'functools.partial.__call__'
    )


def test_nested_returned_composition_preserves_every_construction(
    tmp_path: Path,
) -> None:
    report = partials(
        tmp_path,
        {
            'source.py': 'from functools import partial\nfrom typing import Protocol\nclass Score(Protocol):\n    def __call__(self, value: int, /) -> int: ...\ndef service(value: int, score: Score) -> int:\n    return score(value)\ndef command(value: int, use_case: Score) -> int:\n    return use_case(value)\ndef wire(score: Score) -> Score:\n    return partial(command, use_case=partial(service, score=score))\n'
        },
    )
    outer, inner = report.constructions
    assert [
        report.typing.types[value.wrapped.type].name for value in report.constructions
    ] == ['source.command', 'source.service']
    assert outer.captures[0].expression.node_id == inner.node_id
    assert outer.captures[0].expression.type == inner.result_type
    assert report.typing.types[inner.captures[0].expression.type].protocol is True


@pytest.mark.parametrize(
    'tail',
    [
        'def wire(flag: bool):\n    origin = first if flag else second\n    return partial(origin)\n',
        'origin = first\njob = partial(origin)\norigin = second\nresult = job(3)\n',
    ],
)
def test_conditional_and_rebound_origins_remain_static_native_facts(
    tmp_path: Path, tail: str
) -> None:
    report = partials(
        tmp_path,
        {
            'source.py': 'from functools import partial\ndef first(value: int) -> int:\n    return value\ndef second(value: int) -> int:\n    return value + 1\n'
            + tail
        },
    )
    value = report.constructions[0]
    assert report.typing.types[value.wrapped.type].name == 'source.first'
    assert all(declaration.kind == 1 for declaration in value.wrapped.declarations)
    assert (
        report.typing.types[value.residual_signature].name
        == 'functools.partial.__call__'
    )


def test_closure_rebinding_exports_callback_identity_without_scanning_dispatch(
    tmp_path: Path,
) -> None:
    report = partials(
        tmp_path,
        {
            'source.py': 'from functools import partial\ndef first(value: int) -> int:\n    return value\ndef second(value: int) -> int:\n    return value + 1\ndef wire():\n    origin = first\n    def callback(value: int) -> int:\n        return origin(value)\n    job = partial(callback)\n    origin = second\n    return job(3)\n'
        },
    )
    assert len(report.constructions) == 1
    assert (
        report.typing.types[report.constructions[0].wrapped.type].name
        == 'source.wire.callback'
    )


def test_keyword_mutation_does_not_turn_capture_into_runtime_value(
    tmp_path: Path,
) -> None:
    report = partials(
        tmp_path,
        {
            'source.py': DIRECT.replace(
                'result = job(3)', 'job.keywords["scale"] = "bad"\nresult = job(3)'
            )
        },
    )
    value = report.constructions[0]
    assert len(report.constructions) == 1
    assert report.typing.types[value.captures[0].expression.type].literal == 2
    assert value.type_errors is None
