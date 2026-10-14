import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from fly_brain.qualification.adapters import bucketed_scalars
from fly_brain.qualification.adapters.accumulation_probe import Case
from fly_brain.qualification.adapters.bucketed_fan_in import evaluate_cases
from fly_brain.qualification.fan_in import build_cases, compare_cases
from fly_brain.simulation.identifiers import FlyWireIds64, NeuronRows32
from fly_brain.simulation.models import Connectome

pytestmark = [pytest.mark.integration, pytest.mark.metal]


@pytest.mark.parametrize('exact_counts', (False, True))
def test_synthetic_fan_in_preserves_original_rows_duplicate_and_zero_edges(
    precision: str, exact_counts: bool
) -> None:
    counts = np.array([2, 3, 0, -3, 1], dtype=np.int32)
    connectome = Connectome(
        FlyWireIds64(np.array([100, 300, 200, 400], dtype=np.int64)),
        NeuronRows32(np.array([3, 0, 0, 1, 1], dtype=np.int32)),
        NeuronRows32(np.array([2, 1, 1, 1, 1], dtype=np.int32)),
        counts,
        counts.astype(np.float64) * 0.275,
    )
    edges = np.array([1, 2, 3, 4], dtype=np.int32)
    cases = build_cases(
        connectome.counts[edges],
        connectome.weights_mv[edges],
        masks={
            'all': np.ones(4, dtype=np.bool_),
            'alternate': np.array([True, False, True, False], dtype=np.bool_),
        },
        permutation=np.array([2, 0, 3, 1], dtype=np.int64),
    )
    first, repeat, single = evaluate_cases(
        connectome, 1, edges, cases, exact_counts=exact_counts
    )
    for original, repeated, singleton in zip(first, repeat, single, strict=True):
        assert original.dtype == np.float32 and original.shape == cases.initial64.shape
        assert original.tobytes() == repeated.tobytes() == singleton.tobytes()
    np.testing.assert_array_equal(
        first[1].astype(np.float64) + first[2].astype(np.float64), cases.exact_counts
    )
    checks = compare_cases(cases, first[0])
    assert checks.one_step_pass.all() and checks.trajectory_pass.all()


@pytest.mark.parametrize('exact_counts', (False, True))
def test_synthetic_scalar_producer_preserves_native_artifact_and_repeat_contract(
    precision: str, exact_counts: bool, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    counts = np.array([3, 0, -3, 1], dtype=np.int32)
    case = Case(
        'identifier-connectome',
        counts.astype(np.float64) * 0.275,
        np.array([True, False, True, True], dtype=np.bool_),
    )

    def selected_cases(_root: Path) -> list[Case]:
        return [case]

    monkeypatch.setattr(bucketed_scalars, 'extended_cases', selected_cases)
    output = tmp_path / 'scalar-probe'
    report = bucketed_scalars.run(
        tmp_path, output, precision, exact_counts=exact_counts
    )
    assert report['cases'] == 1
    assert report['all_components_repeat_and_match_standalone'] is True
    artifact = output / 'case-000.npz'
    with np.load(artifact) as values:
        assert values['counts'].dtype == np.int32
        assert values['counts'].tobytes() == counts.tobytes()
        assert values['weights64'].dtype == np.float64
        assert values['weights64'].tobytes() == case.weights.tobytes()
        assert values['accepted'].tobytes() == case.accepted.tobytes()
        for batch, repeat, single in (
            ('result32', 'repeated32', 'standalone32'),
            ('count_high32', 'repeat_high32', 'standalone_high32'),
            ('count_low32', 'repeat_low32', 'standalone_low32'),
        ):
            assert values[batch].dtype == np.float32 and values[batch].shape == (3,)
            assert values[batch].tobytes() == values[repeat].tobytes()
            assert values[batch].tobytes() == np.repeat(values[single], 3).tobytes()
    saved = json.loads((output / 'bucketed-scalars.json').read_text())
    assert (
        saved['measurements'][0]['artifact_sha256']
        == hashlib.sha256(artifact.read_bytes()).hexdigest()
    )
