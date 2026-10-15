import pytest

from fly_brain.qualification.reference_parameters import model_parameters

pytestmark = [pytest.mark.integration, pytest.mark.reference]


def test_reference_parameters_keep_pinned_order_types_and_fresh_values() -> None:
    expected = (
        ('tauSyn', 5.0),
        ('tDelay', 1.8),
        ('v0', -52.0),
        ('vReset', -52.0),
        ('vRest', -52.0),
        ('vThreshold', -45.0),
        ('tauMem', 20.0),
        ('tRefrac', 2.2),
        ('scalePoisson', 250),
        ('wScale', 0.275),
    )
    first, second = model_parameters(), model_parameters()
    assert tuple(first.items()) == tuple(second.items()) == expected
    assert [type(value) for value in first.values()] == [
        type(value) for _, value in expected
    ]
    assert first is not second
    first['wScale'] = 0
    assert tuple(second.items()) == expected
