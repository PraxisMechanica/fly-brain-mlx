import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

import pytest

from tests.quality.support import PROJECT, git, repository, run
from tools.architecture.compiler import JsonValue, object_value
from tools.code_quality import native_impact as native
from tools.code_quality.change_inputs import Inputs
from tools.code_quality.native_impact_inputs import request_inputs

PREFIX = 'tools/architecture/'
PROVIDER = PREFIX + 'native_provider.mjs'
CONSUMER = PREFIX + 'native_consumer.mjs'
OTHER = PREFIX + 'native_other.mjs'
GLOBAL = PREFIX + 'native_global.d.ts'
MANIFEST = {'package.json': '{"type":"module"}\n'}


def write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    git(root, 'add', name)


def checkout(root: Path, sources: Mapping[str, str]) -> Path:
    repository(root)
    (root / 'node_modules').symlink_to(PROJECT / 'node_modules')
    for name, text in sources.items():
        write(root, name, text)
    git(root, 'commit', '-qm', 'Declare native source context')
    return root


def inputs(root: Path, *changed: str) -> Inputs:
    return Inputs(
        root, frozenset(changed), frozenset(), None, None, git(root, 'write-tree')
    )


def compiler(root: Path, sources: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return run(
        ['node', str(root / native.PACKAGE / 'bin/tsc'), *native.FLAGS, *sources], root
    )


@pytest.mark.parametrize(
    'provider,original,consumer,extra',
    (
        (
            PROVIDER,
            "export function value() { return 'text'; }\n",
            "import {value} from './native_provider.mjs'; value().toUpperCase();\n",
            {},
        ),
        (
            PROVIDER,
            "export function value() { return 'text'; }\n",
            "import {value} from './native_facade.mjs'; value().toUpperCase();\n",
            {
                PREFIX
                + 'native_facade.mjs': "export {value} from './native_provider.mjs';\n"
            },
        ),
        (
            PROVIDER,
            "export function value() { return 'text'; }\n",
            "/** @type {ReturnType<typeof import('./native_provider.mjs').value>} */\nconst value = 'text'; value.toUpperCase(); export {};\n",
            {},
        ),
        (
            GLOBAL,
            'declare namespace Contract { type Value = string; }\n',
            '/// <reference path="./native_global.d.ts" />\n/** @type {Contract.Value} */ const value = "text"; value.toUpperCase(); export {};\n',
            MANIFEST,
        ),
        (
            GLOBAL,
            'declare namespace Contract { type Value = string; }\n',
            '/** @type {Contract.Value} */ const value = "text"; value.toUpperCase(); export {};\n',
            MANIFEST,
        ),
        (
            GLOBAL,
            "declare module 'contract' { export type Value = string; }\n",
            '/** @type {import("contract").Value} */ const value = "text"; value.toUpperCase(); export {};\n',
            MANIFEST,
        ),
        (
            GLOBAL,
            'export {}; declare global { namespace Contract { type Value = string; } }\n',
            '/** @type {Contract.Value} */ const value = "text"; value.toUpperCase(); export {};\n',
            MANIFEST,
        ),
    ),
)
def test_real_unchanged_consumers_reject_changed_contract_and_repair(
    tmp_path: Path, provider: str, original: str, consumer: str, extra: dict[str, str]
) -> None:
    root = checkout(
        tmp_path,
        {
            provider: original,
            CONSUMER: consumer,
            OTHER: 'export const other = 1;\n',
            **extra,
        },
    )
    write(root, provider, original.replace("'text'", '1').replace('string', 'number'))
    selected = native.affected(inputs(root, provider), False)
    rejected = compiler(root, selected)
    weakened = compiler(root, (provider,))
    write(root, provider, original)
    repaired = compiler(root, selected)
    assert (
        CONSUMER in selected,
        rejected.returncode,
        'TS' in rejected.stdout,
        weakened.returncode,
        repaired.returncode,
    ) == (True, 2, True, 0, 0)


def test_cycles_literal_imports_and_close_unrelated_exclusion(tmp_path: Path) -> None:
    root = checkout(
        tmp_path,
        {
            PROVIDER: "import {other} from './native_facade.mjs'; export const value = other;\n",
            PREFIX
            + 'native_facade.mjs': "import './native_provider.mjs'; export const other = 1;\n",
            CONSUMER: "const module = await import('./native_provider.mjs'); export const value = module.value;\n",
            OTHER: 'export const value = 1;\n',
        },
    )
    selected = native.affected(inputs(root, PROVIDER), False)
    assert (selected, compiler(root, selected).returncode) == (
        tuple(sorted((PROVIDER, PREFIX + 'native_facade.mjs', CONSUMER))),
        0,
    )


@pytest.mark.parametrize(
    'source',
    (
        "export const value = import('./missing.mjs');\n",
        "const name = './native_provider.mjs'; export const value = import(name);\n",
        "export {value} from './missing.mjs';\n",
        "/** @type {import('./missing.mjs').Value} */ export const value = 1;\n",
        '/// <reference path="./missing.d.ts" />\nexport const value = 1;\n',
        '/// <reference types="missing" />\nexport const value = 1;\n',
        'export function value( {\n',
        "import './hidden.mjs'; export const value = 1;\n",
    ),
)
def test_unproved_module_reference_parse_and_discovery_forms_fail(
    tmp_path: Path, source: str
) -> None:
    root = checkout(
        tmp_path,
        {
            PROVIDER: 'export const value = 1;\n',
            CONSUMER: source,
            PREFIX + 'hidden.mjs': 'export const hidden = 1;\n',
        },
    )
    with pytest.raises(ValueError, match='COV002'):
        native.affected(inputs(root, PROVIDER), False)


@pytest.mark.parametrize(
    'seed,runtime',
    (
        ('uv.lock', True),
        ('package.json', False),
        ('tools/code_quality/check.py', False),
        ('tools/code_quality/changes.py', False),
        ('tools/code_quality/native_impact.py', False),
        ('tools/code_quality/native_impact_inputs.py', False),
        ('tools/code_quality/native_impact_records.py', False),
        (native.TOOL, False),
        ('tools/code_quality/native_impact_context.mjs', False),
        ('tools/code_quality/native_impact_projection.mjs', False),
        (PREFIX + 'native_sources_compiler.mjs', False),
    ),
)
def test_actual_runtime_and_selector_context_changes_invalidate_all_native_roots(
    tmp_path: Path, seed: str, runtime: bool
) -> None:
    sources = {
        PROVIDER: 'export const value = 1;\n',
        OTHER: 'export const other = 1;\n',
        native.TOOL: 'export const tool = 1;\n',
        'tools/code_quality/native_impact_context.mjs': 'export const context = 1;\n',
        'tools/code_quality/native_impact_projection.mjs': 'export const projection = 1;\n',
        PREFIX + 'native_sources_compiler.mjs': 'export const compiler = 1;\n',
    }
    root = checkout(tmp_path, sources)
    assert native.affected(inputs(root, seed), runtime) == tuple(sorted(sources))


def test_missing_empty_omitted_and_escaping_scope_is_not_pass(tmp_path: Path) -> None:
    root = checkout(tmp_path, MANIFEST)
    with pytest.raises(ValueError, match='empty'):
        native.affected(inputs(root), True)
    write(root, PROVIDER, 'export const value = 1;\n')
    selected = inputs(root, PROVIDER)
    (root / PROVIDER).unlink()
    with pytest.raises(ValueError, match='discovery'):
        native.affected(selected, False)
    (root / PROVIDER).symlink_to(root / 'calculation.py')
    with pytest.raises(ValueError, match='escapes'):
        native.affected(selected, False)
    (root / PROVIDER).unlink()
    write(root, PROVIDER, 'export const value = 1;\n')
    selected = inputs(root, PROVIDER)
    (root / OTHER).write_text('export const other = 1;\n')
    with pytest.raises(ValueError, match='discovery'):
        native.affected(selected, False)


@pytest.mark.parametrize(
    'field,value',
    (
        ('schema', 2),
        ('schema', True),
        ('schema', 1.0),
        ('version', 'unknown'),
        ('flags', []),
        ('graph', {}),
        ('globals', ['outside']),
        ('inputs', {}),
    ),
)
def test_changed_or_omitted_native_facts_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: JsonValue
) -> None:
    root = checkout(tmp_path, {PROVIDER: 'export const value = 1;\n'})
    original = native.subprocess.run

    def changed(
        arguments: list[str],
        *,
        cwd: Path,
        input: str,
        capture_output: Literal[True],
        text: Literal[True],
        timeout: int,
        check: Literal[False],
    ) -> subprocess.CompletedProcess[str]:
        result = original(
            arguments,
            cwd=cwd,
            input=input,
            capture_output=capture_output,
            text=text,
            timeout=timeout,
            check=check,
        )
        response = object_value(json.loads(result.stdout))
        response[field] = value
        return subprocess.CompletedProcess(
            result.args, result.returncode, json.dumps(response), result.stderr
        )

    monkeypatch.setattr(native.subprocess, 'run', changed)
    with pytest.raises(ValueError):
        native.dependencies(root, (PROVIDER,))


