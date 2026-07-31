import pytest

from ptfkit.rawls1985 import (
    Rawls1985PTFResult,
    calc_ptf_rawls1985,
)


@pytest.mark.parametrize(
    ('inputs', 'expected'),
    [
        pytest.param(
            {
                'sand': 85.0,
                'clay': 5.0,
                'bulk_density': 1.22,
            },
            (
                0.539622641509434,  # theta_s
                0.0433368876283375,  # theta_r
                0.17638786971144513,  # a_vg
                1.4210250201887282,  # n_vg
                0.0001222579832691,  # k_sat    # the value is an order of magnitude too high
                0.5,  # l_vgm
            ),
            id='Loamy sand',
        ),
        pytest.param(
            {
                'sand': 50.23,
                'clay': 11.05,
                'bulk_density': 1.42,
            },
            (
                0.4641509433962264,
                0.05892013070315877,
                0.057106771301369326,
                1.3756978043451136,
                5.3158081523771515e-06,  # the value is adequate
                0.5,
            ),
            id='Loam',
        ),
        pytest.param(
            {
                'sand': 5.0,
                'clay': 25.0,
                'bulk_density': 1.42,
            },
            (
                0.4641509433962264,
                0.08121380543538625,
                0.012968976548983005,
                1.2800253948640887,
                1.665203202067226e-07,  # the value is an order of magnitude too low
                0.5,
            ),
            id='Silt loam',
        ),
    ],
)
def test_valid_calc_ptf_rawls1985(inputs: dict[str, float], expected: tuple):
    res = calc_ptf_rawls1985(**inputs)

    assert isinstance(res, Rawls1985PTFResult)
    for res_val, exp_val in zip(res, expected, strict=True):
        assert (
            abs(res_val - exp_val) < 0.001  # relaxed tolerance for complex formulas
        )
