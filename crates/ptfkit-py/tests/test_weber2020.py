from __future__ import annotations

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.weber2020 import Weber2020PTFResult, calc_ptf_weber2020


ATOL = 1.0e-12
RTOL = 1.0e-12
INPUTS = {
    'theta_r_vgm': 0.05,
    'theta_s_vgm': 0.45,
    'alpha_vgm': 0.02,
    'n_vgm': 1.6,
    'tau_vgm': -0.5,
    'k_s_vgm': 100.0,
}
EXPECTED = np.array(
    [
        0.06267,
        0.38607,
        0.0201472407335197,
        1.71980542683289,
        -0.887,
        172.186857498601,
        0.0190546071796325,
    ]
)
FIELDS = (
    'theta_snc_bw',
    'theta_sc_bw',
    'alpha_bw',
    'n_bw',
    'tau_bw',
    'k_sc_bw',
    'k_snc_bw',
)


def test_scalar_golden_case_and_result_contract():
    result = calc_ptf_weber2020(**INPUTS)

    assert isinstance(result, Weber2020PTFResult)
    assert result._fields == FIELDS
    assert all(isinstance(value, np.floating) for value in result)
    npt.assert_allclose(result, EXPECTED, rtol=RTOL, atol=ATOL)


def test_ndarray_inputs():
    inputs = {name: np.full(2, value) for name, value in INPUTS.items()}

    result = calc_ptf_weber2020(**inputs)

    assert isinstance(result, Weber2020PTFResult)
    for actual, expected in zip(result, EXPECTED, strict=True):
        assert isinstance(actual, np.ndarray)
        assert actual.shape == (2,)
        npt.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL)


def test_mixed_scalar_and_ndarray_broadcasting():
    theta_r_values = np.array([[0.05], [0.1]])
    tau_values = np.array([[-0.5, 0.0, 1.0]])

    result = calc_ptf_weber2020(
        theta_r_vgm=theta_r_values,
        theta_s_vgm=INPUTS['theta_s_vgm'],
        alpha_vgm=INPUTS['alpha_vgm'],
        n_vgm=INPUTS['n_vgm'],
        tau_vgm=tau_values,
        k_s_vgm=INPUTS['k_s_vgm'],
    )

    assert isinstance(result, Weber2020PTFResult)
    assert all(field.shape == (2, 3) for field in result)
    for row, theta_r_vgm in enumerate(theta_r_values[:, 0]):
        for column, tau_vgm in enumerate(tau_values[0]):
            expected = calc_ptf_weber2020(
                **INPUTS
                | {
                    'theta_r_vgm': float(theta_r_vgm),
                    'tau_vgm': float(tau_vgm),
                }
            )
            for actual_field, expected_field in zip(result, expected, strict=True):
                assert actual_field[row, column] == pytest.approx(
                    expected_field,
                    rel=RTOL,
                    abs=ATOL,
                )


def test_out_reuses_result_arrays():
    inputs = {name: np.full(2, value) for name, value in INPUTS.items()}
    expected = calc_ptf_weber2020(**inputs)
    out = Weber2020PTFResult(*(np.empty(2) for _ in FIELDS))

    result = calc_ptf_weber2020(**inputs, out=out)

    assert isinstance(result, Weber2020PTFResult)
    assert result is not out
    for actual, target, expected_field in zip(result, out, expected, strict=True):
        assert actual is target
        npt.assert_allclose(actual, expected_field, rtol=RTOL, atol=ATOL)


def test_positive_tau_is_constrained_before_regression():
    result = calc_ptf_weber2020(**INPUTS | {'tau_vgm': 1.0})

    assert result.tau_bw == pytest.approx(0.0295, rel=RTOL, abs=ATOL)
