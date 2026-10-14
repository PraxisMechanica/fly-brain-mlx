from dataclasses import asdict, fields, replace
from pathlib import Path

import numpy as np
import pytest

from fly_brain.comparison.acceptance import (
    steps_from_reference_clock,
    validate_coordinates,
)
from fly_brain.comparison.models import RowSpikeSteps, SpikeSteps
from fly_brain.qualification.adapters.case_spikes import load
from fly_brain.simulation.identifiers import FlyWireIds64, NeuronRows32, NeuronRows64
from fly_brain.simulation.models import Connectome
from tests.quality.support import PROJECT
from tests.unit.test_identifier_type_contracts import typed
from tests.unit.test_metric_identifier_contracts import array_state
from tools.code_quality.json_values import object_value

pytestmark = pytest.mark.unit


@pytest.mark.parametrize('readonly', (False, True))
@pytest.mark.parametrize('size', (0, 6))
def test_raster_specializations_keep_record_fields_and_exact_borrowed_arrays(
    readonly: bool, size: int
) -> None:
    neurons = np.arange(12, dtype=np.int64)[::2][:size]
    steps = np.arange(12, dtype=np.int64)[1::2][:size]
    neurons.setflags(write=not readonly)
    steps.setflags(write=not readonly)
    before = (array_state(neurons), array_state(steps))
    row = SpikeSteps(neurons=NeuronRows64(neurons), steps=steps)
    wire = SpikeSteps(FlyWireIds64(neurons), steps)
    cloned = replace(row)
    assert (
        type(row),
        type(wire),
        type(cloned),
        row.neurons is neurons,
        wire.neurons is neurons,
        cloned.neurons is neurons,
        row.steps is steps,
        wire.steps is steps,
        cloned.steps is steps,
        tuple(field.name for field in fields(row)),
        tuple(row.__dict__),
        tuple(asdict(wire)),
        (array_state(neurons), array_state(steps)),
    ) == (
        SpikeSteps,
        SpikeSteps,
        SpikeSteps,
        True,
        True,
        True,
        True,
        True,
        True,
        ('neurons', 'steps'),
        ('neurons', 'steps'),
        ('neurons', 'steps'),
        before,
    )