def test_unchanged_consumer_is_lost_when_dependency_selection_is_weakened(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = checkout(
        tmp_path,
        {
            PROVIDER: 'export function value() { return 1; }\n',
            CONSUMER: "import {value} from './native_provider.mjs'; value().toUpperCase();\n",
        },
    )
    selected = native.affected(inputs(root, PROVIDER), False)

    def incomplete(
        _root: Path, sources: tuple[str, ...]
    ) -> tuple[dict[str, set[str]], set[str]]:
        return {name: {name} for name in sources}, set()

    monkeypatch.setattr(native, 'dependencies', incomplete)
    weakened = native.affected(inputs(root, PROVIDER), False)
    assert (
        CONSUMER in selected,
        CONSUMER in weakened,
        compiler(root, selected).returncode,
        compiler(root, weakened).returncode,
    ) == (True, False, 2, 0)


@pytest.mark.parametrize('selected', ((), (PROVIDER,)))
def test_incomplete_command_scope_cannot_skip_a_changed_native_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selected: tuple[str, ...]
) -> None:
    checkout(
        tmp_path,
        {PROVIDER: 'export const value = 1;\n', CONSUMER: 'export const value = 1;\n'},
    )
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match='COV002.*dependent scope'):
        native.commands((PROVIDER, CONSUMER), selected)


