"""Git-selected inputs; filesystem execution consistency belongs to the runner."""

import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .gate import references
from .git_environment import isolated_environment

Stage = Literal['commit', 'push', 'ci', 'manual']
ROOTS = ('src/', 'tests/', 'tools/', 'typings/')
RANGES = {
    'push': ('PRE_COMMIT_FROM_REF', 'PRE_COMMIT_TO_REF'),
    'ci': ('QUALITY_BASE', 'QUALITY_HEAD'),
}


@dataclass(frozen=True)
class Inputs:
    root: Path
    changed: frozenset[str]
    existing: frozenset[str]
    base: str | None
    head: str | None
    tree: str | None


def git(root: Path, *arguments: str) -> str:
    return (
        subprocess.check_output(
            ['git', '-C', str(root), *arguments],
            env=isolated_environment(),
            stderr=subprocess.PIPE,
        )
        .decode()
        .strip('\n')
    )


def paths(root: Path, *arguments: str) -> set[str]:
    return set(git(root, *arguments).split('\0')) - {''}


def resolve_inputs(root: Path, stage: Stage, environment: Mapping[str, str]) -> Inputs:
    root = root.resolve()
    if Path(git(root, 'rev-parse', '--show-toplevel')).resolve() != root:
        raise ValueError('selector must run at the checkout root')
    base = head = None
    unindexed: set[str] = set()
    if stage in ('commit', 'manual'):
        changed = paths(
            root, 'diff', '--cached', '--name-only', '-z', '--no-renames', 'HEAD'
        )
        if stage == 'manual':
            changed |= paths(root, 'diff', '--name-only', '-z', '--no-renames')
        unindexed = {
            path
            for path in paths(root, 'ls-files', '--others', '-z')
            if path.startswith(ROOTS)
            and path.endswith(('.py', '.pyi', '.mjs', '.d.ts'))
        }
        changed |= unindexed
        files = paths(root, 'ls-files', '-z') | unindexed
        tree = None if stage == 'manual' or unindexed else git(root, 'write-tree')
    else:
        requested = references({key: environment.get(key, '') for key in RANGES[stage]})
        if requested is None:
            raise ValueError('submitted range is required')
        base, head = (
            git(root, 'rev-parse', '--verify', ref + '^{commit}') for ref in requested
        )
        revisions = git(root, 'rev-list', base + '..' + head).splitlines()
        if not revisions or head != git(root, 'rev-parse', 'HEAD'):
            raise ValueError('submitted range is empty or not the current checkout')
        changed = paths(
            root,
            'log',
            '--root',
            '--diff-merges=separate',
            '--format=',
            '--name-only',
            '-z',
            '--no-renames',
            base + '..' + head,
        )
        files = paths(root, 'ls-tree', '-r', '--name-only', '-z', head)
        tree = git(root, 'rev-parse', head + '^{tree}')
    existing = {
        path
        for path in files
        if path.endswith(('.py', '.pyi')) and (root / path).is_file()
    }
    return Inputs(root, frozenset(changed), frozenset(existing), base, head, tree)
