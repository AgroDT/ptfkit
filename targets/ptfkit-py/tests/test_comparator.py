import pytest

from _helpers import assert_close, resolved_tolerance


@pytest.mark.parametrize(
    ('expected', 'absolute', 'relative', 'tolerance', 'below', 'boundary', 'above'),
    [
        pytest.param(4.0, 0.5, 0.0625, 0.5, 4.25, 4.5, 5.0, id='absolute'),
        pytest.param(4.0, 0.125, 0.25, 1.0, 4.5, 5.0, 6.0, id='relative'),
        pytest.param(-4.0, 0.125, 0.25, 1.0, -4.5, -5.0, -6.0, id='negative'),
        pytest.param(0.0, 0.125, 0.25, 0.125, 0.0625, 0.125, 0.25, id='zero'),
        # At zero, the literal guard is also the exact boundary value.
        pytest.param(0.0, 0.0, 0.0, 1e-14, 5e-15, 1e-14, 2e-14, id='guard'),
    ],
)
def test_independent_tolerances_and_boundaries(
    *,
    expected: float,
    absolute: float,
    relative: float,
    tolerance: float,
    below: float,
    boundary: float,
    above: float,
):
    assert resolved_tolerance(expected, absolute, relative) == tolerance
    metadata = {
        'absolute': absolute,
        'relative': relative,
        'quantity': 'test_quantity',
        'unit': '1',
        'source': 'registry',
    }
    assert_close(below, expected, **metadata)
    assert_close(boundary, expected, **metadata)
    with pytest.raises(AssertionError):
        assert_close(above, expected, **metadata)
