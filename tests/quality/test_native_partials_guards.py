import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tests.quality.native_partial_support import DIRECT, changed_bridge, partials
from tests.quality.native_type_support import PACKAGE, write
from tests.quality.support import PROJECT
from tools.architecture import native_partials
from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.inventory import Source
from tools.architecture.native_partials import (
    PartialConstructionReport,
    inspect_partials,
    parse_partial_report,
)
from tools.architecture.native_types import values


def test_bad_keyword_is_rejected_and_repair_keeps_exact_constructor(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError, match='COV002: native partial type is incomplete or erroneous'
    ):
        partials(tmp_path, {'source.py': DIRECT.replace('scale=2', 'scale="bad"')})
    repaired = partials(tmp_path, {'source.py': DIRECT})
    assert (
        repaired.typing.types[repaired.constructions[0].constructor_signature].name
        == 'functools.partial.__new__'
    )


@pytest.mark.parametrize('capture', ['*values', '**keywords'])
def test_unpacked_capture_without_native_residual_shape_fails_closed(
    tmp_path: Path, capture: str
) -> None:
    text = DIRECT.replace(
        'job = partial(score, scale=2)',
        f'values = (3,)\nkeywords = {{"scale": 2}}\njob = partial(score, {capture})',
    )
    with pytest.raises(ValueError, match='COV002:.*native partial residual shape'):
        partials(tmp_path, {'source.py': text})


@pytest.mark.parametrize(
    'case',
    [
        'source_empty',
        'construction_empty',
        'node_missing',
        'bridge_missing',
        'package_changed',
        'dts_missing',
    ],
)
def test_required_tool_and_scope_inputs_fail_closed(tmp_path: Path, case: str) -> None:
    sources = write(tmp_path, {'source.py': DIRECT})
    package = PACKAGE
    node = 'node'
    bridge = PROJECT / 'tools/architecture/native_partials.mjs'
    if case == 'source_empty':
        sources = ()
    elif case == 'construction_empty':
        sources = write(
            tmp_path,
            {
                'source.py': 'def partial(value: int) -> int:\n    return value\nresult = partial(3)\n'
            },
        )
    elif case == 'node_missing':
        node = 'missing-native-partial-node'
    elif case == 'bridge_missing':
        bridge = tmp_path / 'native_partials.mjs'
    elif case == 'package_changed':
        package = tmp_path / 'package'
        package.mkdir()
        (package / 'package.json').write_text(json.dumps({'version': 'changed'}))
    else:
        bridge = changed_bridge(
            tmp_path / 'bridge', 'native_partials.mjs', 'const request', 'const request'
        )
        (bridge.parent / 'native_partials_api.d.ts').unlink()
    with pytest.raises(ValueError, match='COV002:'):
        inspect_partials(tmp_path, sources, package, node=node, bridge=bridge)


def test_changed_and_missing_discovered_source_are_rejected(tmp_path: Path) -> None:
    sources = write(tmp_path, {'source.py': DIRECT})
    (tmp_path / 'source.py').write_text(DIRECT.replace('scale=2', 'scale=3'))
    with pytest.raises(ValueError, match='COV002: native partial source'):
        inspect_partials(tmp_path, sources, PACKAGE)
    (tmp_path / 'source.py').unlink()
    with pytest.raises(ValueError, match='COV002:'):
        inspect_partials(tmp_path, sources, PACKAGE)


def test_native_parse_error_rejects_without_python_ast_discovery(
    tmp_path: Path,
) -> None:
    text = b'from functools import partial\njob = partial(\n'
    (tmp_path / 'source.py').write_bytes(text)
    source = Source('source.py', hashlib.sha256(text).hexdigest(), ())
    with pytest.raises(ValueError, match='COV002: native partial source parse failed'):
        inspect_partials(tmp_path, (source,), PACKAGE)


def test_undiscovered_loaded_source_rejects_even_when_partial_is_valid(
    tmp_path: Path,
) -> None:
    (tmp_path / 'hidden.py').write_text(
        'def score(value: int, *, scale: int) -> int:\n    return value * scale\n'
    )
    with pytest.raises(
        ValueError, match='COV002: native type reached undiscovered first-party source'
    ):
        partials(
            tmp_path,
            {
                'source.py': 'from functools import partial\nfrom hidden import score\njob = partial(score, scale=2)\n'
            },
        )


@pytest.mark.parametrize('kind', ['source', 'artifact'])
def test_mid_analysis_mutation_rejects_source_and_bridge_inputs(
    tmp_path: Path, kind: str
) -> None:
    bridge = changed_bridge(
        tmp_path / 'bridge',
        'native_partials_context.mjs',
        'import { createHash }',
        "import { writeFileSync } from 'node:fs';\nimport { createHash }",
    )
    context = bridge.parent / 'native_partials_context.mjs'
    target = '[...sources.keys()][0]' if kind == 'source' else 'artifacts[0].path'
    context.write_text(
        context.read_text().replace(
            'source.verify();', f"writeFileSync({target}, 'changed'); source.verify();"
        )
    )
    with pytest.raises(
        ValueError, match='COV002:.*(source changed|bridge source changed)'
    ):
        partials(tmp_path / 'source', {'source.py': DIRECT}, bridge=bridge)


