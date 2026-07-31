import numpy.testing as npt
import pytest

from ptfkit.ramos2023 import (
    Ramos2023PTFResult,
    calc_ptf_ramos2023_allfcwp,
    calc_ptf_ramos2023_sscbdgmd,
    calc_ptf_ramos2023_sscd,
    calc_ptf_ramos2023_sscgmd,
)


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'coarse_sand': 51,
                'fine_sand': 34,
                'silt': 10,
                'clay': 5,
                'depth': 20,
            },
            Ramos2023PTFResult(
                theta_s=-1.144506,
                theta_r=0.125,
                a_vg=0.0849239,
                n_vg=0.919,
                k_sat=3.955799e-07,
                l_vgm=78.766,
            ),
            id='Loamy sand',
        ),
        pytest.param(
            {
                'coarse_sand': 25,
                'fine_sand': 25,
                'silt': 40,
                'clay': 10,
                'depth': 20,
            },
            Ramos2023PTFResult(
                theta_s=-0.444506,
                theta_r=0.225,
                a_vg=0.000632393,
                n_vg=0.019,
                k_sat=1.459024e-08,
                l_vgm=41.666,
            ),
            id='Loam',
        ),
        pytest.param(
            {
                'coarse_sand': 2,
                'fine_sand': 3,
                'silt': 70,
                'clay': 25,
                'depth': 20,
            },
            Ramos2023PTFResult(
                theta_s=0.455494,
                theta_r=0.525,
                a_vg=1.280084e-05,
                n_vg=-1.481,
                k_sat=5.381342e-10,
                l_vgm=-6.034,
            ),
            id='Silt loam',
        ),
    ],
)
def test_calc_ptf_ramos2023_sscd(
    inputs: dict[str, float],
    expected: tuple,
):
    res = calc_ptf_ramos2023_sscd(**inputs)
    npt.assert_almost_equal(res, expected, decimal=6)


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'coarse_sand': 51,
                'fine_sand': 34,
                'silt': 10,
                'clay': 25,
                'gmd': 0.224,
                'gsd': 6.917,
            },
            Ramos2023PTFResult(
                theta_s=1.336758,
                theta_r=0.4959720,
                a_vg=1.920605e-4,
                n_vg=4.391760,
                k_sat=1.602888e-11,
                l_vgm=-2.437865e1,
            ),
            id='Loamy sand',
        ),
        pytest.param(
            {
                'coarse_sand': 25,
                'fine_sand': 25,
                'silt': 40,
                'clay': 10,
                'gmd': 0.041,
                'gsd': 10.875,
            },
            Ramos2023PTFResult(
                theta_s=1.0897625,
                theta_r=0.3343,
                a_vg=1.282499e-06,
                n_vg=2.499648,
                k_sat=1.265153e-13,
                l_vgm=-67.72275,
            ),
            id='Loam',
        ),
        pytest.param(
            {
                'coarse_sand': 2,
                'fine_sand': 3,
                'silt': 70,
                'clay': 25,
                'gmd': 0.099,
                'gsd': 11.919,
            },
            Ramos2023PTFResult(
                theta_s=1.8968581,
                theta_r=0.576004,
                a_vg=2.834827e-08,
                n_vg=3.75403,
                k_sat=7.502724e-14,
                l_vgm=-109.03155,
            ),
            id='Silt Loam',
        ),
    ],
)
def test_calc_ptf_ramos2023_sscgmd(
    inputs: dict[str, float],
    expected: tuple,
):
    res = calc_ptf_ramos2023_sscgmd(**inputs)
    npt.assert_almost_equal(res, expected, decimal=6)


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'fine_sand': 34,
                'silt': 10,
                'clay': 5,
                'depth': 20,
                'bulk_density': 1.26,
                'gmd': 0.224,
                'gsd': 6.917,
            },
            Ramos2023PTFResult(
                theta_s=-3.063668,
                theta_r=0.1965554,
                a_vg=1.699621e-05,
                n_vg=1.435434,
                k_sat=9.467727e-11,
                l_vgm=-26.20365,
            ),
            id='Loamy sand',
        ),
        pytest.param(
            {
                'fine_sand': 25,
                'silt': 40,
                'clay': 10,
                'depth': 20,
                'bulk_density': 1.42,
                'gmd': 0.041,
                'gsd': 10.875,
            },
            Ramos2023PTFResult(
                theta_s=-3.501068,
                theta_r=0.335175,
                a_vg=7.185038e-08,
                n_vg=0.691605,
                k_sat=7.295977e-13,
                l_vgm=-74.29275,
            ),
            id='Loam',
        ),
        pytest.param(
            {
                'fine_sand': 3,
                'silt': 70,
                'clay': 25,
                'depth': 20,
                'bulk_density': 1.42,
                'gmd': 0.099,
                'gsd': 11.919,
            },
            Ramos2023PTFResult(
                theta_s=-3.282068,
                theta_r=0.5755878,
                a_vg=2.215174e-10,
                n_vg=0.728207,
                k_sat=8.561198e-14,
                l_vgm=-125.45655,
            ),
            id='Silt Loam',
        ),
    ],
)
def test_calc_ptf_ramos2023_sscbdgmd(
    inputs: dict[str, float],
    expected: tuple,
):
    res = calc_ptf_ramos2023_sscbdgmd(**inputs)
    npt.assert_almost_equal(res, expected, decimal=6)


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'fine_sand': 34,
                'silt': 10,
                'clay': 5,
                'bulk_density': 1.26,
                'gmd': 0.224,
                'gsd': 6.917,
                'theta_33': 0.155,
                'theta_1580': 0.045,
            },
            Ramos2023PTFResult(
                theta_s=-2.00844,
                theta_r=0.06767,
                a_vg=1.458543,
                n_vg=2.177876,
                k_sat=4.018259e-09,
                l_vgm=-7.110265,
            ),
            id='Loamy sand',
        ),
        pytest.param(
            {
                'fine_sand': 25,
                'silt': 40,
                'clay': 10,
                'bulk_density': 1.42,
                'gmd': 0.041,
                'gsd': 10.875,
                'theta_33': 0.285,
                'theta_1580': 0.144,
            },
            Ramos2023PTFResult(
                theta_s=-2.34065,
                theta_r=0.35768,
                a_vg=1.838649,
                n_vg=1.269064,
                k_sat=1.340689e-09,
                l_vgm=-28.078048,
            ),
            id='Loam',
        ),
        pytest.param(
            {
                'fine_sand': 3,
                'silt': 70,
                'clay': 25,
                'bulk_density': 1.42,
                'gmd': 0.099,
                'gsd': 11.919,
                'theta_33': 0.198,
                'theta_1580': 0.080,
            },
            Ramos2023PTFResult(
                theta_s=-2.43291,
                theta_r=0.21105,
                a_vg=2.903837,
                n_vg=2.696568,
                k_sat=2.160668e-08,
                l_vgm=-45.14736,
            ),
            id='Silt Loam',
        ),
    ],
)
def test_calc_ptf_ramos2023_allfcwp(
    inputs: dict[str, float],
    expected: tuple,
):
    res = calc_ptf_ramos2023_allfcwp(**inputs)
    npt.assert_almost_equal(res, expected, decimal=6)
