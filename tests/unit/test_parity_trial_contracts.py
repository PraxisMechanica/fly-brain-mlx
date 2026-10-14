import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from fly_brain.qualification.matrix import required_cases
from fly_brain.qualification.models import ParityCase
from fly_brain.qualification.schemas import ParityOptions
from fly_brain.simulation.identifiers import TrialId
from tests.quality.support import PROJECT
from tests.unit.test_identifier_type_contracts import typed
from tools.architecture.compiler import object_value

pytestmark = pytest.mark.unit


@pytest.mark.checker
@pytest.mark.parametrize('wrong', ('int', 'NeuronRow', 'FlyWireNeuronId'))
def test_case_constructor_rejects_equal_values_in_wrong_trial_space(
    tmp_path: Path, wrong: str
) -> None:
    imports = 'TrialId' if wrong == 'int' else f'TrialId, {wrong}'
    source = (
        'from fly_brain.qualification.models import ParityCase\n'
        f'from fly_brain.simulation.identifiers import {imports}\n'
        f'def consume(value: {wrong}) -> ParityCase:\n'
        "    return ParityCase('p9', 1000, value)\n"
        'def valid(value: TrialId) -> ParityCase:\n'
        "    return ParityCase('p9', 1000, value)\n"
        f'def preserve(value: {wrong}) -> {wrong}:\n    return value\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    start = object_value(object_value(diagnostic['range'])['start'])
    assert (
        len(found),
        diagnostic['rule'],
        diagnostic['file'],
        start['line'],
        typed(
            tmp_path,
            source.replace(f'consume(value: {wrong})', 'consume(value: TrialId)'),
        ),
    ) == (1, 'reportArgumentType', str(tmp_path / 'consumer.py'), 3, [])


@pytest.mark.checker
def test_captured_reexported_case_constructor_retains_the_trial_contract(
    tmp_path: Path,
) -> None:
    (tmp_path / 'facade.py').write_text(
        'from fly_brain.qualification.models import ParityCase as Case\n'
    )
    source = (
        'from facade import Case\n'
        'from fly_brain.simulation.identifiers import NeuronRow, TrialId\n'
        'def consume(value: NeuronRow) -> Case:\n'
        '    def captured() -> Case:\n'
        "        return Case('sugar', 1000, value)\n"
        '    return captured()\n'
        'def valid(value: TrialId) -> TrialId:\n    return value\n'
        'def preserve(value: NeuronRow) -> NeuronRow:\n    return value\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    assert (
        len(found),
        diagnostic['rule'],
        object_value(object_value(diagnostic['range'])['start'])['line'],
        typed(
            tmp_path,
            source.replace('consume(value: NeuronRow)', 'consume(value: TrialId)'),
        ),
    ) == (1, 'reportArgumentType', 4, [])


@pytest.mark.checker
def test_erasing_actual_case_trial_annotation_loses_primitive_rejection(
    tmp_path: Path,
) -> None:
    original = (PROJECT / 'src/fly_brain/qualification/models.py').read_text()
    local = tmp_path / 'local_models.py'
    local.write_text(original)
    source = (
        'from local_models import ParityCase\n'
        'def consume(value: int) -> ParityCase:\n'
        "    return ParityCase('p9', 1000, value)\n"
    )
    assert len(typed(tmp_path, source)) == 1
    local.write_text(original.replace('trial: TrialId', 'trial: int'))
    assert typed(tmp_path, source) == []


def test_catalog_retains_all_fifty_two_values_and_their_original_order() -> None:
    cases = required_cases()
    encoded = json.dumps(
        [asdict(case) for case in cases], separators=(',', ':')
    ).encode()
    assert (len(cases), hashlib.sha256(encoded).hexdigest()) == (
        52,
        '152e4073a86609a412e92512107da4cdeb5299e26abf6f3aa4698511bd0a3488',
    )


def test_case_keeps_supplied_trial_scalar_and_exact_json_field_order() -> None:
    trial = TrialId(4)
    case = ParityCase('p9', 1000, trial)
    assert (
        case.trial is trial,
        type(case.trial) is int,
        json.dumps(asdict(case)),
        case,
        hash(case),
    ) == (
        True,
        True,
        '{"experiment": "p9", "steps": 1000, "trial": 4}',
        required_cases()[19],
        hash(required_cases()[19]),
    )


@pytest.mark.parametrize('trial', (2, 4))
def test_validated_transport_keeps_integer_trial_and_establishes_requested_label(
    tmp_path: Path, trial: int
) -> None:
    (tmp_path / 'tests/qualification').mkdir(parents=True)
    options = ParityOptions(
        project=tmp_path,
        output=tmp_path / 'fresh',
        experiment='p9',
        trial=trial,
    )
    case = options.to_case()
    assert (
        ParityOptions.model_fields['trial'].annotation is int,
        ParityOptions.model_json_schema()['properties']['trial'],
        case.trial is options.trial,
        case.trial,
        options.model_dump(mode='json')['trial'],
        case in required_cases(),
    ) == (
        True,
        {'default': 0, 'maximum': 4, 'minimum': 0, 'title': 'Trial', 'type': 'integer'},
        True,
        trial,
        trial,
        True,
    )


@pytest.mark.checker
def test_diagnostic_coverage_preserves_case_trial_contract_and_primitive_steps(
    tmp_path: Path,
) -> None:
    source = (
        'from fly_brain.qualification.matrix_diagnostics import GroupCoverage\n'
        'from fly_brain.qualification.models import ParityCase\n'
        'from fly_brain.simulation.identifiers import NeuronRow, TrialId\n'
        'def consume(value: NeuronRow, steps: int) -> GroupCoverage:\n'
        "    return GroupCoverage('p9', steps, (value,), (), (), (), ())\n"
        'def selected(case: ParityCase) -> TrialId:\n    return case.trial\n'
        'def valid(trial: TrialId, steps: int) -> ParityCase:\n'
        "    return ParityCase('p9', steps, trial)\n"
        'def preserve(value: NeuronRow) -> NeuronRow:\n    return value\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    assert (
        len(found),
        diagnostic['rule'],
        typed(tmp_path, source.replace('value: NeuronRow,', 'value: TrialId,')),
    ) == (1, 'reportArgumentType', [])