@pytest.mark.checker
@pytest.mark.parametrize(
    'bad,good',
    (
        ('validate(wire, 4, 100)', 'validate(row, 4, 100)'),
        (
            'validate(raster.SpikeSteps[ids.NeuronRows64](raw, row.steps), 4, 100)',
            'validate(raster.SpikeSteps[ids.NeuronRows64](row.neurons, row.steps), 4, 100)',
        ),
        ('score(row, wire, wire, 0.1)', 'score(wire, wire, wire, 0.1)'),
        (
            'score(raster.SpikeSteps[ids.FlyWireIds64](raw, wire.steps), wire, wire, 0.1)',
            'score(raster.SpikeSteps[ids.FlyWireIds64](wire.neurons, wire.steps), wire, wire, 0.1)',
        ),
        (
            'score(raster.SpikeSteps[ids.FlyWireIds64](foreign, wire.steps), wire, wire, 0.1)',
            'score(raster.SpikeSteps[ids.FlyWireIds64](wire.neurons, wire.steps), wire, wire, 0.1)',
        ),
        (
            'measure(((wire, row),), wire.neurons, 0.1)',
            'measure(((wire, wire),), wire.neurons, 0.1)',
        ),
        (
            'measure(((wire, wire),), row.neurons, 0.1)',
            'measure(((wire, wire),), wire.neurons, 0.1)',
        ),
        (
            'measure(((wire, wire),), raw, 0.1)',
            'measure(((wire, wire),), wire.neurons, 0.1)',
        ),
        (
            'measure(((wire, wire),), foreign, 0.1)',
            'measure(((wire, wire),), wire.neurons, 0.1)',
        ),
    ),
)
def test_actual_raster_consumers_reject_plain_foreign_and_mixed_spaces(
    tmp_path: Path, bad: str, good: str
) -> None:
    source = (
        'import numpy as np\n'
        'from numpy.typing import NDArray\n'
        'from fly_brain.comparison import models as raster\n'
        'from fly_brain.simulation import identifiers as ids\n'
        'from fly_brain.qualification.spike_comparison_ports import '
        'CoordinateValidator, CaseScorer, TrialMeasurer\n'
        'def forward(row: raster.RowSpikeSteps, wire: raster.FlyWireSpikeSteps, '
        'raw: NDArray[np.int64], foreign: ids.TrialIds64, '
        'validate: CoordinateValidator, score: CaseScorer, measure: TrialMeasurer)'
        f' -> None:\n    {bad}\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    start = object_value(object_value(diagnostic['range'])['start'])
    assert (
        len(found),
        diagnostic['rule'],
        diagnostic['file'],
        start['line'],
        typed(tmp_path, source.replace(bad, good)),
    ) == (
        1,
        'reportArgumentType',
        str(tmp_path / 'consumer.py'),
        6,
        [],
    )


@pytest.mark.checker
def test_raster_alias_type_only_reexport_and_capture_preserve_space(
    tmp_path: Path,
) -> None:
    (tmp_path / 'facade.py').write_text(
        'from fly_brain.comparison.models import RowSpikeSteps as PublicRow\n'
    )
    source = (
        'from typing import TYPE_CHECKING\n'
        'from fly_brain.comparison.models import FlyWireSpikeSteps\n'
        'if TYPE_CHECKING:\n    from facade import PublicRow as Row\n'
        'def forward(wrong: FlyWireSpikeSteps) -> Row:\n'
        '    def captured() -> Row:\n        return wrong\n'
        '    return captured()\n'
    )
    found = typed(tmp_path, source)
    diagnostic = object_value(found[0])
    start = object_value(object_value(diagnostic['range'])['start'])
    assert (
        len(found),
        diagnostic['rule'],
        start['line'],
        typed(
            tmp_path,
            source.replace('wrong: FlyWireSpikeSteps', 'wrong: Row').replace(
                'from fly_brain.comparison.models import FlyWireSpikeSteps\n', ''
            ),
        ),
    ) == (
        1,
        'reportReturnType',
        6,
        [],
    )


@pytest.mark.checker
def test_erasing_raster_specializations_restores_wrong_space_forwarding(
    tmp_path: Path,
) -> None:
    original = (PROJECT / 'src/fly_brain/comparison/models.py').read_text()
    path = tmp_path / 'local_models.py'
    path.write_text(original)
    source = (
        'from local_models import RowSpikeSteps, FlyWireSpikeSteps\n'
        'def forward(wire: FlyWireSpikeSteps) -> RowSpikeSteps:\n    return wire\n'
    )
    found = typed(tmp_path, source)
    assert (len(found), object_value(found[0])['rule']) == (1, 'reportReturnType')
    weakened = (
        original.replace('class SpikeSteps(Generic[RasterIds]):', 'class SpikeSteps:')
        .replace('    neurons: RasterIds\n', '    neurons: NDArray[np.int64]\n')
        .replace('SpikeSteps[NeuronRows64]', 'SpikeSteps')
        .replace('SpikeSteps[FlyWireIds64]', 'SpikeSteps')
    )
    path.write_text(weakened)
    assert (weakened != original, typed(tmp_path, source)) == (True, [])


@pytest.mark.parametrize('fault', (False, True))
def test_native_row_ingress_validates_before_actual_flywire_lookup(
    tmp_path: Path,
    fault: bool,
) -> None:
    ids = np.array([300000000000000001, 7, 0], dtype=np.int64)
    connectome = Connectome(
        FlyWireIds64(ids),
        NeuronRows32(np.array([], dtype=np.int32)),
        NeuronRows32(np.array([], dtype=np.int32)),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    indices = np.array([2, 3 if fault else 0], dtype=np.int64)
    steps = np.array([4, 2], dtype=np.int64)
    np.savez(
        tmp_path / 'reference-native.npz',
        spike_i=indices.astype(np.int32),
        spike_t=steps * 0.0001,
    )
    np.savez(tmp_path / 'mlx-native.npz', spike_neurons=indices, spike_steps=steps)
    np.savez(
        tmp_path / 'native.npz',
        spike_neurons=indices,
        spike_steps=steps,
        spike_trials=np.zeros(2, dtype=np.int64),
    )
    observed: list[RowSpikeSteps] = []

    def checked(value: RowSpikeSteps, neurons: int, horizon: int) -> None:
        observed.append(value)
        validate_coordinates(value, neurons, horizon)

    if fault:
        with pytest.raises(ValueError, match='pinned neuron/step bounds'):
            load(
                connectome,
                10,
                tmp_path,
                tmp_path,
                validate=checked,
                convert_clock=steps_from_reference_clock,
            )
        assert observed[0].neurons.tolist() == [2, 3]
        return
    actual, _ = load(
        connectome,
        10,
        tmp_path,
        tmp_path,
        validate=checked,
        convert_clock=steps_from_reference_clock,
    )
    assert (
        tuple((row.neurons.tolist(), row.steps.tolist()) for row in observed),
        tuple(
            (value.neurons.dtype, value.neurons.tobytes(), value.steps.tobytes())
            for value in actual.values()
        ),
    ) == (
        (([2, 0], [4, 2]),) * 3,
        ((np.dtype(np.int64), ids[indices].tobytes(), steps.tobytes()),) * 3,
    )
