import json
from pathlib import Path
from typing import cast

import pytest

from tests.quality.support import PROJECT, run
from tools.architecture.compiler import Compiler, JsonValue, object_value

pytestmark = pytest.mark.unit


def typed(root: Path, source: str) -> list[JsonValue]:
    if not source.strip():
        raise ValueError('COV002: identifier fixture has no source scope')
    (root / 'pyrightconfig.json').write_text(
        json.dumps(
            {
                'typeCheckingMode': 'strict',
                'pythonVersion': '3.10',
                'venvPath': str(PROJECT),
                'venv': '.venv',
                'extraPaths': [str(PROJECT / 'src')],
                'stubPath': str(PROJECT / 'typings'),
                'include': ['consumer.py'],
            }
        )
    )
    (root / 'consumer.py').write_text(source)
    result = run(
        [
            'uv',
            'run',
            '--locked',
            '--no-sync',
            'pyright',
            '--project',
            str(root / 'pyrightconfig.json'),
            '--outputjson',
        ],
        PROJECT,
    )
    assert result.returncode in (0, 1), result.stderr
    report = object_value(cast(JsonValue, json.loads(result.stdout)))
    diagnostics = report['generalDiagnostics']
    assert isinstance(diagnostics, list)
    return diagnostics


@pytest.mark.parametrize(
    'owned,other',
    (
        ('FlyWireNeuronId', 'int'),
        ('NeuronRow', 'FlyWireNeuronId'),
        ('TrialId', 'NeuronRow'),
        ('FlyWireNeuronId', 'TrialId'),
        ('FlyWireIds64', 'NeuronRows64'),
        ('NeuronRows32', 'EdgeRows32'),
        ('NeuronRows64', 'TrialIds64'),
        ('EdgeRows32', 'NeuronRows32'),
        ('PaddedEdgeRows32', 'EdgeRows32'),
        ('TrialIds16', 'TrialIds64'),
        ('TrialIds64', 'FlyWireIds64'),
    ),
)
def test_native_consumer_rejects_wrong_space_and_accepts_repaired_contract(
    tmp_path: Path, owned: str, other: str
) -> None:
    source = (
        'from fly_brain.simulation.identifiers import '
        + ', '.join(name for name in (owned, other) if name != 'int')
        + '\n'
        + f'def consume(value: {owned}) -> {owned}:\n    return value\n'
        + f'def execute(value: {other}) -> {owned}:\n    return consume(value)\n'
        + f'def preserve(value: {other}) -> {other}:\n    return value\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    start = object_value(object_value(diagnostic['range'])['start'])
    assert (len(found), diagnostic['rule'], diagnostic['file'], start['line']) == (
        1,
        'reportArgumentType',
        str(tmp_path / 'consumer.py'),
        4,
    )
    assert (
        typed(
            tmp_path,
            source.replace(f'execute(value: {other}', f'execute(value: {owned}'),
        )
        == []
    )


def test_alias_reexport_and_wrapper_keep_the_actual_scalar_boundary(
    tmp_path: Path,
) -> None:
    (tmp_path / 'facade.py').write_text(
        'from fly_brain.simulation.identifiers import NeuronRow as PublicRow\n'
    )
    source = (
        'from facade import PublicRow as Row\n'
        'from fly_brain.simulation.identifiers import FlyWireNeuronId as Id\n'
        'def consume(value: Row) -> Row:\n    return value\n'
        'def forward(value: Id) -> Row:\n    return consume(value)\n'
        'def preserve(value: Id) -> Id:\n    return value\n'
    )
    found = typed(tmp_path, source)
    assert len(found) == 1
    assert object_value(found[0])['rule'] == 'reportArgumentType'
    assert (
        typed(tmp_path, source.replace('forward(value: Id)', 'forward(value: Row)'))
        == []
    )


def test_primitive_count_and_explicit_rebranding_remain_native_coverage_limits(
    tmp_path: Path,
) -> None:
    source = (
        'from fly_brain.simulation.identifiers import '
        'NeuronRow, FlyWireIds64, NeuronRows64\n'
        'def count(value: NeuronRow) -> int:\n    return value\n'
        + 'def explicit_rebrand(value: FlyWireIds64) -> NeuronRows64:\n'
        + '    return NeuronRows64(value)\n'
    )
    assert typed(tmp_path, source) == []


def test_erasing_brand_loses_primitive_rejection(tmp_path: Path) -> None:
    original = (PROJECT / 'src/fly_brain/simulation/identifiers.py').read_text()
    (tmp_path / 'local_ids.py').write_text(original)
    source = (
        'from local_ids import NeuronRow\n'
        'def consume(value: NeuronRow) -> int:\n    return value\n'
        'def execute(value: int) -> int:\n    return consume(value)\n'
    )
    assert len(typed(tmp_path, source)) == 1
    (tmp_path / 'local_ids.py').write_text(
        original.replace("NewType('NeuronRow', int)", 'int')
    )
    assert typed(tmp_path, source) == []


def test_empty_scope_and_unknown_type_are_analysis_failures(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='COV002:.*no source scope'):
        typed(tmp_path, '')
    path = tmp_path / 'unknown.py'
    path.write_text('value = MissingIdentity(0)\n')
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        with pytest.raises(ValueError, match='COV002: unresolved source symbol'):
            compiler.resolve(path, 1, 12)
