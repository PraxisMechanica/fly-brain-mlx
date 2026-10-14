from pathlib import Path

import pytest

from tests.quality.support import PROJECT
from tests.quality.test_parity_stimulus_boundary import lint
from tests.quality.test_reference_silencing_boundary import typed

pytestmark = pytest.mark.unit
RULE = 'DEP003/ROLE005: Input audit uses owned mapping services'
SOURCE = 'fly_brain.qualification.input_audit_service'
TARGETS = (
    'fly_brain.simulation.mapping',
    'fly_brain.simulation.input_service',
    'fly_brain.simulation.module',
)
TYPES = """from pathlib import Path
from fly_brain.qualification.input_audit_service import run
from fly_brain.qualification.input_audit_rules import bucket_report
from fly_brain.qualification.ports import AbsoluteCountReader, DestinationGroupingReader, DestinationBucketsReader, InputAuditFiles
from fly_brain.simulation.models import Connectome, InputPin
from fly_brain.simulation.module import build_absolute_count_reader, build_destination_grouping_reader, build_destination_buckets_reader, build_connectome_silencer
absolute: AbsoluteCountReader = build_absolute_count_reader()
grouping: DestinationGroupingReader = build_destination_grouping_reader()
buckets: DestinationBucketsReader = build_destination_buckets_reader()
def execute(connectome: Connectome, pin: InputPin, output: Path, files: InputAuditFiles) -> dict[str, object]:
    bucket_report(connectome, pin, buckets=buckets(connectome))
    return run(connectome, pin, output, read_grouping=grouping, read_absolute_counts=absolute, silence=build_connectome_silencer(), files=files, read_buckets=buckets)
"""


def contract(name: str = RULE) -> str:
    block = next(
        value
        for value in (PROJECT / 'pyproject.toml')
        .read_text()
        .split('[[tool.importlinter.contracts]]')
        if 'name = "' + name + '"' in value
    )
    return (
        '[tool.importlinter]\nroot_package = "fly_brain"\n\n[[tool.importlinter.contracts]]'
        + block
    )


def sources(root: Path, target: str, code: str, source: str = SOURCE) -> Path:
    names = {
        SOURCE: 'VALUE = 1\n',
        'fly_brain.qualification.input_audit_rules': 'VALUE = 1\n',
        **{name: 'VALUE = 1\n' for name in (*TARGETS, target)},
    }
    names[source] = code
    names['fly_brain.qualification.mapping_helper'] = f'from {target} import VALUE\n'
    names['fly_brain.qualification.ports'] = 'VALUE = 1\n'
    for name in (
        'fly_brain',
        'fly_brain.qualification',
        'fly_brain.qualification.adapters',
        'fly_brain.simulation',
    ):
        path = root / 'src' / Path(*name.split('.')) / '__init__.py'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('')
    for name, code in names.items():
        (root / 'src' / Path(*name.split('.')).with_suffix('.py')).write_text(code)
    config = root / 'contract.toml'
    config.write_text(contract())
    return config


@pytest.mark.parametrize('target', TARGETS)
def test_new_contract_rejects_each_private_target_and_accepts_consumer_values(
    tmp_path: Path,
    target: str,
) -> None:
    config = sources(tmp_path, target, f'from {target} import VALUE as hidden\n')
    result, output = lint(tmp_path, config)
    assert (
        result != 0,
        RULE in output,
        SOURCE in output,
        target in output,
        '(l.1)' in output,
    ) == (True,) * 5
    (tmp_path / 'src/fly_brain/qualification/input_audit_service.py').write_text(
        'from fly_brain.qualification.ports import VALUE\n'
    )
    assert lint(tmp_path, config)[0] == 0


def test_new_contract_preserves_transitive_reexport_rejection_and_weakening(
    tmp_path: Path,
) -> None:
    config = sources(
        tmp_path,
        TARGETS[0],
        'from fly_brain.qualification.mapping_helper import VALUE\n',
    )
    result, output = lint(tmp_path, config)
    assert (
        result != 0,
        SOURCE in output,
        'fly_brain.qualification.mapping_helper' in output,
        TARGETS[0] in output,
        '(l.1)' in output,
    ) == (True,) * 5
    config.write_text(
        contract().replace(
            'allow_indirect_imports = false', 'allow_indirect_imports = true'
        )
    )
    assert lint(tmp_path, config)[0] == 0


def test_live_contract_and_close_literal_pass_but_missing_source_fails(
    tmp_path: Path,
) -> None:
    config = sources(
        tmp_path, TARGETS[0], '# import simulation.mapping\nVALUE = "mapping"\n'
    )
    assert (lint(tmp_path, config)[0], lint(PROJECT, config)[0]) == (0, 0)
    config.write_text(contract().replace(SOURCE, 'fly_brain.qualification.missing'))
    result, output = lint(tmp_path, config)
    assert result != 0 and 'does not exist' in output


@pytest.mark.parametrize(
    'keyword',
    (
        'read_grouping=grouping, ',
        'read_absolute_counts=absolute, ',
        'silence=build_connectome_silencer(), ',
        'read_buckets=buckets',
    ),
)
def test_each_required_collaboration_rejects_omission_then_accepts_real_providers(
    tmp_path: Path,
    keyword: str,
) -> None:
    result, output = typed(tmp_path, TYPES.replace(keyword, '', 1))
    assert (result, 'consumer.py:' in output, keyword.split('=')[0] in output) == (
        1,
        True,
        True,
    )
    assert typed(tmp_path, TYPES)[0] == 0


def test_bucket_rule_requires_completed_data_and_analysis_errors_fail(
    tmp_path: Path,
) -> None:
    result, output = typed(
        tmp_path, TYPES.replace('buckets=buckets(connectome)', 'buckets=buckets')
    )
    assert result == 1 and 'reportArgumentType' in output
    assert typed(tmp_path, TYPES)[0] == 0
    result, output = typed(tmp_path, TYPES + 'def broken(\n')
    assert result == 1 and 'error:' in output
