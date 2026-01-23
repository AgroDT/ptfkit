import pytest

from ptfkit.wang2012 import calc_ptf_wang2012


@pytest.mark.parametrize(
    ('sand', 'silt', 'clay', 'bulk_density', 'soil_organic_carbon', 'altitude', 'expected'),
    [
        pytest.param(
            85.0,
            10.0,
            5.0,
            1.22,
            0.033,
            1193,
            (61.540575, 38.491949, 3.872974e-05),
            id='Loamy sand',
        ),
        pytest.param(
            50.6,
            39.2,
            10.2,
            1.35,
            0.742,
            1193,
            (51.071502, 24.608724, 1.751326e-05),
            id='Loam',
        ),
        pytest.param(
            15.5,
            67.4,
            17.1,
            1.24,
            1.231,
            1391,
            (54.682452, 29.285901, 9.934949e-06),
            id='Silt loam',
        ),
    ],
)
def test_calc_ptf_wang2012(
    sand: float,
    silt: float,
    clay: float,
    bulk_density: float,
    soil_organic_carbon: float,
    altitude: float,
    expected: tuple,
):
    res = calc_ptf_wang2012(
        sand=sand,
        silt=silt,
        clay=clay,
        bulk_density=bulk_density,
        soil_organic_carbon=soil_organic_carbon,
        altitude=altitude,
    )
    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 1e-06
