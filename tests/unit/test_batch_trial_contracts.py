import json
from dataclasses import asdict, fields
from pathlib import Path

import numpy as np
import pytest

from fly_brain.comparison.acceptance import validate_coordinates
from fly_brain.qualification.adapters.batch_verify import compare
from fly_brain.qualification.batch_evidence import (
    NativeDifference,
    NativeDigest,
    PhaseDifference,
    native_difference,
)
from fly_brain.simulation.identifiers import TrialId
from tests.quality.support import PROJECT, run
from tests.unit.test_batch_native import native
from tests.unit.test_identifier_type_contracts import typed
from tools.architecture.compiler import JsonValue, object_value

pytestmark = pytest.mark.unit
HASHES = ('1' * 64, '2' * 64, '3' * 64, '4' * 64)


def consumer(label: str) -> str:
    return (
        'from collections.abc import Callable\n'
        'from pathlib import Path\n'
        'from fly_brain.qualification import batch_evidence as evidence\n'
        'from fly_brain.qualification.adapters import batch_verify\n'
        'from fly_brain.qualification.adapters import batch_environment\n'
        'from fly_brain.qualification.spike_comparison_ports import CoordinateValidator\n'
        'from fly_brain.simulation import identifiers as ids\n'
        f'def forward(wrong: {label}, correct: ids.TrialId, '
        'native: tuple[evidence.NativeDigest, ...], '
        'phases: tuple[evidence.PhaseDigest, ...], path: Path, '
        'validate: CoordinateValidator, launch: Callable[[str, str], bytes]) -> None:\n'
        "    evidence.PhaseDifference(wrong, 0, 1, 'native')\n"
        '    evidence.NativeDifference(wrong, 0)\n'
        '    evidence.native_difference(native, {wrong: native}, 1)\n'
        '    evidence.phase_difference(phases, {wrong: phases}, 1)\n'
        "    batch_verify.compare(path, {wrong: path}, 'cpu', 1, 6, 3, 2, validate=validate)\n"
        "    batch_environment.require_environments(path, (path, 'launch'), "
        "{wrong: (path, 'launch')}, launch)\n"
    )


def location(entry: JsonValue) -> tuple[JsonValue, JsonValue, JsonValue]:
    value = object_value(entry)
    start = object_value(object_value(value['range'])['start'])
    return value['rule'], value['file'], start['line']


@pytest.mark.checker
@pytest.mark.parametrize('wrong', ('int', 'ids.NeuronRow', 'ids.FlyWireNeuronId'))
def test_actual_batch_label_fields_and_maps_reject_plain_and_foreign_spaces(
    tmp_path: Path, wrong: str
) -> None:
    assert tuple(map(location, typed(tmp_path, consumer(wrong)))) == tuple(
        zip(
            ('reportArgumentType',) * 6,
            (str(tmp_path / 'consumer.py'),) * 6,
            range(8, 14),
            strict=True,
        )
    )


@pytest.mark.checker
def test_trial_labels_repair_all_six_actual_boundaries(tmp_path: Path) -> None:
    assert typed(tmp_path, consumer('ids.TrialId')) == []


@pytest.mark.checker
@pytest.mark.parametrize(
    'module,import_line,alias,remaining',
    (
        (
            'batch_evidence',
            'from fly_brain.qualification import batch_evidence as evidence',
            'evidence',
            (12, 13),
        ),
        (
            'adapters.batch_verify',
            'from fly_brain.qualification.adapters import batch_verify',
            'batch_verify',
            (8, 9, 10, 11, 13),
        ),
        (
            'adapters.batch_environment',
            'from fly_brain.qualification.adapters import batch_environment',
            'batch_environment',
            (8, 9, 10, 11, 12),
        ),
    ),
)
def test_erasing_each_batch_label_contract_loses_its_native_rejection(
    tmp_path: Path,
    module: str,
    import_line: str,
    alias: str,
    remaining: tuple[int, ...],
) -> None:
    original = (
        (PROJECT / 'src/fly_brain/qualification' / Path(*module.split('.')))
        .with_suffix('.py')
        .read_text()
    )
    local = original.replace(
        'from .batch_native import',
        'from fly_brain.qualification.adapters.batch_native import',
    )
    path = tmp_path / 'local_subject.py'
    path.write_text(local)
    source = consumer('int').replace(import_line, f'import local_subject as {alias}')
    strong = tuple(map(location, typed(tmp_path, source)))
    weakened = local.replace(
        'from fly_brain.simulation.identifiers import TrialId',
        'from builtins import int as TrialId',
    )
    path.write_text(weakened)
    weak = tuple(map(location, typed(tmp_path, source)))
    assert (weakened != local, strong, weak) == (
        True,
        tuple(
            zip(
                ('reportArgumentType',) * 6,
                (str(tmp_path / 'consumer.py'),) * 6,
                range(8, 14),
                strict=True,
            )
        ),
        tuple(
            zip(
                ('reportArgumentType',) * len(remaining),
                (str(tmp_path / 'consumer.py'),) * len(remaining),
                remaining,
                strict=True,
            )
        ),
    )


