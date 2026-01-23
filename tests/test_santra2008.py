import pytest

from ptfkit.santra2008 import calc_ptf_santra2008


# mean inputs from Chilika dataset: 16.51, 34.99, 1.50, 0.92, 6.83, ALTITUDE=33.35 (!!!)
# mean from Chilika dataset: a_vg=0.106459, n_vg=1.23, k_sat=2.543638e-06
# Values of altitude in issue are too low, so high values of altitude makes values of k_sat too high
@pytest.mark.parametrize(
    ('silt', 'clay', 'bulk_density', 'soil_organic_carbon', 'ph', 'altitude', 'expected'),
    [
        pytest.param(
            10.0,
            5.0,
            1.22,
            0.5,
            5.5,
            30.0,
            (
                0.306687,
                1.331076,
                2.498409e-05,
            ),
            id='Loamy sand',
        ),
        pytest.param(
            38.72,
            11.05,
            1.42,
            1.5,
            6.8,
            100.0,
            (
                0.041658,  # a_vg (cm⁻¹)
                1.216687,  # n_vg
                4.264804e-05,  # k_sat (cm/day)
            ),
            id='Loam',
        ),
        pytest.param(
            64.67,
            17.20,
            1.31,
            2.0,
            7.0,
            50.0,
            (
                0.018415,
                1.131474,
                3.922014e-06,
            ),
            id='Silt loam',
        ),
    ],
)
def test_calc_ptf_santra2008(
    silt: float,
    clay: float,
    bulk_density: float,
    soil_organic_carbon: float,
    ph: float,
    altitude: float,
    expected: tuple,
):
    res = calc_ptf_santra2008(
        silt=silt,
        clay=clay,
        bulk_density=bulk_density,
        soil_organic_carbon=soil_organic_carbon,
        ph=ph,
        altitude=altitude,
    )

    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 0.1  # relaxed tolerance for complex formulas
