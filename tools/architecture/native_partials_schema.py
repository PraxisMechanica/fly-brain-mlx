from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.native_partials_records import (
    PartialCapture,
    PartialConstruction,
    PartialConstructionReport,
    PartialExpression,
    PartialSource,
)
from tools.architecture.native_partials_validation import validate_partial_report
from tools.architecture.native_sources import location
from tools.architecture.native_types import (
    boolean,
    declaration,
    integer,
    optional_string,
    parse_report,
    string,
    values,
)
from tools.architecture.native_types_envelope import parse_inputs


def optional_flag(value: JsonValue) -> bool | None:
    return None if value is None else boolean(value)


def partial_expression(value: JsonValue) -> PartialExpression:
    item = object_value(value)
    if set(item) != {
        'node_id',
        'native_kind',
        'location',
        'type',
        'declarations',
        'is_incomplete',
        'type_errors',
    }:
        raise ValueError('COV002: native partial expression schema changed')
    declarations = tuple(
        declaration(entry) for entry in values(item.get('declarations'))
    )
    if any(entry is None for entry in declarations):
        raise ValueError('COV002: native partial expression declaration is absent')
    return PartialExpression(
        integer(item.get('node_id')),
        integer(item.get('native_kind')),
        location(item.get('location')),
        integer(item.get('type')),
        tuple(entry for entry in declarations if entry is not None),
        optional_flag(item.get('is_incomplete')),
        optional_flag(item.get('type_errors')),
    )


def partial_capture(value: JsonValue) -> PartialCapture:
    item = object_value(value)
    if set(item) != {'argument_node_id', 'name', 'expression'}:
        raise ValueError('COV002: native partial capture schema changed')
    return PartialCapture(
        integer(item.get('argument_node_id')),
        optional_string(item.get('name')),
        partial_expression(item.get('expression')),
    )


def partial_construction(value: JsonValue) -> PartialConstruction:
    item = object_value(value)
    if set(item) != {
        'node_id',
        'location',
        'sha256',
        'callee_type',
        'constructor_signature',
        'wrapped',
        'captures',
        'result_type',
        'residual_signature',
        'callee_is_incomplete',
        'callee_type_errors',
        'is_incomplete',
        'type_errors',
    }:
        raise ValueError('COV002: native partial construction schema changed')
    return PartialConstruction(
        integer(item.get('node_id')),
        location(item.get('location')),
        string(item.get('sha256')),
        integer(item.get('callee_type')),
        integer(item.get('constructor_signature')),
        partial_expression(item.get('wrapped')),
        tuple(partial_capture(entry) for entry in values(item.get('captures'))),
        integer(item.get('result_type')),
        integer(item.get('residual_signature')),
        optional_flag(item.get('is_incomplete')),
        optional_flag(item.get('type_errors')),
        optional_flag(item.get('callee_is_incomplete')),
        optional_flag(item.get('callee_type_errors')),
    )


def parse_partial_report(value: JsonValue) -> PartialConstructionReport:
    item = object_value(value)
    if set(item) != {
        'schema',
        'version',
        'artifacts',
        'node',
        'python',
        'request_sha256',
        'files',
        'sites',
        'types',
        'inputs',
        'bridge_sources',
    }:
        raise ValueError('COV002: native partial response schema changed')
    sources: list[PartialSource] = []
    for entry in values(item.get('files')):
        file = object_value(entry)
        if set(file) != {'path', 'sha256', 'constructions'}:
            raise ValueError('COV002: native partial file schema changed')
        sources.append(
            PartialSource(
                string(file.get('path')),
                string(file.get('sha256')),
                tuple(
                    partial_construction(value)
                    for value in values(file.get('constructions'))
                ),
            )
        )
    report = PartialConstructionReport(
        parse_report(item),
        tuple(sources),
        parse_inputs(item.get('bridge_sources')),
        string(item.get('request_sha256')),
    )
    validate_partial_report(report)
    return report