@pytest.mark.parametrize(
    'field',
    [
        'schema',
        'reference',
        'site',
        'native_flag',
        'callee_flag',
        'capture_flag',
        'location',
        'library',
        'declaration_input',
        'request',
        'artifact',
        'native_artifact',
        'native_artifact_empty',
        'input_duplicate',
        'duplicate',
    ],
)
def test_response_mutation_rejects_schema_graph_and_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    decoder = parse_partial_report

    def mutated(value: JsonValue) -> PartialConstructionReport:
        response = object_value(value)
        file = object_value(values(response['files'])[0])
        construction = object_value(values(file['constructions'])[0])
        wrapped = object_value(construction['wrapped'])
        index = construction['constructor_signature']
        assert isinstance(index, int)
        mutations: dict[str, tuple[dict[str, JsonValue], str, JsonValue]] = {
            'schema': (construction, 'runtime_target', 'guessed'),
            'reference': (construction, 'residual_signature', 999999),
            'site': (response, 'sites', values(response['sites'])[:-1]),
            'native_flag': (construction, 'is_incomplete', True),
            'callee_flag': (construction, 'callee_type_errors', True),
            'capture_flag': (wrapped, 'type_errors', True),
            'location': (object_value(wrapped['location']), 'line', 1),
            'library': (
                object_value(values(response['types'])[index]),
                'name',
                'other.partial.__new__',
            ),
            'declaration_input': (
                object_value(values(wrapped['declarations'])[0]),
                'sha256',
                'changed',
            ),
            'request': (response, 'request_sha256', 'changed'),
            'artifact': (response, 'bridge_sources', []),
            'native_artifact': (
                object_value(response['artifacts']),
                'dist/vendor.js',
                'changed',
            ),
            'native_artifact_empty': (response, 'artifacts', {}),
            'input_duplicate': (
                response,
                'inputs',
                [*values(response['inputs']), values(response['inputs'])[0]],
            ),
            'duplicate': (file, 'constructions', [construction, construction]),
        }
        target, key, replacement = mutations[field]
        target[key] = replacement
        return decoder(response)

    monkeypatch.setattr(native_partials, 'parse_partial_report', mutated)
    with pytest.raises(ValueError, match='COV002:'):
        partials(tmp_path, {'source.py': DIRECT})


def test_weakening_library_identity_accepts_the_same_false_declaration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    decoder = parse_partial_report

    def forged(value: JsonValue) -> PartialConstructionReport:
        response = object_value(value)
        file = object_value(values(response['files'])[0])
        construction = object_value(values(file['constructions'])[0])
        index = construction['constructor_signature']
        assert isinstance(index, int)
        object_value(values(response['types'])[index])['name'] = 'other.partial.__new__'
        return decoder(response)

    monkeypatch.setattr(native_partials, 'parse_partial_report', forged)
    with pytest.raises(
        ValueError, match='COV002: native partial library identity differs'
    ):
        partials(tmp_path, {'source.py': DIRECT})

    def disabled(_report: PartialConstructionReport) -> None:
        return

    monkeypatch.setattr(
        'tools.architecture.native_partials_schema.validate_partial_report', disabled
    )
    weakened = partials(tmp_path, {'source.py': DIRECT})
    index = weakened.constructions[0].constructor_signature
    assert weakened.typing.types[index].name == 'other.partial.__new__'


def test_native_error_and_selection_guards_independently_reject_bad_capture(
    tmp_path: Path,
) -> None:
    bad = DIRECT.replace('scale=2', 'scale="bad"')
    with pytest.raises(
        ValueError, match='COV002: native partial type is incomplete or erroneous'
    ):
        partials(tmp_path / 'normal', {'source.py': bad})
    bridge = changed_bridge(
        tmp_path / 'bridge',
        'native_partials_projection.mjs',
        'if (flag(result.isIncomplete) || flag(result.typeErrors))',
        'if (false)',
    )
    with pytest.raises(
        ValueError,
        match='COV002: native partial constructor signatures is not an array',
    ):
        partials(tmp_path / 'native-weakened', {'source.py': bad}, bridge=bridge)


def test_checked_javascript_bridge_closure_and_native_syntax_pass() -> None:
    compiler = (
        PROJECT / 'node_modules/.pnpm/typescript@5.9.3/node_modules/typescript/bin/tsc'
    )
    bridge = PROJECT / 'tools/architecture/native_partials.mjs'
    result = subprocess.run(
        [
            'node',
            str(compiler),
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
            str(bridge),
            str(bridge.with_name('native_partials_api.d.ts')),
        ],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    for path in bridge.parent.glob('native_partials*.mjs'):
        checked = subprocess.run(
            ['node', '--check', str(path)], text=True, capture_output=True, check=False
        )
        assert checked.returncode == 0, checked.stdout + checked.stderr
