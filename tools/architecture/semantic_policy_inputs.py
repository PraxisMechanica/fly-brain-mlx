import hashlib
from pathlib import Path, PurePosixPath

from .semantic_policy_records import Binding, Input
from .semantic_policy_schema import require
from .symbols import Symbol


def exact_path(root: Path, name: str) -> Path:
    path = PurePosixPath(name)
    require(
        all(
            (
                not path.is_absolute(),
                path.as_posix() == name,
                '..' not in path.parts,
                bool(path.parts),
                not set(name) & set('\\*?[]\x00'),
            )
        ),
        'input path is not exact and relative: ' + name,
    )
    result = root / name
    require(
        all((result.resolve() == result, result.resolve().is_relative_to(root))),
        'input uses symlink or escapes root: ' + name,
    )
    return result


def verify_input(root: Path, item: Input) -> str:
    path = exact_path(root, item.path)
    actual = hashlib.sha256(read_bytes(path)).hexdigest()
    require(actual == item.sha256, 'input hash changed: ' + item.path)
    return actual


def read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as error:
        raise ValueError(
            'COV002: semantic policy input missing: ' + str(path)
        ) from error


def verify_anchor(root: Path, binding: Binding, symbol: Symbol) -> None:
    anchor = binding.anchor
    location = symbol.location
    label = (
        f'{binding.symbol.path}:{location.line}:{location.column} '
        f'[{binding.symbol.context}:{binding.symbol.qualified_name}:'
        f'{binding.symbol.native_kind}:{binding.symbol.occurrence}]'
    )
    require(
        (
            anchor.source_sha256,
            anchor.line,
            anchor.column,
            anchor.end_line,
            anchor.end_column,
        )
        == (
            symbol.provenance.sha256,
            location.line,
            location.column,
            location.end_line,
            location.end_column,
        ),
        'native hash/UTF16 anchor differs: ' + label,
    )
    path = Path(symbol.provenance.path)
    content = read_bytes(path)
    require(
        hashlib.sha256(content).hexdigest() == anchor.source_sha256,
        'native source changed: ' + str(path),
    )
    if symbol.provenance.project_path is not None:
        require(
            path.resolve() == exact_path(root, binding.symbol.path).resolve(),
            'native source path differs',
        )
    try:
        lines = content.decode('utf-8-sig').splitlines()
    except UnicodeError as error:
        raise ValueError('COV002: native source is not UTF8: ' + label) from error
    require(
        all((anchor.end_line >= anchor.line, anchor.end_line <= max(1, len(lines)))),
        'native anchor line range is invalid',
    )
    for line, column in (
        (anchor.line, anchor.column),
        (anchor.end_line, anchor.end_column),
    ):
        encoded = (lines[line - 1] if lines else '').encode('utf-16-le')
        require(column * 2 <= len(encoded), 'native UTF16 column exceeds source')
        try:
            encoded[: column * 2].decode('utf-16-le')
        except UnicodeError as error:
            raise ValueError(
                'COV002: native UTF16 anchor splits a codepoint'
            ) from error
    require(
        (anchor.end_line, anchor.end_column) >= (anchor.line, anchor.column),
        'native anchor range is reversed',
    )
