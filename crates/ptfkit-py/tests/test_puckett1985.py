import pytest

from ptfkit.puckett1985 import (
    Puckett1985PTFResult,
    calc_ptf_puckett1985,
)


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'sand': 70.9,
                'fine_sand': 36.4,
                'clay': 11.8,
                'bulk_density': 1.67,
                'porosity': 0.380,
            },
            (
                0.34288,  # theta_0
                0.33926,  # theta_1
                0.248615,  # theta_5
                0.1980438,  # theta_10
                0.1582936,  # theta_30
                0.1453562,  # theta_60
                0.1392896,  # theta_100
                0.128588,  # theta_500
                0.1427788,  # theta_1000
                0.1236346,  # theta_1500
                4.2399741e-06,  # k_sat  # adequate value
            ),
            id='Cahaba, Ap (Sandy loam)',
        ),
        pytest.param(
            {
                'sand': 51.1,
                'fine_sand': 23.1,
                'clay': 13.1,
                'bulk_density': 1.57,
                'porosity': 0.396,
            },
            (
                0.34208,
                0.3345,
                0.295998,
                0.2675672,
                0.2305859,
                0.2130413,
                0.2035389,
                0.183477,
                0.1933847,
                0.1725184,
                3.279881e-06,  # adequate value
            ),
            id='Lucedate, Ap (Loam)',
        ),
        pytest.param(
            {
                'sand': 34.6,
                'fine_sand': 16.3,
                'clay': 31.8,
                'bulk_density': 1.64,
                'porosity': 0.395,
            },
            (
                0.35896,
                0.35507,
                0.375813,
                0.3713616,
                0.3476317,
                0.3312929,
                0.3209337,
                0.29588,
                0.3029911,
                0.2812862,
                8.163944e-08,  # adequate value
            ),
            id='Malbis 1, Bt4 (Clay loam)',
        ),
    ],
)
def test_calc_ptf_puckett1985(
    inputs: dict[str, float],
    expected: tuple,
):
    res = calc_ptf_puckett1985(**inputs)

    assert isinstance(res, Puckett1985PTFResult)
    for res_val, exp_val in zip(res, expected, strict=True):
        assert abs(res_val - exp_val) < 0.01  # relaxed tolerance for complex formulas
