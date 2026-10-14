import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from tests.quality.native_call_support import (
    BRIDGE,
    FUNCTION,
    OVERLOAD,
    calls,
    modified_bridge,
)
from tests.quality.native_type_support import PACKAGE, write
from tools.architecture import native_calls
from tools.architecture.compiler import JsonValue, object_value
from tools.architecture.inventory import Source
from tools.architecture.native_calls import (
    NativeCallReport,
    inspect_calls,
    parse_call_report,
)
from tools.architecture.native_types import NativeTypeReport, TypedSite, values


def test_argument_error_is_rejected_and_repair_preserves_target(tmp_path: Path) -> None:
    with pytest.raises(
        ValueError, match='COV002: native call type is incomplete or erroneous'
    ):
        calls(tmp_path, {'source.py': FUNCTION + 'result = score("wrong")\n'})
    report = calls(tmp_path, {'source.py': FUNCTION + 'result = score(1)\n'})
    assert report.signature(report.calls[0]).name == 'source.score'


@pytest.mark.parametrize(
    'definition',
    [
        'from typing import Any\ndef call(value: Any) -> int:\n    return value(1)\n',
        'def call(value):\n    return value(1)\n',
        'from typing import Any\ndef work(value: int) -> list[Any]:\n    return [value]\nresult = work(1)\n',
        'from typing import Any\ndef work(value: list[Any]) -> int:\n    return 1\nresult = work([1])\n',
    ],
)
def test_any_unknown_and_nested_dynamic_call_surfaces_fail_closed(
    tmp_path: Path, definition: str
) -> None:
    with pytest.raises(ValueError, match='COV002:'):
        calls(tmp_path, {'source.py': definition})


def test_erased_callable_factory_is_rejected_and_inferred_factory_repairs_it(
    tmp_path: Path,
) -> None:
    files = {
        'source.py': 'from typing import Callable\n'
        + FUNCTION
        + 'def factory() -> Callable[[int], int]:\n    return score\nresult = factory()(1)\n'
    }
    with pytest.raises(
        ValueError, match='COV002: native callable declaration is erased'
    ):
        calls(tmp_path, files)
    repaired = calls(
        tmp_path,
        {
            'source.py': FUNCTION
            + 'def factory():\n    return score\nresult = factory()(1)\n'
        },
    )
    assert repaired.signature(repaired.calls[-1]).name == 'source.score'


def test_union_overload_choice_is_ambiguous_and_weakening_hides_it(
    tmp_path: Path,
) -> None:
    files = {
        'source.py': OVERLOAD
        + 'def run(value: int | str) -> int | str:\n    return choose(value)\n'
    }
    with pytest.raises(
        ValueError, match='COV002: native call target is missing or ambiguous'
    ):
        calls(tmp_path / 'source', files)
    bridge = modified_bridge(
        tmp_path / 'bridge',
        lambda source: source.replace(
            'if (selected.length !== 1)', 'if (selected.length === 0)'
        ),
    )
    weakened = calls(tmp_path / 'source', files, bridge=bridge)
    assert weakened.calls[0].overload_index == 0
    assert weakened.typing.types[weakened.calls[0].result_type].category == 'union'


def test_computed_shape_is_explicitly_unsupported(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='COV002: unsupported computed native call'):
        calls(tmp_path, {'source.py': 'result = (lambda value: value)(1)\n'})


def test_disabling_precision_rejection_accepts_same_dynamic_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = {
        'source.py': 'from typing import Any\ndef work() -> Any:\n    return 1\nresult = work()\n'
    }
    with pytest.raises(ValueError, match='COV002: native any type'):
        calls(tmp_path, files)

    def weakened_precision(report: NativeTypeReport, site: TypedSite) -> None:
        pass

    monkeypatch.setattr(NativeTypeReport, 'require_precise', weakened_precision)
    weakened = calls(tmp_path, files)
    assert weakened.typing.types[weakened.calls[0].result_type].category == 'any'


