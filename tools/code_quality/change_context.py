"""TOML/native compiler context invalidation, independent of file-impact traversal."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

import tomli

from .change_inputs import Inputs, git

RUNTIME = {'uv.lock', 'package.json', 'pnpm-lock.yaml'}
ROOT_CONTEXT = ('project', 'dependency-groups', 'build-system')
TOOL_CONTEXT = ('uv', 'pyright', 'ruff', 'importlinter')


@dataclass(frozen=True)
class Invalidation:
    runtime: bool
    types: bool
    style: bool
    boundaries: bool


def tool(configuration: Mapping[str, object]) -> dict[object, object]:
    value = configuration.get('tool', {})
    if not isinstance(value, dict):
        raise ValueError('checking tool configuration is not a TOML table')
    return cast(dict[object, object], value)


def compiler_context(inputs: Inputs) -> Invalidation:
    before: dict[str, object] = tomli.loads(
        git(inputs.root, 'show', (inputs.base or 'HEAD') + ':pyproject.toml')
    )
    after: dict[str, object] = tomli.loads((inputs.root / 'pyproject.toml').read_text())
    before_tool, after_tool = tool(before), tool(after)
    root_changed = any(before.get(key) != after.get(key) for key in ROOT_CONTEXT)
    tool_changed = {
        key for key in TOOL_CONTEXT if before_tool.get(key) != after_tool.get(key)
    }
    runtime = bool(inputs.changed & RUNTIME) or root_changed or 'uv' in tool_changed
    return Invalidation(
        runtime,
        runtime
        or 'pyright' in tool_changed
        or any(
            path.startswith('typings/') and path.endswith('.pyi')
            for path in inputs.changed
        ),
        runtime or 'ruff' in tool_changed,
        runtime
        or 'importlinter' in tool_changed
        or 'tools/architecture/neutral_import_contract.py' in inputs.changed,
    )
