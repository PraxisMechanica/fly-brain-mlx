import json
import shutil
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from .git_environment import isolated_environment

MANAGED_ROOTS = ('logs',)
OUTPUT_ROOTS = (*MANAGED_ROOTS, '.quality-reports', 'executions')
POLICY = 'tools/code_quality/retention.json'


@dataclass(frozen=True)
class RetainedPath:
    path: Path
    reason: str
    release_when: str


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate retention field: {key}')
        result[key] = value
    return result


def _object(value: object, fields: set[str]) -> Mapping[str, object]:
    if not isinstance(value, dict) or set(cast(dict[object, object], value)) != fields:
        raise ValueError('Retention policy has malformed or unknown fields')
    return cast(dict[str, object], value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Retention reason and release_when require nonempty text')
    return value.strip()


def _relative_path(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError('Retention path must be checkout-relative')
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or any(part in ('', '.', '..') for part in value.split('/'))
        or any(part.casefold() == '.git' for part in path.parts)
        or any(char in value for char in '\\*?[]')
        or value in OUTPUT_ROOTS
    ):
        raise ValueError(
            'Retention path cannot be absolute, traversal, Git metadata or a cleanup root'
        )
    return Path(*path.parts)


def _without_symlinks(root: Path, relative: Path) -> None:
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f'Refusing a symlinked retention path: {relative}')


def read_retention(root: Path) -> tuple[RetainedPath, ...]:
    _without_symlinks(root, Path(POLICY))
    data = _object(
        cast(
            object,
            json.loads((root / POLICY).read_text(), object_pairs_hook=_unique_object),
        ),
        {'version', 'exceptions'},
    )
    if type(data['version']) is not int or data['version'] != 1:
        raise ValueError('Unsupported retention policy version')
    if not isinstance(data['exceptions'], list):
        raise ValueError('Retention exceptions must be a list')
    retained: list[RetainedPath] = []
    for value in cast(list[object], data['exceptions']):
        entry = _object(value, {'path', 'reason', 'release_when'})
        relative = _relative_path(entry['path'])
        if any(
            relative.is_relative_to(old.path) or old.path.is_relative_to(relative)
            for old in retained
        ):
            raise ValueError(f'Duplicate or overlapping retention path: {relative}')
        _without_symlinks(root, relative)
        retained.append(
            RetainedPath(relative, _text(entry['reason']), _text(entry['release_when']))
        )
    return tuple(retained)


def _deletions(path: Path, retained: tuple[Path, ...]) -> list[Path]:
    if path in retained or not path.exists():
        return []
    if not any(saved.is_relative_to(path) for saved in retained):
        return [path]
    result: list[Path] = []
    for child in path.iterdir():
        if child.is_symlink() or not child.is_dir():
            if child not in retained:
                result.append(child)
        else:
            result.extend(_deletions(child, retained))
    return result


def clean_outputs(root: Path) -> None:
    if root.is_symlink():
        raise ValueError('Refusing a symlinked checkout root')
    root = root.resolve()
    entries = read_retention(root)
    tracked = set(
        subprocess.check_output(
            ['git', 'ls-files', '-z', '--', POLICY, *OUTPUT_ROOTS],
            cwd=root,
            env=isolated_environment(),
            text=True,
        ).split('\0')
    ) - {''}
    if POLICY not in tracked:
        raise ValueError('Retention policy must be indexed before cleanup')
    if tracked - {POLICY}:
        raise ValueError('Refusing to clean versioned generated files')
    retained = tuple(
        root / entry.path for entry in entries if entry.path.parts[0] in MANAGED_ROOTS
    )
    planned: list[Path] = []
    for name in OUTPUT_ROOTS:
        directory = root / name
        if directory.is_symlink():
            raise ValueError(f'Refusing to clean a symlinked {name} root')
        if directory.exists() and not directory.is_dir():
            raise ValueError(f'The {name} path must be a directory')
        if name in MANAGED_ROOTS:
            planned.extend(_deletions(directory, retained))
    for path in planned:
        if path.is_symlink() or not path.is_dir():
            path.unlink()
        else:
            shutil.rmtree(path)
