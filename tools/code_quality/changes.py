"""Changed/current scope composition. Component owners run regressions once.

Runtime imports, historical deletion closure and complete architecture coverage
are unsupported. The runner must verify checkout/index consistency before planning.
"""

import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from grimp.exceptions import GrimpException

from .change_context import compiler_context
from .change_inputs import RANGES as RANGES
from .change_inputs import Stage as Stage
from .change_inputs import resolve_inputs
from .impact import current_graph, module_name
from .native_impact import affected as native_affected


@dataclass(frozen=True)
class Plan:
    changed: tuple[str, ...]
    python: tuple[str, ...]
    format_files: tuple[str, ...]
    boundaries: bool
    metrics: bool
    base: str | None
    head: str | None
    boundary_files: tuple[str, ...] = ()
    tree: str | None = None
    native: tuple[str, ...] = ()


def build_plan(root: Path, stage: Stage, environment: Mapping[str, str]) -> Plan:
    """Preserve range seeds and current consumers; never certify architecture rules.

    Unproved Python deletions/renames fail COV002. Stubs invalidate typing globally.
    main.py conservatively consumes app modules. This API selects static checks.
    """
    try:
        inputs = resolve_inputs(root, stage, environment)
        context = compiler_context(inputs)
        changed, existing = inputs.changed, inputs.existing
        actual = changed & existing
        python_sources = {path for path in existing if path.endswith('.py')}
        changed_python = actual & python_sources
        python = set(actual)
        removed = {path for path in changed if path.endswith('.py')} - existing
        if removed:
            raise ValueError(
                'unproved affected scope for removed Python input: '
                + ', '.join(sorted(removed))
            )
        if changed_python:
            graph = current_graph(inputs.root, inputs.tree)
            required = python_sources - {'main.py'}
            sources = {module_name(path): path for path in required}
            if len(sources) != len(required) or not sources.keys() <= graph.modules:
                raise ValueError('native graph omits required Python source')
            affected: set[str] = set()
            for path in changed_python - {'main.py'}:
                name = module_name(path)
                affected |= {name} | graph.find_downstream_modules(
                    name, as_package=path.endswith('/__init__.py')
                )
                if path.endswith('/__init__.py'):
                    affected |= graph.find_descendants(name)
            python |= {sources[name] for name in affected & sources.keys()}
        app = {path for path in python_sources if path.startswith('src/')}
        boundary_files = app if context.boundaries else python & app
        if python & app and 'main.py' in existing:
            python.add('main.py')
        if context.types:
            python |= existing
        if (context.types or context.boundaries) and not app:
            raise ValueError('invalidated canonical application context is empty')
        return Plan(
            tuple(sorted(changed)),
            tuple(sorted(python)),
            tuple(sorted(existing if context.style else actual)),
            bool(boundary_files),
            context.runtime
            or any(path.startswith('tools/code-quality/') for path in changed)
            or any(
                path.endswith(('.py', '.mjs', '.js', '.ts', '.tsx', '.jsx'))
                for path in changed
            ),
            inputs.base,
            inputs.head,
            tuple(sorted(boundary_files)),
            inputs.tree,
            native_affected(inputs, context.runtime),
        )
    except (
        OSError,
        ValueError,
        KeyError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        GrimpException,
    ) as error:
        raise ValueError('COV002: ' + str(error)) from error
