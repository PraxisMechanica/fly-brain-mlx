"""Typed JSON objects used by check diagnostics and contract fixtures."""

from typing import TypeAlias

JsonValue: TypeAlias = (
    str | int | float | bool | None | list['JsonValue'] | dict[str, 'JsonValue']
)


def object_value(value: JsonValue) -> dict[str, JsonValue]:
    if not isinstance(value, dict):
        raise ValueError('COV002: JSON value is not an object')
    return value
