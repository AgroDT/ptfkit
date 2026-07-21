from __future__ import annotations

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.cosby1984 import Cosby1984UnivariatePTFResult, calc_ptf_cosby1984_univariate


ATOL = 1e-12
RTOL = 1e-8
FIELDS = Cosby1984UnivariatePTFResult._fields
CASES = [
    ((50.0, 30.0, 20.0), (6.09, 1.225, -0.119, 42.6, 2.34, 0.5553, 6.27)),
    ((80.0, 15.0, 5.0), (3.705, 0.832, 0.34, 38.82, 1.59, 0.50715, 7.365)),
]


@pytest.mark.parametrize(('inputs', 'expected'), CASES)
def test_calc_ptf_cosby1984_univariate_scalar(
    inputs: tuple[float, float, float],
    expected: tuple[float, float, float, float, float, float, float],
):
    sand, silt, clay = inputs
    result = calc_ptf_cosby1984_univariate(sand=sand, silt=silt, clay=clay)

    assert isinstance(result, Cosby1984UnivariatePTFResult)
    for field, expected_value in zip(FIELDS, expected, strict=True):
        assert getattr(result, field) == pytest.approx(
            expected_value,
            rel=RTOL,
            abs=ATOL,
        )


def test_calc_ptf_cosby1984_univariate_array():
    result = calc_ptf_cosby1984_univariate(
        sand=np.array([inputs[0] for inputs, _expected in CASES]),
        silt=np.array([inputs[1] for inputs, _expected in CASES]),
        clay=np.array([inputs[2] for inputs, _expected in CASES]),
    )

    for index, field in enumerate(FIELDS):
        expected = np.array([expected[index] for _inputs, expected in CASES])
        npt.assert_allclose(
            getattr(result, field),
            expected,
            rtol=RTOL,
            atol=ATOL,
        )


def test_calc_ptf_cosby1984_univariate_broadcasting():
    result = calc_ptf_cosby1984_univariate(
        sand=np.array([50.0, 80.0]),
        silt=30.0,
        clay=np.array([20.0, 5.0]),
    )

    npt.assert_allclose(result.mean_b, np.array([6.09, 3.705]), rtol=RTOL)
    npt.assert_allclose(result.sd_log_k_sat, np.array([0.5553, 0.5553]), rtol=RTOL)


def test_calc_ptf_cosby1984_univariate_out():
    out = Cosby1984UnivariatePTFResult(*(np.empty(2, dtype=float) for _ in FIELDS))
    result = calc_ptf_cosby1984_univariate(
        sand=np.array([50.0, 80.0]),
        silt=np.array([30.0, 15.0]),
        clay=np.array([20.0, 5.0]),
        out=out,
    )

    assert result is not out
    for result_field, out_field in zip(result, out, strict=True):
        assert result_field is out_field

    npt.assert_allclose(result.mean_theta_s, np.array([42.6, 38.82]), rtol=RTOL)
    npt.assert_allclose(result.sd_theta_s, np.array([6.27, 7.365]), rtol=RTOL)
