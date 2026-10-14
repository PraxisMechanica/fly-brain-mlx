from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.native_types_envelope import (
    parse_artifacts,
    parse_inputs,
    parse_sites,
)
from tools.architecture.native_types_payload import boolean as boolean
from tools.architecture.native_types_payload import declaration as declaration
from tools.architecture.native_types_payload import indices as indices
from tools.architecture.native_types_payload import integer as integer
from tools.architecture.native_types_payload import optional_integer as optional_integer
from tools.architecture.native_types_payload import optional_string as optional_string
from tools.architecture.native_types_payload import parameter as parameter
from tools.architecture.native_types_payload import string as string
from tools.architecture.native_types_payload import type_node as type_node
from tools.architecture.native_types_payload import values as values
from tools.architecture.native_types_report import NativeTypeReport


def parse_report(value: JsonValue) -> NativeTypeReport:
    item = object_value(value)
    if (
        type(item.get('schema')) is not int
        or item.get('schema') != 1
        or item.get('version') != '1.1.414'
    ):
        raise ValueError('COV002: native type response schema or version changed')
    types = tuple(type_node(node) for node in values(item.get('types')))
    if not types or any(node.id != index for index, node in enumerate(types)):
        raise ValueError('COV002: native type graph identity is incomplete')
    sites = parse_sites(item.get('sites'))
    references = tuple(index for node in types for index in node.references()) + tuple(
        site.type for site in sites
    )
    if not sites or any(index >= len(types) for index in references):
        raise ValueError(
            'COV002: native type graph has absent queried/referenced nodes'
        )
    artifacts = parse_artifacts(item.get('artifacts'))
    inputs = parse_inputs(item.get('inputs'))
    return NativeTypeReport(
        string(item.get('version')),
        artifacts,
        string(item.get('node')),
        string(item.get('python')),
        tuple(sites),
        types,
        inputs,
    )
