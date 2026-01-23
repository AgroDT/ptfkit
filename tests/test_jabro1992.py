import numpy.testing as npt
import pytest

from ptfkit.jabro1992 import calc_ptf_jabro1992


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'silt': 10.0,
                'clay': 5.0,
                'bulk_density': 1.26,
            },
            0.0003849641,
            id='Loamy sand (min BD)',
        ),
        pytest.param(
            {
                'silt': 38.72,
                'clay': 11.05,
                'bulk_density': 1.42,
            },
            9.804038e-06,
            id='Loam',
        ),
        pytest.param(
            {
                'silt': 52.0,
                'clay': 30.0,
                'bulk_density': 1.97,
            },
            7.292436e-09,
            id='Silty clay loam (max silt)',
        ),
        pytest.param(
            {
                'silt': 0.2,
                'clay': 44.0,
                'bulk_density': 1.61,
            },
            2.032824e-05,
            id='Sandy clay (min silt, max clay)',
        ),
    ],
)
def test_valid_calc_ptf_jabro1992(inputs: dict[str, float], expected: float):
    res = calc_ptf_jabro1992(**inputs)
    npt.assert_almost_equal(res, expected, decimal=10)
