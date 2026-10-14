from dataclasses import replace

from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.native_types_records import (
    NativeDeclaration,
    NativeParameter,
    NativeTupleArgument,
    NativeType,
)
from tools.architecture.symbols import Location


def integer(value: JsonValue) -> int:
    if type(value) is not int or value < 0:
        raise ValueError('COV002: native type schema requires a nonnegative integer')
    return value


def string(value: JsonValue) -> str:
    if not isinstance(value, str):
        raise ValueError('COV002: native type schema requires a string')
    return value


def boolean(value: JsonValue) -> bool:
    if type(value) is not bool:
        raise ValueError('COV002: native type schema requires a boolean')
    return value


def values(value: JsonValue) -> list[JsonValue]:
    if not isinstance(value, list):
        raise ValueError('COV002: native type schema requires an array')
    return value


def optional_integer(value: JsonValue) -> int | None:
    return None if value is None else integer(value)


def optional_string(value: JsonValue) -> str | None:
    return None if value is None else string(value)


def declaration(value: JsonValue) -> NativeDeclaration | None:
    if value is None:
        return None
    item = object_value(value)
    location = Location(
        string(item.get('path')),
        integer(item.get('line')),
        integer(item.get('column')),
        integer(item.get('end_line')),
        integer(item.get('end_column')),
    )
    if location.line == 0 or (location.end_line, location.end_column) < (
        location.line,
        location.column,
    ):
        raise ValueError('COV002: native declaration range is invalid')
    return NativeDeclaration(
        location, integer(item.get('kind')), string(item.get('sha256'))
    )


def parameter(value: JsonValue) -> NativeParameter:
    item = object_value(value)
    if set(item) != {'name', 'kind', 'flags', 'type', 'default_type'}:
        raise ValueError('COV002: native parameter schema changed')
    kind = string(item.get('kind'))
    if kind not in (
        'simple',
        'args',
        'kwargs',
        'positional_separator',
        'keyword_separator',
    ):
        raise ValueError('COV002: native parameter kind is unsupported')
    type_index = optional_integer(item.get('type'))
    if (type_index is None) != kind.endswith('_separator'):
        raise ValueError('COV002: native parameter type or separator is missing')
    return NativeParameter(
        optional_string(item.get('name')),
        kind,
        integer(item.get('flags')),
        type_index,
        optional_integer(item.get('default_type')),
    )


def indices(value: JsonValue) -> tuple[int, ...]:
    return tuple(integer(item) for item in values(value))


def type_node(value: JsonValue) -> NativeType:
    item = object_value(value)
    category = string(item.get('category'))
    if category not in (
        'unbound',
        'unknown',
        'any',
        'never',
        'class',
        'function',
        'overloaded',
        'union',
        'typevar',
    ):
        raise ValueError('COV002: native type category is unsupported: ' + category)
    fields = {
        'class': (
            'name',
            'native_source_id',
            'details_flags',
            'declaration',
            'protocol',
            'unspecialized',
            'arguments',
            'type_parameters',
            'bases',
            'tuple_arguments',
        ),
        'function': (
            'name',
            'details_flags',
            'declaration',
            'parameters',
            'type_parameters',
            'gradual_callable',
            'return_type',
            'declared_return',
        ),
        'overloaded': ('overloads', 'implementation'),
        'union': ('members',),
        'typevar': (
            'name',
            'scope',
            'variance',
            'constraints',
            'bound',
            'default_type',
            'default_explicit',
        ),
        'any': ('ellipsis',),
    }
    required = {'id', 'category', 'flags', *fields.get(category, ())}
    allowed: set[str] = required | ({'literal'} if category == 'class' else set())
    if not required.issubset(item) or not item.keys() <= allowed:
        raise ValueError('COV002: native type record schema changed: ' + category)
    base = NativeType(integer(item.get('id')), category, integer(item.get('flags')))
    if category == 'class':
        tuple_arguments = tuple(
            NativeTupleArgument(
                integer(object_value(arg).get('type')),
                boolean(object_value(arg).get('unbounded')),
            )
            for arg in values(item.get('tuple_arguments'))
        )
        literal = item.get('literal')
        if not isinstance(literal, (str, int, float, bool, type(None))):
            raise ValueError('COV002: native class literal is unsupported')
        return replace(
            base,
            name=string(item.get('name')),
            declaration=declaration(item.get('declaration')),
            protocol=boolean(item.get('protocol')),
            unspecialized=boolean(item.get('unspecialized')),
            native_source_id=integer(item.get('native_source_id')),
            details_flags=integer(item.get('details_flags')),
            arguments=indices(item.get('arguments')),
            type_parameters=indices(item.get('type_parameters')),
            bases=indices(item.get('bases')),
            tuple_arguments=tuple_arguments,
            literal=literal,
        )
    if category == 'function':
        return replace(
            base,
            name=string(item.get('name')),
            declaration=declaration(item.get('declaration')),
            details_flags=integer(item.get('details_flags')),
            parameters=tuple(parameter(arg) for arg in values(item.get('parameters'))),
            type_parameters=indices(item.get('type_parameters')),
            return_type=integer(item.get('return_type')),
            declared_return=boolean(item.get('declared_return')),
            gradual_callable=boolean(item.get('gradual_callable')),
        )
    if category == 'overloaded':
        overloads = indices(item.get('overloads'))
        if not overloads:
            raise ValueError('COV002: native overload set is empty')
        return replace(
            base,
            overloads=overloads,
            implementation=optional_integer(item.get('implementation')),
        )
    if category == 'union':
        members = indices(item.get('members'))
        if not members:
            raise ValueError('COV002: native union has no members')
        return replace(base, members=members)
    if category == 'typevar':
        return replace(
            base,
            name=string(item.get('name')),
            scope=optional_string(item.get('scope')),
            variance=integer(item.get('variance')),
            constraints=indices(item.get('constraints')),
            bound=optional_integer(item.get('bound')),
            default_type=optional_integer(item.get('default_type')),
            default_explicit=boolean(item.get('default_explicit')),
        )
    if category == 'any':
        return replace(base, ellipsis=boolean(item.get('ellipsis')))
    return base