@pytest.mark.parametrize('order', ((0, 1, 2, 3), (3, 1, 0, 2)))
def test_canonical_labels_keep_scalar_identity_mapping_order_and_integer_encoding(
    order: tuple[int, ...],
) -> None:
    labels = (
        TrialId(order[0]),
        TrialId(order[1]),
        TrialId(order[2]),
        TrialId(order[3]),
    )
    batch = (NativeDigest(-1, HASHES), NativeDigest(0, HASHES))
    singles = {
        label: tuple(NativeDigest(row.step, (row.native[label],)) for row in batch)
        for label in labels
    }
    values = tuple(map(id, singles.values()))
    changed = (batch[0], NativeDigest(0, (*HASHES[:3], 'f' * 64)))
    comparison = (
        native_difference(batch, singles, 1),
        native_difference(changed, singles, 1),
    )
    raw = int('3000')
    label = TrialId(raw)
    phase = PhaseDifference(label, 0, 1, 'due')
    native = NativeDifference(label, 0)
    assert (
        comparison,
        tuple(singles),
        tuple(map(id, singles)),
        tuple(map(id, singles.values())),
        label is raw,
        phase.trial is raw,
        native.trial is raw,
        type(phase.trial),
        tuple(field.name for field in fields(phase)),
        json.dumps(
            {'phase': asdict(phase), 'native': asdict(native), 'labels': labels}
        ),
    ) == (
        (None, NativeDifference(TrialId(3), 0)),
        labels,
        tuple(map(id, labels)),
        values,
        True,
        True,
        True,
        int,
        ('trial', 'begin', 'rows', 'field'),
        '{"phase": {"trial": 3000, "begin": 0, "rows": 1, "field": "due"}, '
        '"native": {"trial": 3000, "step": 0}, "labels": ' + json.dumps(order) + '}',
    )


@pytest.mark.integration
def test_saved_singleton_label_three_uses_position_zero_and_float_keys_still_fail(
    tmp_path: Path,
) -> None:
    labels = (TrialId(3), TrialId(1), TrialId(0), TrialId(2))
    singletons = {label: tmp_path / f'single-{label}' for label in labels}
    batch = tmp_path / 'batch'
    for directory, trials, positions, neurons, digests in (
        (batch, 4, np.arange(4, dtype=np.int64), np.arange(4, dtype=np.int64), HASHES),
        *(
            (
                path,
                1,
                np.zeros(1, dtype=np.int64),
                np.array([label], dtype=np.int64),
                (HASHES[label],),
            )
            for label, path in singletons.items()
        ),
    ):
        directory.mkdir()
        arrays = native('cpu', trials)
        arrays['spike_trials'] = positions
        arrays['spike_neurons'] = neurons
        arrays['spike_steps'] = np.zeros(arrays['spike_trials'].size, dtype=np.int64)
        with (directory / 'native.npz').open('xb') as artifact:
            np.savez_compressed(artifact, **arrays)
        (directory / 'native-digests.jsonl').write_text(
            ''.join(
                json.dumps({'step': step, 'native_sha256': digests}) + '\n'
                for step in (-1, 0)
            )
        )
    difference, finals = compare(
        batch, singletons, 'cpu', 1, 6, 3, 2, validate=validate_coordinates
    )
    source = (
        'import sys\n'
        'from pathlib import Path\n'
        'from fly_brain.comparison.acceptance import validate_coordinates\n'
        'from fly_brain.qualification.adapters.batch_verify import compare\n'
        'root = Path(sys.argv[1])\n'
        "compare(root / 'batch', "
        "{float(label): root / f'single-{label}' for label in (3, 1, 0, 2)}, "
        "'cpu', 1, 6, 3, 2, validate=validate_coordinates)\n"
    )
    found = tuple(map(location, typed(tmp_path, source)))
    process = run(
        [
            'uv',
            'run',
            '--locked',
            '--no-sync',
            'python',
            str(tmp_path / 'consumer.py'),
            str(tmp_path),
        ],
        PROJECT,
    )
    assert (
        difference,
        tuple(finals),
        tuple(finals.values()),
        tuple(map(id, finals)),
        found,
        process.returncode,
        'tuple indices must be integers or slices, not float' in process.stderr,
        'trial_spikes(batch, 4, neurons, steps, validate=validate)[trial]'
        in process.stderr,
    ) == (
        None,
        labels,
        ((),) * 4,
        tuple(map(id, labels)),
        (('reportArgumentType', str(tmp_path / 'consumer.py'), 5),),
        1,
        True,
        True,
    )
