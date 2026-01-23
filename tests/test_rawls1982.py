import pytest

from ptfkit.rawls1982 import (
    calc_full_wrc_rawls1982,
    calc_theta_33_rawls1982,
    calc_theta_1500_rawls1982,
)


@pytest.mark.parametrize(
    ('clay', 'organic_matter', 'expected'),
    [
        pytest.param(5.12, 0.1, 0.05318, id='Loamy sand, min OM value'),
        pytest.param(43.88, 0.66, 0.255828, id='Sandy clay'),
        pytest.param(86.56, 1.78, 0.486924, id='Clay'),
        pytest.param(36.63, 12.5, 0.40665, id='Clay loam, max OM value'),
    ],
)
def test_valid_calc_theta_1500(clay: float, organic_matter: float, expected: float):
    res = calc_theta_1500_rawls1982(
        clay=clay,
        organic_matter=organic_matter,
    )
    assert abs(res - expected) < 0.001


@pytest.mark.parametrize(
    ('sand', 'organic_matter', 'theta_1500', 'expected'),
    [
        pytest.param(
            85.0,
            0.1,
            0.05318,
            0.1179896,
            id='Loamy sand, input theta_1500 is predicted',
        ),
        pytest.param(
            45.07,
            0.66,
            0.239,
            0.339407,
            id='Loam, input theta_1500 is real',
        ),
        pytest.param(
            5.0,
            1.78,
            0.486924,
            0.61756528,
            id='Clay, input theta_1500 is predicted',
        ),
        pytest.param(
            5.0,
            1.78,
            0.272,
            0.46282,
            id='Clay, input theta_1500 is real',
        ),
        pytest.param(
            35.0,
            12.5,
            0.40665,
            0.727888,
            id='Clay loam, input theta_1500 is predicted',
        ),
    ],
)
def test_valid_calc_theta_33(
    sand: float,
    organic_matter: float,
    theta_1500: float,
    expected: float,
):
    res = calc_theta_33_rawls1982(sand=sand, organic_matter=organic_matter, theta_1500=theta_1500)
    assert abs(res - expected) < 0.001


@pytest.mark.parametrize(
    ('sand', 'organic_matter', 'bulk_density', 'theta_33', 'theta_1500', 'expected'),
    [
        pytest.param(
            85.0,
            0.66,
            1.22,
            0.091,
            0.033,
            (
                0.247242,
                0.968738,
                0.145588,
                0.10483,
                0.091,
                0.075428,
                0.063192,
                0.052946,
                0.045826,
                0.041824,
                0.038932,
                0.033,
            ),
            id='Loamy sand, input theta from issue',
        ),
        pytest.param(
            50.23,
            1.78,
            1.42,
            0.270,
            0.117,
            (
                0.43456,
                1.173015,
                0.342058,
                0.287534,
                0.27,
                0.224508,
                0.204096,
                0.178258,
                0.158058,
                0.145392,
                0.135846,
                0.117,
            ),
            id='Loam, input theta from issue',
        ),
        pytest.param(
            5.0,
            12.5,
            1.42,
            0.330,
            0.133,
            (
                0.262168,
                1.15072,
                0.35152,
                0.35622,
                0.33,
                0.270348,
                0.26752,
                0.23877,
                0.21297,
                0.19448,
                0.18027,
                0.133,
            ),
            id='Silt loam, input theta from issue, max OM value',
        ),
    ],
)
def test_valid_calc_full_wrc(
    sand: float,
    organic_matter: float,
    bulk_density: float,
    theta_33: float,
    theta_1500: float,
    expected: tuple,
):
    res = calc_full_wrc_rawls1982(
        sand=sand,
        organic_matter=organic_matter,
        bulk_density=bulk_density,
        theta_33=theta_33,
        theta_1500=theta_1500,
    )

    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 0.001