def test_incomplete_source_discovery_and_independent_weakening(tmp_path: Path) -> None:
    root = tmp_path / 'source'
    root.mkdir()
    (root / 'hidden.py').write_text(FUNCTION)
    files = {'entry.py': 'from hidden import score\nresult = score(1)\n'}
    with pytest.raises(ValueError, match='COV002: native type reached undiscovered'):
        calls(root, files)
    bridge = modified_bridge(tmp_path / 'bridge', lambda source: source)
    sources = bridge.with_name('native_types_sources.mjs')
    text = sources.read_text()
    guard = 'if (inside(this.root, path) && !this.sources.has(path))'
    assert guard in text
    sources.write_text(text.replace(guard, 'if (false)'))
    weakened = calls(root, files, bridge=bridge)
    declaration = weakened.signature(weakened.calls[0]).declaration
    assert declaration is not None
    assert declaration.location.path == str(root / 'hidden.py')


def test_changed_source_and_source_changed_during_native_read_fail_closed(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'source'
    sources = write(root, {'source.py': FUNCTION + 'result = score(1)\n'})
    path = root / 'source.py'
    path.write_text(FUNCTION + 'result = score(2)\n')
    with pytest.raises(
        ValueError,
        match='COV002: native call source escapes scope, duplicates or changed',
    ):
        inspect_calls(root, sources, PACKAGE)
    bridge = modified_bridge(
        tmp_path / 'bridge',
        lambda source: source.replace(
            'import { createHash }',
            "import { writeFileSync } from 'node:fs';\nimport { createHash }",
        ).replace(
            'source.verify();',
            "writeFileSync([...sources.keys()][0], 'changed'); source.verify();",
        ),
    )
    with pytest.raises(
        ValueError, match='COV002: source changed during native type analysis'
    ):
        calls(root, {'source.py': FUNCTION + 'result = score(1)\n'}, bridge=bridge)


@pytest.mark.parametrize(
    'case',
    ['source_empty', 'call_empty', 'node_missing', 'bridge_missing', 'package_changed'],
)
def test_missing_required_call_inputs_fail_closed(tmp_path: Path, case: str) -> None:
    sources = write(tmp_path, {'source.py': FUNCTION + 'result = score(1)\n'})
    node = 'node'
    bridge = BRIDGE
    package = PACKAGE
    if case == 'source_empty':
        sources = ()
    elif case == 'call_empty':
        sources = write(tmp_path, {'source.py': FUNCTION})
    elif case == 'node_missing':
        node = 'missing-native-call-node'
    elif case == 'bridge_missing':
        bridge = tmp_path / 'native_calls.mjs'
    else:
        package = tmp_path / 'package'
        package.mkdir()
        (package / 'package.json').write_text(json.dumps({'version': 'changed'}))
    with pytest.raises(ValueError, match='COV002:'):
        inspect_calls(tmp_path, sources, package, node=node, bridge=bridge)


@pytest.mark.parametrize(
    'field', ['schema', 'references', 'overload', 'sites', 'request', 'artifacts']
)
def test_native_response_mutation_rejects_schema_identity_and_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    decoder = parse_call_report

    def mutated(value: JsonValue) -> NativeCallReport:
        response = object_value(value)
        source = object_value(values(response['files'])[0])
        call = object_value(values(source['calls'])[0])
        if field == 'schema':
            call['effect'] = 'guessed_pure'
        elif field == 'references':
            call['selected_signature'] = 999999
        elif field == 'overload':
            call['overload_index'] = 1
        elif field == 'sites':
            response['sites'] = values(response['sites'])[:-1]
        elif field == 'request':
            response['request_sha256'] = 'changed'
        else:
            response['bridge_sources'] = []
        return decoder(response)

    monkeypatch.setattr(native_calls, 'parse_call_report', mutated)
    with pytest.raises(ValueError, match='COV002:'):
        calls(tmp_path, {'source.py': OVERLOAD + 'result = choose(1)\n'})


def test_signature_cannot_be_read_from_foreign_report(tmp_path: Path) -> None:
    report = calls(tmp_path, {'source.py': FUNCTION + 'result = score(1)\n'})
    with pytest.raises(ValueError, match='COV002: native call is outside this report'):
        report.signature(replace(report.calls[0], node_id=999999))


def test_native_parse_error_rejects_source_without_python_discovery(
    tmp_path: Path,
) -> None:
    content = b'result = broken(\n'
    (tmp_path / 'source.py').write_bytes(content)
    source = Source('source.py', hashlib.sha256(content).hexdigest(), ())
    with pytest.raises(
        ValueError, match='COV002: native discovered source parse failed'
    ):
        inspect_calls(tmp_path, (source,), PACKAGE)
