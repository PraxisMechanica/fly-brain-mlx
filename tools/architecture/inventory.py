import ast
import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class Declaration:
    name: str
    kind: str
    line: int


@dataclass(frozen=True)
class Source:
    path: str
    sha256: str
    declarations: tuple[Declaration, ...]


@dataclass(frozen=True)
class Ownership:
    owner: str
    role: str
    declarations: tuple[str, ...]
    artifact_sha256: str | None = None


def declarations(tree: ast.Module) -> tuple[Declaration, ...]:
    result: list[Declaration] = []

    def names(target: ast.expr) -> tuple[str, ...]:
        if isinstance(target, ast.Name):
            return (target.id,)
        if isinstance(target, (ast.Tuple, ast.List)):
            return tuple(name for item in target.elts for name in names(item))
        return ()

    def walk(node: ast.AST, scope: str = '', values: bool = True) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = scope + '.' + child.name if scope else child.name
                result.append(Declaration(name, type(child).__name__, child.lineno))
                walk(child, name, isinstance(child, ast.ClassDef))
            elif values and isinstance(child, (ast.Assign, ast.AnnAssign)):
                targets = (
                    child.targets if isinstance(child, ast.Assign) else (child.target,)
                )
                for target in targets:
                    for identifier in names(target):
                        name = scope + '.' + identifier if scope else identifier
                        result.append(Declaration(name, 'value', child.lineno))
            else:
                walk(child, scope, values)

    walk(tree)
    return tuple(result)


def discover(root: Path, source_roots: Sequence[str]) -> tuple[Source, ...]:
    root = root.resolve()
    paths: set[Path] = set()
    for source_root in source_roots:
        directory = root / source_root
        if not directory.exists():
            raise ValueError('COV002: missing source root: ' + source_root)
        if not directory.resolve().is_relative_to(root):
            raise ValueError('COV002: source root escapes workspace: ' + source_root)
        if directory.is_file():
            if directory.suffix not in ('.py', '.pyi'):
                raise ValueError('COV002: unsupported Python source: ' + source_root)
            found = {directory}
        else:
            if any(
                item.is_symlink() and item.is_dir() for item in directory.rglob('*')
            ):
                raise ValueError(
                    'COV002: unsupported source directory symlink: ' + source_root
                )
            found = {
                path
                for pattern in ('*.py', '*.pyi')
                for path in directory.rglob(pattern)
            }
        if not found:
            raise ValueError('COV002: intended source scope is empty: ' + source_root)
        paths.update(found)
    if not paths:
        raise ValueError('COV002: intended source scope is empty')
    result: list[Source] = []
    for path in sorted(paths):
        relative = path.relative_to(root).as_posix()
        if not path.resolve().is_relative_to(root):
            raise ValueError('COV002: source escapes workspace: ' + relative)
        try:
            content = path.read_bytes()
            tree = ast.parse(content, filename=relative)
        except SyntaxError as error:
            raise ValueError(
                f'COV002: {relative}:{error.lineno}: parse failed: {error.msg}'
            ) from error
        except (OSError, UnicodeError, ValueError) as error:
            raise ValueError(
                'COV002: source could not be parsed: ' + relative
            ) from error
        result.append(
            Source(relative, hashlib.sha256(content).hexdigest(), declarations(tree))
        )
    return tuple(result)


def reconcile(
    sources: Sequence[Source], ownership: Mapping[str, Ownership]
) -> tuple[Finding, ...]:
    if not sources:
        raise ValueError('COV002: ownership reconciliation scope is empty')
    findings: list[Finding] = []
    discovered = {source.path for source in sources}
    for path in sorted(ownership.keys() - discovered):
        findings.append(
            Finding('COV001', path, 1, 'Mapped source is absent from discovery')
        )
    for source in sources:
        expected = ownership.get(source.path)
        if expected is None:
            findings.append(
                Finding('COV001', source.path, 1, 'Source has no reviewed owner/role')
            )
            continue
        if not expected.owner.strip() or not expected.role.strip():
            findings.append(
                Finding('COV001', source.path, 1, 'Source owner/role is empty')
            )
        if (
            expected.artifact_sha256 is not None
            and expected.artifact_sha256 != source.sha256
        ):
            findings.append(
                Finding('COV001', source.path, 1, 'Frozen artifact provenance changed')
            )
        observed = {item.name: item for item in source.declarations}
        registered = set(expected.declarations)
        for name in sorted(observed.keys() - registered):
            item = observed[name]
            findings.append(
                Finding(
                    'COV001',
                    source.path,
                    item.line,
                    'Unclassified declaration: ' + name,
                )
            )
        for name in sorted(registered - observed.keys()):
            findings.append(
                Finding(
                    'COV001', source.path, 1, 'Mapped declaration is absent: ' + name
                )
            )
    return tuple(findings)
