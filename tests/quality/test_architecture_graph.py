from pathlib import Path

import pytest

from tests.quality.test_architecture_symbols import (
    CONTRACT,
    STORE,
    semantic_model,
    symbol_named,
)
from tools.architecture.graph import Edge, Graph, call_graph, source_graph
from tools.architecture.symbols import Location, Provenance, Reference, Symbol

pytestmark = pytest.mark.unit


def test_same_module_transitive_call_path_has_exact_native_evidence(
    tmp_path: Path,
) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': STORE
            + 'def helper(port: Store) -> int:\n    return port.read()\n'
            'def execute(port: Store) -> int:\n    return helper(port)\n'
        },
    )
    graph = call_graph(model)
    execute = symbol_named(model, 'service.py', 'execute')
    forbidden = symbol_named(model, 'service.py', 'Store.read')
    paths = graph.forbidden_paths((execute,), (forbidden,))
    assert [
        (
            edge.source.name,
            edge.target.name,
            edge.evidence.location.line,
            edge.evidence.location.column,
        )
        for edge in paths[0]
    ] == [('execute', 'helper', 7, 11), ('helper', 'Store.read', 5, 16)]
    direct_only = Graph(
        graph.nodes, tuple(edge for edge in graph.edges if edge.source == execute)
    )
    assert not direct_only.forbidden_paths((execute,), (forbidden,))


@pytest.mark.parametrize(
    'body',
    (
        'def execute(port: Port) -> int:\n    return port.read()\n',
        'def execute(value: int) -> int:\n    return value + 1\n',
    ),
)
def test_injected_port_repair_and_close_pure_case_have_no_concrete_call_path(
    tmp_path: Path, body: str
) -> None:
    model = semantic_model(tmp_path, {'service.py': CONTRACT + STORE + body})
    graph = call_graph(model)
    assert not graph.forbidden_paths(
        (symbol_named(model, 'service.py', 'execute'),),
        (symbol_named(model, 'service.py', 'Store.read'),),
    )


def test_type_only_reexport_source_path_retains_file_and_declaration_links(
    tmp_path: Path,
) -> None:
    model = semantic_model(
        tmp_path,
        {
            'repository.py': STORE,
            'facade.py': 'from repository import Store as Hidden\n',
            'service.py': 'from typing import TYPE_CHECKING\n'
            'if TYPE_CHECKING:\n    from facade import Hidden as Alias\n'
            'def execute(port: Alias) -> int:\n    return 1\n',
        },
    )
    graph = source_graph(model)
    service = symbol_named(model, 'service.py', '<module>')
    facade = symbol_named(model, 'facade.py', '<module>')
    implementation = symbol_named(model, 'repository.py', 'Store')
    imported_path = graph.path(service, facade)
    assert imported_path is not None
    assert (
        imported_path[0].evidence.kind,
        imported_path[0].evidence.location.line,
    ) == ('import', 3)
    annotation_path = graph.path(
        symbol_named(model, 'service.py', 'execute'), implementation
    )
    assert annotation_path is not None
    assert [edge.evidence.kind for edge in annotation_path] == ['declaration', 'type']
    assert [edge.evidence.location.line for edge in annotation_path] == [4, 4]


def test_native_call_cycle_and_group_cycle_keep_original_edge_evidence(
    tmp_path: Path,
) -> None:
    model = semantic_model(
        tmp_path,
        {
            'service.py': 'def alpha(value: int) -> int:\n    return beta(value)\n'
            'def beta(value: int) -> int:\n    return alpha(value)\n'
        },
    )
    alpha = symbol_named(model, 'service.py', 'alpha')
    beta = symbol_named(model, 'service.py', 'beta')
    graph = call_graph(model)
    cycles = graph.cycles()
    assert len(cycles) == 1
    assert {(edge.source, edge.target) for edge in cycles[0]} == {
        (alpha, beta),
        (beta, alpha),
    }
    collapsed = graph.collapse(
        {node: node.name if node in (alpha, beta) else 'other' for node in graph.nodes}
    )
    assert {edge.evidence.location.line for edge in collapsed.cycles()[0]} == {2, 4}
    weakened = Graph(
        graph.nodes, tuple(edge for edge in graph.edges if edge.source != beta)
    )
    assert not weakened.cycles()


def evidence(tmp_path: Path) -> Reference:
    path = str(tmp_path / 'fixture.py')
    location = Location(path, 1, 0, 1, 1)
    symbol = Symbol(
        'fixture',
        'function',
        location,
        Provenance(path, 'fixture-graph', 'fixture.py'),
        None,
    )
    return Reference(symbol, symbol, location, 'read')


def test_generic_graph_returns_shortest_path_and_distinct_cycle_witnesses(
    tmp_path: Path,
) -> None:
    origin = evidence(tmp_path)
    graph = Graph(
        ('a', 'b', 'c', 'd', 'e'),
        tuple(
            Edge(source, target, origin)
            for source, target in (
                ('a', 'b'),
                ('b', 'c'),
                ('a', 'c'),
                ('c', 'a'),
                ('d', 'd'),
            )
        ),
    )
    path = graph.path('a', 'c')
    assert path is not None and [(edge.source, edge.target) for edge in path] == [
        ('a', 'c')
    ]
    assert len(graph.cycles()) == 2
    assert graph.path('a', 'e') is None


def test_deep_generic_graph_does_not_depend_on_python_recursion_limit(
    tmp_path: Path,
) -> None:
    origin = evidence(tmp_path)
    graph = Graph(
        tuple(range(2000)), tuple(Edge(node, node + 1, origin) for node in range(1999))
    )
    path = graph.path(0, 1999)
    assert path is not None and len(path) == 1999
    assert len(graph.components()) == 2000
    assert not graph.cycles()


def test_empty_absent_and_incomplete_graph_scopes_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='COV002: intended graph scope is empty'):
        Graph[str]((), ())
    with pytest.raises(
        ValueError, match='COV002: resolved graph edge has an undiscovered node'
    ):
        Graph(('a',), (Edge('a', 'absent', evidence(tmp_path)),))
    graph: Graph[str] = Graph(('a', 'b'), ())
    with pytest.raises(
        ValueError, match='COV002: intended populated graph selection is empty'
    ):
        graph.forbidden_paths((), ('b',))
    with pytest.raises(
        ValueError, match='COV002: selected graph node is absent from discovery'
    ):
        graph.path('a', 'absent')
    with pytest.raises(ValueError, match='COV002: graph group mapping is incomplete'):
        graph.collapse({'a': 'domain'})
