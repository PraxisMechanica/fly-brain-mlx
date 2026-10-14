"""Pure validation of native compiler dependency and read receipts."""

from pathlib import Path

from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.native_types_schema import integer, string, values


def facts(
    response: JsonValue,
    root: Path,
    sources: tuple[str, ...],
    records: dict[str, str],
    configuration: dict[str, str],
    flags: tuple[str, ...],
) -> tuple[dict[str, set[str]], set[str], dict[str, str]]:
    response = object_value(response)
    if (
        integer(response.get('schema')),
        response.get('version'),
        response.get('flags'),
    ) != (
        1,
        '5.9.3',
        list(flags),
    ):
        raise ValueError('COV002: native compiler context differs from checker')
    graph = {
        Path(path).relative_to(root).as_posix(): {
            Path(string(value)).relative_to(root).as_posix()
            for value in values(required)
        }
        for path, required in object_value(response.get('graph')).items()
    }
    globals_ = {
        Path(string(value)).relative_to(root).as_posix()
        for value in values(response.get('globals'))
    }
    if not globals_ <= graph.keys() or any(
        name not in required or not required <= graph.keys()
        for name, required in graph.items()
    ):
        raise ValueError('COV002: native dependency scope is incomplete')
    reads = {
        path: string(expected)
        for path, expected in object_value(response.get('inputs')).items()
    }
    if set(graph) != set(sources) or any(
        reads.get(path) != expected
        for path, expected in {**records, **configuration}.items()
    ):
        raise ValueError('COV002: native compiler omitted required input')
    return graph, globals_, reads
