import pytest

from ptfkit.qiao2018 import calc_ptf_qiao2018


@pytest.mark.parametrize(
    ('sand', 'clay', 'bulk_density', 'soil_organic_carbon', 'expected'),
    [
        pytest.param(
            85.0,
            5.0,
            1.22,
            0.21,
            (0.28070022, 0.02046, -6.64346822, 1.503383e-05),
            id='Loamy sand',
        ),
        pytest.param(
            50.23,
            11.05,
            1.42,
            0.65,
            (0.42061217, 0.012106, -11.33758704, 5.494327e-06),
            id='Loam',
        ),
        pytest.param(
            12.88,
            27.12,
            1.48,
            1.02,
            (0.45940846, 0.004216, -12.95467475, 1.856572e-06),
            id='Silt loam',
        ),
    ],
)
def test_valid(
    sand: float,
    clay: float,
    bulk_density: float,
    soil_organic_carbon: float,
    expected: tuple,
):
    res = calc_ptf_qiao2018(
        sand=sand,
        clay=clay,
        bulk_density=bulk_density,
        soil_organic_carbon=soil_organic_carbon,
    )
    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 1e-08
