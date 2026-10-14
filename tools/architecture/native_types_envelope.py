from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.native_types_payload import declaration, integer, string, values
from tools.architecture.native_types_records import TypedSite


def parse_sites(entries: JsonValue) -> tuple[TypedSite, ...]:
    sites: list[TypedSite] = []
    for value in values(entries):
        query = object_value(value)
        declarations = tuple(
            declaration(value) for value in values(query.get('declarations'))
        )
        if any(value is None for value in declarations):
            raise ValueError('COV002: native query declaration is unresolved')
        sites.append(
            TypedSite(
                string(query.get('path')),
                integer(query.get('line')),
                integer(query.get('column')),
                integer(query.get('type')),
                tuple(value for value in declarations if value is not None),
            )
        )
    return tuple(sites)


def parse_artifacts(value: JsonValue) -> tuple[tuple[str, str], ...]:
    artifacts = tuple(
        (key, string(value)) for key, value in object_value(value).items()
    )
    return artifacts


def parse_inputs(value: JsonValue) -> tuple[tuple[str, str], ...]:
    inputs = tuple(
        (
            string(object_value(value).get('path')),
            string(object_value(value).get('sha256')),
        )
        for value in values(value)
    )
    return inputs
