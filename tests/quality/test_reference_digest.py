import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import pytest

from fly_brain.qualification.adapters.observer_stream import StreamShape
from fly_brain.qualification.adapters.reference_identity import create
from fly_brain.qualification.reference_values import ReferenceProducerDigest
from fly_brain.simulation.models import Connectome, Stimulus
from tests.quality.support import PROJECT, run
from tools.architecture.compiler import Compiler, JsonValue, object_value
from tools.architecture.resolution import unique_location

pytestmark = pytest.mark.unit
IMPORT = (
    'from fly_brain.qualification.reference_values import '
    'ReferenceProducerDigest as Digest\n'
)
CONSUMER = 'def consume(value: Digest) -> Digest:\n    return value\n'

LegacyProducer = Callable[
    [
        Connectome,
        Stimulus,
        tuple[int, ...],
        StreamShape,
        Mapping[str, str],
        Path,
        Mapping[str, object],
    ],
    tuple[str, dict[str, object]],
]


def preserved_identity(
    legacy: LegacyProducer,
    connectome: Connectome,
    stimulus: Stimulus,
    silenced: tuple[int, ...],
    shape: StreamShape,
    directory: Path,
    context: Mapping[str, object],
) -> ReferenceProducerDigest:
    actual, record = create(
        connectome, stimulus, silenced, shape, {}, directory, context
    )
    original, prior = legacy(
        connectome, stimulus, silenced, shape, {}, directory, context
    )
    encoded = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
    prior_encoded = json.dumps(prior, sort_keys=True, separators=(',', ':')).encode()
    assert (record, tuple(record), encoded, actual) == (
        prior,
        tuple(prior),
        prior_encoded,
        original,
    )
    return actual


def typed(root: Path, source: str) -> dict[str, JsonValue]:
    if not source.strip():
        raise ValueError('COV002: digest type fixture has no source scope')
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
    return object_value(cast(JsonValue, json.loads(result.stdout)))


def diagnostics(report: dict[str, JsonValue]) -> list[JsonValue]:
    items = report['generalDiagnostics']
    assert isinstance(items, list)
    return items


@pytest.mark.parametrize(
    'imports,annotation',
    (
        (IMPORT, 'str'),
        (IMPORT, 'int'),
        (IMPORT, 'bytes'),
        (
            IMPORT + 'from typing import NewType\nOther = NewType("Other", str)\n',
            'Other',
        ),
        ('from facade import Public as Digest\n', 'str'),
    ),
)
def test_native_digest_consumer_rejects_primitive_foreign_brand_and_reexport(
    tmp_path: Path, imports: str, annotation: str
) -> None:
    (tmp_path / 'facade.py').write_text(
        'from fly_brain.qualification.reference_values import '
        'ReferenceProducerDigest as Public\n'
    )
    body = CONSUMER + f'def execute(value: {annotation}) -> Digest:\n'
    body += '    return consume(value)\n'
    found = diagnostics(typed(tmp_path, imports + body))
    diagnostic = object_value(found[0])
    start = object_value(object_value(diagnostic['range'])['start'])
    assert (
        len(found),
        diagnostic['rule'],
        diagnostic['file'],
        start['line'],
        'ReferenceProducerDigest' in str(diagnostic['message']),
    ) == (
        1,
        'reportArgumentType',
        str(tmp_path / 'consumer.py'),
        len(imports.splitlines()) + 3,
        True,
    )
    assert (
        diagnostics(typed(tmp_path, imports + body.replace(annotation, 'Digest'))) == []
    )


def test_brand_preserves_string_identity_and_primitive_serialization() -> None:
    raw = ''.join(('12' * 16, 'ab' * 16))
    digest = ReferenceProducerDigest(raw)
    assert (digest is raw, type(digest), json.dumps({'digest': digest})) == (
        True,
        str,
        json.dumps({'digest': raw}),
    )


def test_actual_producer_and_digest_resolve_to_the_owned_native_definitions(
    tmp_path: Path,
) -> None:
    source = (
        IMPORT
        + 'from fly_brain.qualification.adapters.reference_identity import create\n'
        + CONSUMER
        + 'producer = create\n'
    )
    assert diagnostics(typed(tmp_path, source)) == []
    path = tmp_path / 'consumer.py'
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        brand = compiler.resolve(path, 3, 20)
        producer = compiler.resolve(path, 5, 12)
    assert (
        unique_location(brand['definitions'], 'digest').path,
        unique_location(producer['definitions'], 'producer').path,
        'ReferenceProducerDigest' in str(producer['signature']),
    ) == (
        str(PROJECT / 'src/fly_brain/qualification/reference_values.py'),
        str(PROJECT / 'src/fly_brain/qualification/adapters/reference_identity.py'),
        True,
    )


def test_native_close_primitive_serialization_and_explicit_rebranding_limit(
    tmp_path: Path,
) -> None:
    source = (
        IMPORT
        + 'from typing import NewType\nOther = NewType("Other", str)\n'
        + CONSUMER
        + 'def serialize(value: Digest) -> str:\n    return value\n'
        + 'def rebrand(value: Other) -> Digest:\n    return consume(Digest(value))\n'
    )
    assert diagnostics(typed(tmp_path, source)) == []


def test_erasing_the_actual_brand_loses_the_same_primitive_rejection(
    tmp_path: Path,
) -> None:
    brand = PROJECT / 'src/fly_brain/qualification/reference_values.py'
    original = brand.read_text()
    (tmp_path / 'local_brand.py').write_text(original)
    source = (
        'from local_brand import ReferenceProducerDigest as Digest\n'
        + CONSUMER
        + 'def execute(value: str) -> Digest:\n    return consume(value)\n'
    )
    assert len(diagnostics(typed(tmp_path, source))) == 1
    (tmp_path / 'local_brand.py').write_text(
        original.replace("NewType('ReferenceProducerDigest', str)", 'str')
    )
    assert diagnostics(typed(tmp_path, source)) == []


def test_weakening_the_consumer_parameter_loses_the_same_foreign_brand_defect(
    tmp_path: Path,
) -> None:
    source = (
        IMPORT
        + 'from typing import NewType\nOther = NewType("Other", str)\n'
        + 'def owned(value: Digest) -> Digest:\n    return value\n'
        + 'def consume(value: Digest) -> str:\n    return value\n'
        + 'def execute(value: Other) -> str:\n    return consume(value)\n'
    )
    assert len(diagnostics(typed(tmp_path, source))) == 1
    assert (
        diagnostics(
            typed(
                tmp_path,
                source.replace('def consume(value: Digest)', 'def consume(value: str)'),
            )
        )
        == []
    )


def test_empty_scope_and_unresolved_digest_target_are_analysis_failures(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match='COV002:.*no source scope'):
        typed(tmp_path, '')
    path = tmp_path / 'unknown.py'
    path.write_text('value = MissingDigest("abc")\n')
    with Compiler(tmp_path, PROJECT / '.venv/bin/pyright-langserver') as compiler:
        with pytest.raises(ValueError, match='COV002: unresolved source symbol'):
            compiler.resolve(path, 1, 12)
