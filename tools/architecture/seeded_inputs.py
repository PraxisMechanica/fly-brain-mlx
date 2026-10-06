import ast
import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tools.architecture.compiler import Compiler
from tools.architecture.coordinates import Coordinates
from tools.architecture.graph import Edge, call_graph
from tools.architecture.inventory import Finding, Source
from tools.architecture.resolution import Resolver, unique_location
from tools.architecture.symbols import Location, Reference, SemanticModel, Symbol

Role = Literal['rules', 'service', 'module', 'types', 'ports', 'external_adapter']


class ResolvedCalls(Resolver):
    def callable(
        self, location: Location, seen: frozenset[Symbol] = frozenset()
    ) -> tuple[Symbol, tuple[Reference, ...]]:
        target = self.symbol(
            unique_location(
                self.native(location)['definitions'], 'callable declaration'
            )
        )
        if target.kind in ('class', 'function'):
            return target, ()
        return self.callable_alias(location, seen)


def analyze(root: Path, sources: Sequence[Source], compiler: Compiler) -> SemanticModel:
    return ResolvedCalls(root, sources, compiler).analyze()


@dataclass(frozen=True)
class Scope:
    path: str
    name: str
    owner: str
    role: Role


def _identity(symbol: Symbol) -> tuple[str | None, str]:
    return symbol.provenance.project_path, symbol.name


def select(model: SemanticModel, path: str, name: str) -> Symbol:
    matches = [item for item in model.symbols if _identity(item) == (path, name)]
    if len(matches) != 1:
        raise ValueError(
            f'COV002: seeded-input symbol is absent or ambiguous: {path}:{name}'
        )
    return matches[0]


def _scopes(model: SemanticModel, scopes: Sequence[Scope]) -> dict[Symbol, Scope]:
    if not scopes:
        raise ValueError('COV002: seeded-input classification scope is empty')
    result: dict[Symbol, Scope] = {}
    for scope in scopes:
        symbol = select(model, scope.path, scope.name)
        if not scope.owner.strip() or symbol in result:
            raise ValueError('COV002: seeded-input ownership is invalid or ambiguous')
        result[symbol] = scope
    for symbol in model.symbols:
        if (
            symbol.provenance.project_path is not None
            and symbol.kind in ('function', 'class', 'module')
            and symbol not in result
        ):
            raise ValueError(
                'COV002: seeded-input callable is unclassified: ' + symbol.name
            )
    return result


def _verify(model: SemanticModel) -> None:
    for item in {symbol.provenance for symbol in model.symbols}:
        try:
            digest = hashlib.sha256(Path(item.path).read_bytes()).hexdigest()
        except OSError as error:
            raise ValueError('COV002: seeded-input source disappeared') from error
        if digest != item.sha256:
            raise ValueError('COV002: seeded-input source changed after resolution')


def _witness(path: Sequence[Edge[Symbol]]) -> str:
    return (
        ' -> '.join(
            f'{item.source.name} ({item.evidence.location.path}:{item.evidence.location.line})'
            for item in path
        )
        + ' -> '
        + path[-1].target.name
    )


def _defaults(symbol: Symbol) -> tuple[ast.expr, ...]:
    tree = ast.parse(Path(symbol.provenance.path).read_bytes())
    nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.lineno == symbol.location.line
        and node.name == symbol.name.rsplit('.', 1)[-1]
    ]
    if len(nodes) != 1:
        raise ValueError('COV002: seeded-input function has no exact default scope')
    return tuple(nodes[0].args.defaults) + tuple(
        item for item in nodes[0].args.kw_defaults if item is not None
    )


def _in_default(symbol: Symbol, location: Location) -> bool:
    path = Path(symbol.provenance.path)
    coordinates = Coordinates(path, path.read_text())
    for item in _defaults(symbol):
        if item.end_lineno is None or item.end_col_offset is None:
            raise ValueError('COV002: default expression scope is incomplete')
        start, end = coordinates.ast_bounds(
            item.lineno, item.col_offset, item.end_lineno, item.end_col_offset
        )
        bounds = coordinates.location(start, end)
        if (bounds.line, bounds.column) <= (location.line, location.column) and (
            location.end_line,
            location.end_column,
        ) <= (bounds.end_line, bounds.end_column):
            return True
    return False


def check(
    model: SemanticModel,
    scopes: Sequence[Scope],
    effects: Sequence[Symbol],
    constructors: Sequence[Symbol] = (),
    pure_targets: Sequence[Symbol] = (),
) -> tuple[Finding, ...]:
    """Check exact reviewed effects in a resolved, explicitly classified call scope."""
    model.capabilities.require('declaration_identity')
    model.capabilities.require('explicit_call_targets')
    _verify(model)
    classified = _scopes(model, scopes)
    rules = tuple(
        symbol for symbol, scope in classified.items() if scope.role == 'rules'
    )
    if not rules or not effects:
        raise ValueError('COV002: seeded-input rule/effect scope is empty')
    graph = call_graph(model)
    graph.require_nodes((*rules, *effects, *constructors, *pure_targets))
    findings: list[Finding] = []
    terminals = frozenset((*effects, *constructors, *pure_targets))
    for path in graph.forbidden_paths(rules, tuple((*effects, *constructors))):
        call = path[0].evidence
        findings.append(
            Finding(
                'STATE001',
                call.location.path,
                call.location.line,
                _witness(path)
                + ': acquire through required typed ports in a service; supply completed values to rules',
            )
        )
    for call in model.calls:
        scope = classified.get(call.caller)
        if scope is None:
            raise ValueError('COV002: seeded-input caller ownership is unresolved')
        if call.target in constructors and scope.role not in (
            'module',
            'external_adapter',
        ):
            findings.append(
                Finding(
                    'DI002',
                    call.location.path,
                    call.location.line,
                    'Non-assembly collaborator construction: ' + call.target.name,
                )
            )
        reachable = scope.role == 'rules' or any(
            graph.path(rule, call.caller) is not None for rule in rules
        )
        if reachable and call.caller not in terminals and call.target not in terminals:
            if call.kind == 'constructor':
                raise ValueError('COV002: constructor lacks an exact reviewed summary')
            target = classified.get(call.target)
            if target is None or target.role == 'ports':
                raise ValueError(
                    'COV002: seeded-input target has no reviewed purity/effect summary: '
                    + call.target.name
                )
    for reference in model.references:
        scope = classified.get(reference.source)
        if (
            scope is not None
            and scope.role == 'rules'
            and reference.kind == 'read'
            and reference.target in (*effects, *constructors)
        ):
            if _in_default(reference.source, reference.location):
                findings.append(
                    Finding(
                        'DI002',
                        reference.location.path,
                        reference.location.line,
                        'Hidden default sampler: ' + reference.target.name,
                    )
                )
    return tuple(
        sorted(
            set(findings),
            key=lambda item: (item.path, item.line, item.rule, item.message),
        )
    )
