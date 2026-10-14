from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.native_calls_records import (
    NativeCall,
    NativeCallArgument,
    NativeCallReport,
    NativeCallSource,
)
from tools.architecture.native_calls_validation import validate_call_report
from tools.architecture.native_sources import location
from tools.architecture.native_types import (
    boolean,
    integer,
    optional_integer,
    optional_string,
    parse_report,
    string,
    values,
)
from tools.architecture.native_types_envelope import parse_inputs


def call_argument(value: JsonValue) -> NativeCallArgument:
    item = object_value(value)
    if set(item) != {'node_id', 'location', 'category', 'name', 'type'}:
        raise ValueError('COV002: native call argument schema changed')
    category = string(item.get('category'))
    if category not in ('simple', 'star', 'double_star'):
        raise ValueError('COV002: native call argument category is unsupported')
    return NativeCallArgument(
        integer(item.get('node_id')),
        location(item.get('location')),
        category,
        optional_string(item.get('name')),
        integer(item.get('type')),
    )


def call_record(value: JsonValue) -> NativeCall:
    item = object_value(value)
    if set(item) != {
        'node_id',
        'location',
        'sha256',
        'kind',
        'callee_type',
        'receiver_type',
        'protocol',
        'selected_signature',
        'overload_index',
        'arguments',
        'result_type',
    }:
        raise ValueError('COV002: native explicit call schema changed')
    kind = string(item.get('kind'))
    if kind not in ('function', 'construction', 'callable_value'):
        raise ValueError('COV002: native explicit call kind is unsupported')
    return NativeCall(
        integer(item.get('node_id')),
        location(item.get('location')),
        string(item.get('sha256')),
        kind,
        integer(item.get('callee_type')),
        optional_integer(item.get('receiver_type')),
        boolean(item.get('protocol')),
        integer(item.get('selected_signature')),
        optional_integer(item.get('overload_index')),
        tuple(call_argument(value) for value in values(item.get('arguments'))),
        integer(item.get('result_type')),
    )


def parse_call_report(value: JsonValue) -> NativeCallReport:
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
        raise ValueError('COV002: native call response schema changed')
    typing = parse_report(item)
    sources = tuple(
        NativeCallSource(
            string(object_value(file).get('path')),
            string(object_value(file).get('sha256')),
            tuple(
                call_record(value) for value in values(object_value(file).get('calls'))
            ),
        )
        for file in values(item.get('files'))
    )
    report = NativeCallReport(
        typing,
        sources,
        parse_inputs(item.get('bridge_sources')),
        string(item.get('request_sha256')),
    )
    validate_call_report(report)
    return report
