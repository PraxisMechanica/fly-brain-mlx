import pytest

from fly_brain.simulation.identifiers import NeuronRow
from fly_brain.simulation.models import Connectome
from fly_brain.simulation.module import build_connectome_silencer
from tests.support.observation_fixtures import fixture

pytestmark = pytest.mark.unit


def payload(value: Connectome) -> tuple[tuple[str, tuple[int, ...], bytes], ...]:
    return tuple(
        (str(array.dtype), array.shape, array.tobytes())
        for array in (
            value.neuron_ids,
            value.sources,
            value.destinations,
            value.counts,
            value.weights_mv,
        )
    )


@pytest.mark.parametrize('empty', (False, True))
@pytest.mark.parametrize(
    'silenced', ((), (NeuronRow(3),), (NeuronRow(3), NeuronRow(3)))
)
def test_owned_service_preserves_outgoing_mask_and_all_input_array_bytes(
    empty: bool, silenced: tuple[NeuronRow, ...]
) -> None:
    connectome = fixture(empty).connectome
    before = payload(connectome)
    silence = build_connectome_silencer()
    constructed = payload(connectome)
    result = silence(connectome, silenced)
    for name in ('neuron_ids', 'sources', 'destinations'):
        assert getattr(result, name) is getattr(connectome, name)
    for original, actual in (
        (connectome.counts, result.counts),
        (connectome.weights_mv, result.weights_mv),
    ):
        values = original.copy()
        if silenced and not empty:
            values[5] = 0
        assert (
            actual is original,
            actual.flags.writeable,
            actual.dtype,
            actual.shape,
            actual.tobytes(),
        ) == (
            False,
            False,
            values.dtype,
            values.shape,
            values.tobytes(),
        )
    observed = payload(connectome)
    assert (constructed, observed) == (before, before)


@pytest.mark.parametrize('row', (NeuronRow(-1), NeuronRow(6)))
def test_owned_service_rejects_invalid_rows_without_mutating_inputs(
    row: NeuronRow,
) -> None:
    connectome = fixture().connectome
    before = payload(connectome)
    with pytest.raises(ValueError, match='Silenced source index is outside'):
        build_connectome_silencer()(connectome, (row,))
    assert payload(connectome) == before
