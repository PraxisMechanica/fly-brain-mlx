import ast
import hashlib
import tokenize
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tools.architecture.coordinates import Coordinates
from tools.architecture.inventory import Source, declarations
from tools.architecture.symbols import (
    Location,
    Provenance,
    ReferenceKind,
    Symbol,
    SymbolKind,
)


@dataclass(frozen=True)
class Site:
    location: Location
    source: Symbol
    scope: Symbol
    kind: ReferenceKind


@dataclass(frozen=True)
class CallSite:
    expression: ast.expr
    location: Location
    caller: Symbol


@dataclass(frozen=True)
class Binding:
    symbol: Symbol
    value: ast.expr | None
    unconditional: bool


class Document(ast.NodeVisitor):
    def __init__(self, root: Path, path: Path, expected: Source | None) -> None:
        try:
            content = path.read_bytes()
            tree = ast.parse(content, filename=str(path))
        except (OSError, UnicodeError, SyntaxError, ValueError) as error:
            raise ValueError(
                'COV002: semantic source could not be parsed: ' + str(path)
            ) from error
        digest = hashlib.sha256(content).hexdigest()
        if expected is not None and (
            expected.sha256 != digest or expected.declarations != declarations(tree)
        ):
            raise ValueError('COV002: semantic discovery changed: ' + expected.path)
        self.provenance = Provenance(
            str(path.resolve()), digest, expected.path if expected is not None else None
        )
        self.content = content
        self.scan = expected is not None
        try:
            self.coordinates = Coordinates(path, content.decode('utf-8-sig'))
        except (UnicodeError, tokenize.TokenError) as error:
            raise ValueError(
                'COV002: semantic source encoding or tokens are unsupported: '
                + str(path)
            ) from error
        self.parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        self.symbols: dict[Location, Symbol] = {}
        self.declaration_ranges: dict[Location, Symbol] = {}
        self.sites: list[Site] = []
        self.calls: list[CallSite] = []
        self.bindings: dict[Symbol, Binding] = {}
        self.writes: dict[tuple[Location | None, str], int] = {}
        self.directives = any(
            isinstance(item, (ast.Global, ast.Nonlocal)) for item in ast.walk(tree)
        )
        location = Location(str(path.resolve()), 1, 0, 1, 0)
        self.module = Symbol('<module>', 'module', location, self.provenance, None)
        self.symbols[location] = self.module
        self.declaration_ranges[location] = self.module
        self.scope: Symbol = self.module
        self.source: Symbol = self.module
        self.kind: ReferenceKind = 'read'
        try:
            self.visit(tree)
        except RecursionError as error:
            raise ValueError(
                'COV002: semantic syntax traversal exceeds supported depth'
            ) from error
        self.verify(root)

    def verify(self, root: Path) -> None:
        try:
            current = Path(self.provenance.path).read_bytes()
        except OSError as error:
            raise ValueError('COV002: semantic source disappeared') from error
        if current != self.content:
            raise ValueError(
                'COV002: source changed during semantic analysis: '
                + self.provenance.path
            )
        if self.provenance.project_path is not None and not Path(
            self.provenance.path
        ).is_relative_to(root):
            raise ValueError('COV002: first-party source escapes semantic workspace')

    def at(
        self,
        node: ast.expr
        | ast.arg
        | ast.alias
        | ast.ClassDef
        | ast.FunctionDef
        | ast.AsyncFunctionDef,
    ) -> Location:
        if node.end_lineno is None or node.end_col_offset is None:
            raise ValueError('COV002: AST source end position is missing')
        try:
            if isinstance(node, ast.Name):
                start, end = self.coordinates.ast_bounds(
                    node.lineno, node.col_offset, node.end_lineno, node.end_col_offset
                )
                return self.coordinates.location(start, end)
            if isinstance(node, ast.Attribute):
                return self.coordinates.attribute(
                    node.end_lineno, node.end_col_offset, node.attr
                )
            return self.coordinates.identifier(
                node.lineno,
                node.col_offset,
                node.end_lineno,
                node.end_col_offset,
                declaration=isinstance(
                    node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                ),
            )
        except ValueError as error:
            raise ValueError(
                f'{error} at {self.provenance.path}:{node.lineno}:{node.col_offset} (AST byte column)'
            ) from error

    def declare(self, name: str, kind: SymbolKind, location: Location) -> Symbol:
        qualified = name if self.scope is self.module else self.scope.name + '.' + name
        symbol = Symbol(qualified, kind, location, self.provenance, self.scope.location)
        self.symbols[location] = symbol
        self.declaration_ranges[location] = symbol
        key = (symbol.container, name)
        self.writes[key] = self.writes.get(key, 0) + 1
        return symbol

    def visit_with(
        self, node: ast.AST, source: Symbol, kind: ReferenceKind = 'read'
    ) -> None:
        previous = self.source, self.kind
        self.source, self.kind = source, kind
        self.visit(node)
        self.source, self.kind = previous

    def definition(
        self, node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
    ) -> Symbol:
        symbol = self.declare(
            node.name,
            'class' if isinstance(node, ast.ClassDef) else 'function',
            self.at(node),
        )
        for decorator in node.decorator_list:
            self.visit_with(decorator, symbol, 'decorator')
        return symbol

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        symbol = self.definition(node)
        for base in node.bases:
            self.visit_with(base, symbol, 'base')
        for keyword in node.keywords:
            self.visit_with(keyword.value, symbol, 'base')
        previous = self.scope, self.source
        self.scope = self.source = symbol
        for statement in node.body:
            self.visit(statement)
        self.scope, self.source = previous

    def function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        symbol = self.definition(node)
        previous = self.scope, self.source
        self.scope = self.source = symbol
        positional = (*node.args.posonlyargs, *node.args.args)
        defaults: tuple[ast.expr | None, ...] = (None,) * (
            len(positional) - len(node.args.defaults)
        ) + tuple(node.args.defaults)
        arguments = [
            (argument, 0, default)
            for argument, default in zip(positional, defaults, strict=True)
        ]
        arguments.extend(
            (argument, 0, default)
            for argument, default in zip(
                node.args.kwonlyargs, node.args.kw_defaults, strict=True
            )
        )
        if node.args.vararg is not None:
            arguments.append((node.args.vararg, 1, None))
        if node.args.kwarg is not None:
            arguments.append((node.args.kwarg, 2, None))
        parameters: list[tuple[ast.arg, Symbol]] = []
        for argument, prefix, default in arguments:
            parameter = self.parameter(argument, prefix, default)
            parameters.append((argument, parameter))
        self.scope = previous[0]
        for argument, parameter in parameters:
            if argument.annotation is not None:
                self.visit_with(argument.annotation, parameter, 'type')
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit_with(default, symbol)
        if node.returns is not None:
            self.visit_with(node.returns, symbol, 'type')
        self.scope = symbol
        for statement in node.body:
            self.visit(statement)
        self.scope, self.source = previous

    def parameter(
        self, argument: ast.arg, prefix: int, default: ast.expr | None
    ) -> Symbol:
        symbol = self.declare(argument.arg, 'parameter', self.at(argument))
        end_node = default if default is not None else argument
        if end_node.end_lineno is None or end_node.end_col_offset is None:
            raise ValueError('COV002: parameter source range is missing')
        start, end = self.coordinates.ast_bounds(
            argument.lineno,
            argument.col_offset - prefix,
            end_node.end_lineno,
            end_node.end_col_offset,
        )
        self.declaration_ranges[self.coordinates.location(start, end)] = symbol
        return symbol

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.function(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            if self.scan:
                self.sites.append(
                    Site(self.at(node), self.source, self.scope, self.kind)
                )
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self.declare(node.id, 'variable', self.at(node))

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.visit(node.value)
        if isinstance(node.ctx, ast.Load):
            if self.scan:
                self.sites.append(
                    Site(self.at(node), self.source, self.scope, self.kind)
                )
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self.declare(node.attr, 'attribute', self.at(node))

    def assign(self, target: ast.expr, value: ast.expr | None) -> Symbol:
        self.visit(target)
        symbol = (
            self.symbols.get(self.at(target))
            if isinstance(target, (ast.Name, ast.Attribute))
            else None
        )
        if symbol is None:
            return self.source
        statement = self.parents[target]
        parent = self.parents.get(statement)
        unconditional = isinstance(
            parent, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )
        self.bindings[symbol] = Binding(symbol, value, unconditional)
        return symbol

    def visit_Assign(self, node: ast.Assign) -> None:
        owner = self.source
        for target in node.targets:
            owner = self.assign(target, node.value if len(node.targets) == 1 else None)
        self.visit_with(node.value, owner)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        owner = self.assign(node.target, node.value)
        self.visit_with(node.annotation, owner, 'type')
        if node.value is not None:
            self.visit_with(node.value, owner)

    def visit_Call(self, node: ast.Call) -> None:
        if not self.scan:
            return
        if not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise ValueError(
                f'COV002: unsupported computed call target: {self.provenance.path}:{node.lineno}'
            )
        self.calls.append(CallSite(node.func, self.at(node.func), self.scope))
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if self.scan and self.kind == 'type' and isinstance(node.value, str):
            raise ValueError(
                f'COV002: string annotation needs native token resolution: {self.provenance.path}:{node.lineno}'
            )

    def visit_Lambda(self, node: ast.Lambda) -> None:
        if self.scan:
            raise ValueError(
                f'COV002: lambda scope needs native callable resolution: {self.provenance.path}:{node.lineno}'
            )

    def import_alias(self, alias: ast.alias) -> None:
        start, end = self.coordinates.ast_bounds(
            alias.lineno,
            alias.col_offset,
            alias.end_lineno or alias.lineno,
            alias.end_col_offset or alias.col_offset,
        )
        tokens = self.coordinates.names_in(start, end)
        imported = tokens[
            : next(
                (index for index, item in enumerate(tokens) if item.string == 'as'),
                len(tokens),
            )
        ]
        if not imported:
            raise ValueError('COV002: wildcard import has no exact symbol coverage')
        location = self.coordinates.location(imported[-1].start, imported[-1].end)
        if self.scan:
            self.sites.append(Site(location, self.scope, self.scope, 'import'))
        token = tokens[-1] if alias.asname is not None else tokens[0]
        self.declare(
            alias.asname or alias.name.split('.')[0],
            'import',
            self.coordinates.location(token.start, token.end),
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.import_alias(alias)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self.scan and node.module is not None:
            tokens = self.coordinates.names_in(
                (
                    node.lineno,
                    self.coordinates.ast_column(node.lineno, node.col_offset),
                ),
                (
                    node.names[0].lineno,
                    self.coordinates.ast_column(
                        node.names[0].lineno, node.names[0].col_offset
                    ),
                ),
            )
            before_import = tokens[
                : next(
                    (
                        index
                        for index, item in enumerate(tokens)
                        if item.string == 'import'
                    ),
                    len(tokens),
                )
            ]
            if len(before_import) < 2:
                raise ValueError('COV002: imported module has no exact token location')
            chosen = before_import[-1]
            self.sites.append(
                Site(
                    self.coordinates.location(chosen.start, chosen.end),
                    self.scope,
                    self.scope,
                    'import',
                )
            )
        for alias in node.names:
            self.import_alias(alias)


def index_sources(root: Path, sources: Sequence[Source]) -> dict[Path, Document]:
    root = root.resolve()
    if not sources:
        raise ValueError('COV002: semantic discovery scope is empty')
    result: dict[Path, Document] = {}
    for source in sources:
        path = (root / source.path).resolve()
        if not path.is_relative_to(root) or path in result:
            raise ValueError(
                'COV002: semantic discovery contains an invalid or duplicate path'
            )
        result[path] = Document(root, path, source)
    return result
