"""Git and physical native input identities for the selected checkout."""

import hashlib
import subprocess
from pathlib import Path

from tools.architecture.native_sources import source_inputs

from .change_inputs import Inputs, paths
from .git_environment import isolated_environment

PACKAGE = 'node_modules/.pnpm/typescript@5.9.3/node_modules/typescript'
TOOL = 'tools/code_quality/native_impact.mjs'
NATIVE_TOOLS = {
    TOOL,
    'tools/code_quality/native_impact_context.mjs',
    'tools/code_quality/native_impact_projection.mjs',
}


def native_source(path: str) -> bool:
    return path in NATIVE_TOOLS or (
        path.startswith('tools/architecture/native_')
        and path.endswith(('.mjs', '.d.ts'))
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover(inputs: Inputs) -> tuple[str, ...]:
    root = inputs.root
    catalog = (
        paths(root, 'ls-tree', '-r', '--name-only', '-z', inputs.tree)
        if inputs.tree
        else paths(root, 'ls-files', '-z') | paths(root, 'ls-files', '--others', '-z')
    )
    expected = {name for name in catalog if native_source(name)}
    found = {
        path.relative_to(root).as_posix()
        for path in (root / 'tools/architecture').rglob('native_*')
        if path.is_file() and native_source(path.relative_to(root).as_posix())
    }
    found.update(name for name in NATIVE_TOOLS if (root / name).is_file())
    if found != expected:
        raise ValueError(
            'COV002: intended native discovery is empty or differs from Git'
        )
    source_inputs(root, tuple(sorted(expected)))
    for name in expected:
        path = root / name
        if path.is_symlink():
            raise ValueError('COV002: native input escapes scope: ' + name)
    if inputs.tree:
        subprocess.run(
            ['git', 'diff', '--exit-code', inputs.tree, '--', *sorted(expected)],
            cwd=root,
            env=isolated_environment(),
            capture_output=True,
            check=True,
        )
    return tuple(sorted(expected))


def request_inputs(
    root: Path, sources: tuple[str, ...]
) -> tuple[dict[str, str], dict[str, str]]:
    records = {item.path: item.sha256 for item in source_inputs(root, sources)}
    configuration = {
        str(path): digest(path)
        for name in sources
        for directory in (root / name).parents
        if directory.is_relative_to(root)
        and (path := directory / 'package.json').is_file()
    }
    return records, configuration
