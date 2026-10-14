"""Explicit automatic pytest scope; typing invalidation is not test impact.

Native/process/resource consumption is not inferred from Python import edges.
Those behavior changes require explicitly selected focused test sources.
"""

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from tempfile import mkdtemp

import tomli

from .change_context import ROOT_CONTEXT, tool
from .change_inputs import Inputs, Stage, git, paths

APP = ('tests/unit/', 'tests/integration/')
QUALITY = 'tests/quality/'
CHECKERS = ('tools/architecture/', 'tools/code_quality/', QUALITY)
PROOF = 'tests/integration/test_session_proof_artifacts.py'


def delivery_inputs(inputs: Inputs, stage: Stage) -> Inputs:
    if stage != 'commit' or 'origin' not in git(inputs.root, 'remote').splitlines():
        return inputs
    base = git(inputs.root, 'merge-base', 'origin/main', 'HEAD')
    pending = paths(
        inputs.root,
        'log',
        '--root',
        '--diff-merges=separate',
        '--format=',
        '--name-only',
        '-z',
        '--no-renames',
        base + '..HEAD',
    )
    return replace(inputs, changed=inputs.changed | pending, base=base)


def application_context(inputs: Inputs) -> bool:
    runtime = bool(inputs.changed & {'uv.lock', 'main.py', 'tests/conftest.py'})
    if 'pyproject.toml' not in inputs.changed:
        return runtime
    before = tomli.loads(
        git(inputs.root, 'show', (inputs.base or 'HEAD') + ':pyproject.toml')
    )
    after = tomli.loads((inputs.root / 'pyproject.toml').read_text())
    before_tool, after_tool = tool(before), tool(after)
    return (
        runtime
        or any(before.get(key) != after.get(key) for key in ROOT_CONTEXT)
        or any(before_tool.get(key) != after_tool.get(key) for key in ('uv', 'pytest'))
    )


def select_tests(
    inputs: Inputs, impacts: Mapping[str, set[str]], stage: Stage
) -> tuple[str, ...]:
    if stage not in ('commit', 'ci'):
        return ()
    tests = {
        path
        for path in inputs.existing
        if path.startswith((*APP, QUALITY))
        and Path(path).name.startswith('test_')
        and path.endswith('.py')
    }
    app = {path for path in tests if path.startswith(APP)}
    affected = set[str]().union(*impacts.values())
    checker = set[str]().union(
        *(scope for seed, scope in impacts.items() if seed.startswith(CHECKERS))
    )
    selected = inputs.changed & tests | affected & app | checker & tests
    if application_context(inputs):
        selected |= app
    return tuple(sorted(selected - {PROOF}))


def commands(
    tests: tuple[str, ...], stage: Stage
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if stage not in ('commit', 'ci') or not tests:
        return ()
    return (('tests', ('python', '-m', 'pytest', '-q', '--ignore=' + PROOF, *tests)),)


def execution_arguments(
    name: str, arguments: tuple[str, ...], stage: Stage
) -> tuple[str, ...]:
    if name != 'tests':
        return arguments
    parent = Path('executions')
    parent.mkdir(exist_ok=True)
    return (*arguments, '--basetemp=' + mkdtemp(prefix=stage + '-tests-', dir=parent))
