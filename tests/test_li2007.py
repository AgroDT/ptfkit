import pytest

from ptfkit.li2007 import calc_ptf_li2007


@pytest.mark.parametrize(
    ('sand', 'silt', 'clay', 'som', 'bd', 'expected'),
    [
        pytest.param(
            85.0,
            10.0,
            5.0,
            0.21,
            1.20,
            (0.5256803583157499, 0.9491464758307142, 1.1657804980997006, 6.549110e-06),
            id='Loamy sand',
        ),
        pytest.param(
            50.23,
            38.72,
            11.05,
            0.65,
            1.42,
            (0.49659526127697506, 0.009519989841950734, 1.1806286355149054, 4.511732e-07),
            id='Loam',
        ),
        pytest.param(
            12.88,
            60.00,
            27.12,
            1.02,
            1.48,
            (0.4053061510618609, 0.0018530400762371828, 1.2080428739797433, 1.515143e-06),
            id='Silty clay',
        ),
    ],
)
def test_valid(sand: float, silt: float, clay: float, som: float, bd: float, expected: tuple):
    res = calc_ptf_li2007(sand=sand, silt=silt, clay=clay, soil_organic_matter=som, bulk_density=bd)
    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 1e-08
