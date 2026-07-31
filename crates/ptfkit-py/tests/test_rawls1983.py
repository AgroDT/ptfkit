import pytest

from ptfkit.rawls1983 import Rawls1983PTFResult, calc_full_wrc_rawls1983


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'sand': 85.0,
                'clay': 5.0,
                'organic_matter': 0.66,
                'bulk_density': 1.22,
            },
            Rawls1983PTFResult(
                theta_20=0.167514,
                theta_33=0.140112,
                theta_60=0.123492,
                theta_100=0.104958,
                theta_200=0.091492,
                theta_400=0.07773,
                theta_700=0.074072,
                theta_1000=0.071182,
                theta_1500=0.059248,
            ),
            id='Loamy sand',
        ),
        pytest.param(
            {
                'sand': 50.23,
                'clay': 11.05,
                'organic_matter': 1.78,
                'bulk_density': 1.42,
            },
            Rawls1983PTFResult(
                theta_20=0.27051,
                theta_33=0.237069,
                theta_60=0.209532,
                theta_100=0.184981,
                theta_200=0.161537,
                theta_400=0.140914,
                theta_700=0.129638,
                theta_1000=0.122851,
                theta_1500=0.1098,
            ),
            id='Loam',
        ),
        pytest.param(
            {
                'sand': 5.0,
                'clay': 25.0,
                'organic_matter': 12.5,
                'bulk_density': 1.42,
            },
            Rawls1983PTFResult(
                theta_20=0.663022,
                theta_33=0.617304,
                theta_60=0.562996,
                theta_100=0.515786,
                theta_200=0.457656,
                theta_400=0.40687,
                theta_700=0.368324,
                theta_1000=0.346294,
                theta_1500=0.320056,
            ),
            id='Silt loam, max OM',
        ),
        pytest.param(
            {
                'sand': 5.0,
                'clay': 25.0,
                'organic_matter': 12.5,
                'bulk_density': 1.82,
            },
            Rawls1983PTFResult(
                theta_20=0.628662,
                theta_33=0.587784,
                theta_60=0.538516,
                theta_100=0.495106,
                theta_200=0.441376,
                theta_400=0.39427,
                theta_700=0.358204,
                theta_1000=0.337574,
                theta_1500=0.312776,
            ),
            id='Silt loam, max OM, high BD',
        ),
    ],
)
def test_valid_calc_full_wrc(inputs: dict[str, float], expected: Rawls1983PTFResult):
    res = calc_full_wrc_rawls1983(**inputs)

    assert isinstance(res, Rawls1983PTFResult)
    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 0.001
