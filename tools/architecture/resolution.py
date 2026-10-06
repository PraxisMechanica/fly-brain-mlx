import ast
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import unquote, urlsplit

from tools.architecture.compiler import Compiler, JsonValue, object_value
from tools.architecture.inventory import Source
from tools.architecture.semantic_index import Document, Site, index_sources
from tools.architecture.symbols import (
    Call,
    Location,
    NominalType,
    Reference,
    SemanticModel,
    Symbol,
)


def position(value: JsonValue) -> tuple[int, int]:
    item = object_value(value)
    line, column = item.get('line'), item.get('character')
    if type(line) is not int or type(column) is not int or line < 0 or column < 0:
        raise ValueError('COV002: native source position is invalid')
    return line + 1, column


def native_location(value: JsonValue, *, hierarchy: bool = False) -> Location:
    item = object_value(value)
    uri = item.get('uri')
    if not isinstance(uri, str):
        raise ValueError('COV002: native symbol URI is missing')
    try:
        parsed = urlsplit(uri)
    except ValueError as error:
        raise ValueError('COV002: native symbol provenance URI is malformed') from error
    if (
        parsed.scheme != 'file'
        or parsed.netloc not in ('', 'localhost')
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError('COV002: native symbol has unsupported provenance URI')
    path = Path(unquote(parsed.path))
    if not path.is_absolute():
        raise ValueError('COV002: native symbol provenance path is not absolute')
    location_range = object_value(item.get('selectionRange' if hierarchy else 'range'))
    start, end = (
        position(location_range.get('start')),
        position(location_range.get('end')),
    )
    if end < start:
        raise ValueError('COV002: native symbol range is reversed')
    try:
        resolved = path.resolve()
    except (ValueError, OSError) as error:
        raise ValueError('COV002: native symbol provenance path is invalid') from error
    return Location(str(resolved), *start, *end)


def unique_location(value: JsonValue, label: str) -> Location:
    if not isinstance(value, list) or not value:
        raise ValueError('COV002: native ' + label + ' is unresolved')
    locations = tuple(dict.fromkeys(native_location(item) for item in value))
    if len(locations) != 1:
        raise ValueError('COV002: native ' + label + ' is ambiguous')
    return locations[0]


class Resolver:
    def __init__(
        self, root: Path, sources: Sequence[Source], compiler: Compiler
    ) -> None:
        self.root = root.resolve()
        if compiler.root != self.root:
            raise ValueError('COV002: native compiler and semantic workspace differ')
        if not compiler.capabilities.get('callHierarchyProvider'):
            raise ValueError('COV002: native compiler lacks callHierarchyProvider')
        self.sources = tuple(sources)
        self.compiler = compiler
        self.documents = index_sources(self.root, sources)
        self.responses: dict[Location, dict[str, JsonValue]] = {}

    def document(self, path: Path) -> Document:
        path = path.resolve()
        document = self.documents.get(path)
        if document is None:
            if path.is_relative_to(self.root):
                raise ValueError(
                    'COV002: native resolution reached undiscovered source: '
                    + str(path)
                )
            document = Document(self.root, path, None)
            self.documents[path] = document
        document.verify(self.root)
        return document

    def symbol(self, location: Location) -> Symbol:
        document = self.document(Path(location.path))
        symbol = document.declaration_ranges.get(location)
        if symbol is None:
            raise ValueError(
                f'COV002: native declaration has no exact source mapping: {location.path}:{location.line}:{location.column}'
            )
        return symbol

    def native(self, location: Location) -> dict[str, JsonValue]:
        self.document(Path(location.path))
        response = self.responses.get(location)
        if response is None:
            response = self.compiler.resolve(
                Path(location.path), location.line, location.column
            )
            self.responses[location] = response
        return response

    def reference(self, site: Site) -> Reference:
        try:
            target = self.symbol(
                unique_location(
                    self.native(site.location)['definitions'], 'declaration'
                )
            )
        except ValueError as error:
            raise ValueError(
                f'{error} at {site.location.path}:{site.location.line}:{site.location.column}'
            ) from error
        captured = False
        container = site.scope.container
        document = self.document(Path(site.scope.location.path))
        while container is not None:
            ancestor = document.symbols.get(container)
            if ancestor is None:
                raise ValueError('COV002: lexical source scope is unresolved')
            if ancestor.kind == 'function' and target.container == ancestor.location:
                captured = True
                break
            container = ancestor.container
        return Reference(site.source, target, site.location, site.kind, captured)

    def nominal_type(self, location: Location) -> NominalType:
        """Resolve one nominal class only; this does not certify a complete type."""
        try:
            target = self.symbol(
                unique_location(self.native(location)['types'], 'type definition')
            )
        except ValueError as error:
            raise ValueError(
                f'{error} at {location.path}:{location.line}:{location.column}'
            ) from error
        if target.kind != 'class':
            raise ValueError(
                f'COV002: native type definition is not a nominal class: {location.path}:{location.line}:{location.column}'
            )
        return NominalType(location, target)

    def callable(
        self, location: Location, seen: frozenset[Symbol] = frozenset()
    ) -> tuple[Symbol, tuple[Reference, ...]]:
        try:
            unique_location(
                self.native(location)['definitions'], 'callable declaration'
            )
        except ValueError as error:
            raise ValueError(
                f'{error} at {location.path}:{location.line}:{location.column}'
            ) from error
        value = self.compiler.request(
            'textDocument/prepareCallHierarchy',
            {
                'textDocument': {'uri': Path(location.path).as_uri()},
                'position': {'line': location.line - 1, 'character': location.column},
            },
        )
        if value:
            if not isinstance(value, list) or len(value) != 1:
                raise ValueError('COV002: native callable target is ambiguous')
            item = object_value(value[0])
            target = self.symbol(native_location(item, hierarchy=True))
            if item.get('kind') not in (5, 6, 12) or target.kind not in (
                'class',
                'function',
            ):
                raise ValueError(
                    'COV002: native callable target lacks a source contract'
                )
            return target, ()
        return self.callable_alias(location, seen)

    def callable_alias(
        self, location: Location, seen: frozenset[Symbol]
    ) -> tuple[Symbol, tuple[Reference, ...]]:
        if len(seen) >= 128:
            raise ValueError('COV002: callable alias chain exceeds supported depth 128')
        target = self.symbol(
            unique_location(self.native(location)['definitions'], 'callable binding')
        )
        if target in seen:
            raise ValueError('COV002: callable alias cycle is unresolved')
        document = self.document(Path(target.location.path))
        binding = document.bindings.get(target)
        key = (target.container, target.name.rsplit('.', 1)[-1])
        if (
            binding is None
            or not binding.unconditional
            or document.writes.get(key) != 1
            or document.directives
        ):
            raise ValueError(
                f'COV002: callable binding is not one unconditional assignment: {location.path}:{location.line}:{location.column}'
            )
        if not isinstance(binding.value, (ast.Name, ast.Attribute)):
            raise ValueError(
                f'COV002: callable factory or computed alias needs structured native types: {location.path}:{location.line}:{location.column}'
            )
        rhs = document.at(binding.value)
        resolved, aliases = self.callable(rhs, seen | {target})
        rhs_target = self.symbol(
            unique_location(self.native(rhs)['definitions'], 'alias RHS')
        )
        return resolved, (Reference(target, rhs_target, rhs, 'read'), *aliases)

    def analyze(self) -> SemanticModel:
        references: list[Reference] = []
        calls: list[Call] = []
        first_party = tuple(
            document
            for document in self.documents.values()
            if document.provenance.project_path is not None
        )
        for document in first_party:
            references.extend(self.reference(site) for site in document.sites)
            for site in document.calls:
                target, aliases = self.callable(site.location)
                calls.append(
                    Call(
                        site.caller,
                        target,
                        site.location,
                        'constructor' if target.kind == 'class' else 'function',
                        aliases,
                    )
                )
        for document in self.documents.values():
            document.verify(self.root)
        symbols = dict.fromkeys(
            symbol for document in first_party for symbol in document.symbols.values()
        )
        for item in references:
            symbols[item.target] = None
        for call in calls:
            symbols[call.target] = None
            for alias in call.aliases:
                symbols[alias.source] = symbols[alias.target] = None
        for symbol in tuple(symbols):
            container = symbol.container
            document = self.document(Path(symbol.location.path))
            while container is not None:
                ancestor = document.symbols.get(container)
                if ancestor is None:
                    raise ValueError('COV002: resolved symbol container is absent')
                symbols[ancestor] = None
                container = ancestor.container
        return SemanticModel(
            self.sources, tuple(symbols), tuple(references), tuple(calls)
        )


def analyze(root: Path, sources: Sequence[Source], compiler: Compiler) -> SemanticModel:
    return Resolver(root, sources, compiler).analyze()