@pytest.mark.parametrize(
    'fault,weaken,expected',
    (
        ('text', False, 'COV002'),
        ('hash', False, 'COV002'),
        ('hash', True, 'accepted'),
    ),
)
def test_swallowed_native_text_and_hash_failures_remain_failed(
    tmp_path: Path, fault: str, weaken: bool, expected: str
) -> None:
    root = checkout(tmp_path, {PROVIDER: 'export const value = 1;\n'})
    records, configuration = request_inputs(root, (PROVIDER,))
    request = {
        'schema': 1,
        'root': str(root),
        'package': str(root / native.PACKAGE),
        'dependencies': str((root / 'node_modules').resolve()),
        'flags': native.FLAGS,
        'sources': records,
        'configuration': configuration,
    }
    script = f"""import {{readFileSync,writeFileSync}} from 'node:fs';
import {{loadCompiler}} from {json.dumps(str(PROJECT / 'tools/architecture/native_sources_compiler.mjs'))};
import {{createContext,verifyInputs}} from {json.dumps(str(PROJECT / 'tools/code_quality/native_impact_context.mjs'))};
const request = {json.dumps(request)};
const fault = {json.dumps(fault)}, weaken = {json.dumps(weaken)}, target = {json.dumps(str(root / PROVIDER))};
const original = readFileSync(target, 'utf8');
const ts = loadCompiler(request.package);
const read = ts.sys.readFile;
if (fault === 'text') ts.sys.readFile = (name, encoding) => {{
  const value = read(name, encoding);
  return name === target ? value + '\\n// changed host text' : value;
}};
try {{
  const context = createContext(request);
  writeFileSync(target, original + '\\n// changed hash');
  try {{ context.host.readFile(target); }} catch {{ }}
  writeFileSync(target, original);
  if (weaken) context.readFailures.length = 0;
  verifyInputs(context);
  console.log('accepted');
}} catch (error) {{ console.log(String(error)); }}
"""
    result = subprocess.run(
        ['node', '--input-type=module'],
        input=script,
        text=True,
        capture_output=True,
        cwd=root,
        timeout=60,
        check=False,
    )
    assert (result.returncode, expected in result.stdout) == (0, True)


def test_actual_tool_sdk_type_import_and_loader_declaration_context_are_observed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_paths: set[Path] = set()
    original = native.digest

    def observed(path: Path) -> str:
        read_paths.add(path.resolve())
        return original(path)

    monkeypatch.setattr(native, 'digest', observed)
    selected = Inputs(PROJECT, frozenset({native.TOOL}), frozenset(), None, None, None)
    sources = native.discover(selected)
    graph, globals_ = native.dependencies(PROJECT, sources)
    assert (
        native.TOOL in sources,
        PREFIX + 'native_sources_compiler.mjs' in graph[native.TOOL],
        PREFIX + 'native_types_node.d.ts' in graph[PREFIX + 'native_types_loading.mjs'],
        PREFIX + 'native_types_node.d.ts' in globals_,
        (PROJECT / native.PACKAGE / 'lib/typescript.d.ts').resolve() in read_paths,
    ) == (True, True, True, True, True)
