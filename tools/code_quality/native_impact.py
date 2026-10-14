"""Scoped native consumer selection and executable command composition."""

import json
import subprocess
from pathlib import Path

from tools.architecture.compiler import object_value
from tools.architecture.native_types_schema import string

from .change_inputs import Inputs
from .native_impact_inputs import NATIVE_TOOLS, native_source, request_inputs
from .native_impact_inputs import PACKAGE as PACKAGE
from .native_impact_inputs import TOOL as TOOL
from .native_impact_inputs import digest as digest
from .native_impact_inputs import discover as discover
from .native_impact_records import facts

FLAGS = (
    '--allowJs',
    '--checkJs',
    '--noEmit',
    '--strict',
    '--noUncheckedIndexedAccess',
    '--exactOptionalPropertyTypes',
    '--target',
    'ES2022',
    '--module',
    'NodeNext',
    '--moduleResolution',
    'NodeNext',
)
CONTEXT = NATIVE_TOOLS | {
    'tools/code_quality/native_impact.py',
    'tools/code_quality/native_impact_inputs.py',
    'tools/code_quality/native_impact_records.py',
    'tools/code_quality/check.py',
    'tools/code_quality/changes.py',
    'tools/architecture/native_sources_compiler.mjs',
}


def dependencies(
    root: Path, sources: tuple[str, ...]
) -> tuple[dict[str, set[str]], set[str]]:
    records, configuration = request_inputs(root, sources)
    request = {
        'schema': 1,
        'root': str(root),
        'package': str(root / PACKAGE),
        'dependencies': str((root / 'node_modules').resolve()),
        'flags': FLAGS,
        'sources': records,
        'configuration': configuration,
    }
    result = subprocess.run(
        ['node', str(Path(__file__).with_suffix('.mjs'))],
        cwd=root,
        input=json.dumps(request),
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    response = object_value(json.loads(result.stdout))
    if result.returncode or 'error' in response:
        raise ValueError(string(response.get('error')))
    graph, globals_, reads = facts(
        response, root, sources, records, configuration, FLAGS
    )
    for name, expected in reads.items():
        if digest(Path(name)) != expected:
            raise ValueError('COV002: native compiler input changed: ' + name)
    return graph, globals_


def affected(inputs: Inputs, runtime: bool) -> tuple[str, ...]:
    changed = {name for name in inputs.changed if native_source(name)}
    invalidated = (
        runtime
        or bool(inputs.changed & CONTEXT)
        or any(name.endswith('package.json') for name in inputs.changed)
    )
    if not changed and not invalidated:
        return ()
    sources = discover(inputs)
    if not changed <= set(sources):
        raise ValueError('COV002: removed native source has no checked dependent scope')
    graph, globals_ = dependencies(inputs.root, sources)
    selected = (
        set(sources)
        if invalidated or changed & globals_
        else changed | {name for name, required in graph.items() if required & changed}
    )
    return tuple(sorted(selected | globals_))


def commands(
    changed: tuple[str, ...], selected: tuple[str, ...]
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    native_changed = tuple(path for path in changed if native_source(path))
    native = tuple(path for path in native_changed if Path(path).is_file())
    if len(native) != len(native_changed):
        raise ValueError('COV002: removed native source has no checked dependent scope')
    if not set(native) <= set(selected):
        raise ValueError('COV002: changed native source has no checked dependent scope')
    result: list[tuple[str, tuple[str, ...]]] = (
        [('native-types', ('node', PACKAGE + '/bin/tsc', *FLAGS, *selected))]
        if selected
        else []
    )
    result.extend(
        ('native-syntax', ('node', '--check', path))
        for path in native
        if path.endswith('.mjs')
    )
    return tuple(result)
