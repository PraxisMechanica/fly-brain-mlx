from collections import deque
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from tools.architecture.symbols import Call, Reference, SemanticModel, Symbol

Node = TypeVar('Node', bound=Hashable)
Group = TypeVar('Group', bound=Hashable)


@dataclass(frozen=True)
class Edge(Generic[Node]):
    source: Node
    target: Node
    evidence: Reference | Call


class Graph(Generic[Node]):
    def __init__(self, nodes: Sequence[Node], edges: Sequence[Edge[Node]]) -> None:
        self.nodes = tuple(dict.fromkeys(nodes))
        self.edges = tuple(dict.fromkeys(edges))
        if not self.nodes:
            raise ValueError('COV002: intended graph scope is empty')
        self.outgoing: dict[Node, list[Edge[Node]]] = {node: [] for node in self.nodes}
        self.incoming: dict[Node, list[Edge[Node]]] = {node: [] for node in self.nodes}
        for edge in self.edges:
            if edge.source not in self.outgoing or edge.target not in self.outgoing:
                raise ValueError('COV002: resolved graph edge has an undiscovered node')
            self.outgoing[edge.source].append(edge)
            self.incoming[edge.target].append(edge)

    def require_nodes(self, nodes: Sequence[Node]) -> None:
        if not nodes:
            raise ValueError('COV002: intended populated graph selection is empty')
        if any(node not in self.outgoing for node in nodes):
            raise ValueError('COV002: selected graph node is absent from discovery')

    def path(self, source: Node, target: Node) -> tuple[Edge[Node], ...] | None:
        self.require_nodes((source, target))
        queue = deque((source,))
        previous: dict[Node, Edge[Node] | None] = {source: None}
        while queue:
            current = queue.popleft()
            for edge in self.outgoing[current]:
                if edge.target == target:
                    result = [edge]
                    node = current
                    while previous[node] is not None:
                        predecessor = previous[node]
                        assert predecessor is not None
                        result.append(predecessor)
                        node = predecessor.source
                    return tuple(reversed(result))
                if edge.target not in previous:
                    previous[edge.target] = edge
                    queue.append(edge.target)
        return None

    def forbidden_paths(
        self, sources: Sequence[Node], targets: Sequence[Node]
    ) -> tuple[tuple[Edge[Node], ...], ...]:
        self.require_nodes(sources)
        self.require_nodes(targets)
        return tuple(
            path
            for source in sources
            for target in targets
            if (path := self.path(source, target)) is not None
        )

    def components(self) -> tuple[tuple[Node, ...], ...]:
        visited: set[Node] = set()
        finished: list[Node] = []
        for node in self.nodes:
            stack = [(node, False)]
            while stack:
                current, finish = stack.pop()
                if finish:
                    finished.append(current)
                elif current not in visited:
                    visited.add(current)
                    stack.append((current, True))
                    stack.extend(
                        (edge.target, False)
                        for edge in reversed(self.outgoing[current])
                    )
        visited.clear()
        result: list[tuple[Node, ...]] = []
        for node in reversed(finished):
            if node in visited:
                continue
            members: list[Node] = []
            pending = [node]
            while pending:
                current = pending.pop()
                if current not in visited:
                    visited.add(current)
                    members.append(current)
                    pending.extend(
                        edge.source for edge in reversed(self.incoming[current])
                    )
            result.append(tuple(members))
        return tuple(result)

    def cycles(self) -> tuple[tuple[Edge[Node], ...], ...]:
        """Return one evidenced cycle per cyclic strongly connected component."""
        result: list[tuple[Edge[Node], ...]] = []
        for component in self.components():
            if len(component) == 1:
                node = component[0]
                loop = next(
                    (edge for edge in self.outgoing[node] if edge.target == node), None
                )
                if loop is not None:
                    result.append((loop,))
                continue
            for node in component:
                if path := self.path(node, node):
                    result.append(path)
                    break
        return tuple(result)

    def collapse(self, groups: Mapping[Node, Group]) -> 'Graph[Group]':
        if any(node not in groups for node in self.nodes):
            raise ValueError('COV002: graph group mapping is incomplete')
        edges = tuple(
            Edge(groups[edge.source], groups[edge.target], edge.evidence)
            for edge in self.edges
            if groups[edge.source] != groups[edge.target]
        )
        return Graph(tuple(groups[node] for node in self.nodes), edges)


def source_graph(model: SemanticModel) -> Graph[Symbol]:
    model.capabilities.require('declaration_identity')
    by_location = {symbol.location: symbol for symbol in model.symbols}
    declarations: list[Reference] = []
    for symbol in model.symbols:
        if symbol.container is not None:
            container = by_location.get(symbol.container)
            if container is None:
                raise ValueError('COV002: source graph declaration container is absent')
            declarations.append(
                Reference(container, symbol, symbol.location, 'declaration')
            )
    references = (
        *declarations,
        *model.references,
        *(reference for call in model.calls for reference in call.aliases),
    )
    return Graph(
        model.symbols,
        tuple(Edge(item.source, item.target, item) for item in references),
    )


def call_graph(model: SemanticModel) -> Graph[Symbol]:
    model.capabilities.require('explicit_call_targets')
    return Graph(
        model.symbols,
        tuple(Edge(item.caller, item.target, item) for item in model.calls),
    )
