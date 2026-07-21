from __future__ import annotations

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.li2007 import Li2007PTFResult, calc_ptf_li2007


ATOL = 1e-12
RTOL = 1e-8
FIELDS = Li2007PTFResult._fields
CASES = [
    (
        (85.0, 10.0, 5.0, 1.20, 0.21),
        (0.5256803583157499, 0.9491464758307142, 1.1657804980997006, 6.549110367333547e-06),
    ),
    (
        (50.23, 38.72, 11.05, 1.42, 0.65),
        (0.49659526127697506, 0.009519989841950734, 1.1806286355149054, 4.5117324656202257e-07),
    ),
    (
        (12.88, 60.0, 27.12, 1.48, 1.02),
        (0.4053061510618609, 0.0018530400762371828, 1.2080428739797433, 1.5151432632107234e-06),
    ),
]


@pytest.mark.parametrize(('inputs', 'expected'), CASES)
def test_calc_ptf_li2007_scalar(
    inputs: tuple[float, float, float, float, float],
    expected: tuple[float, float, float, float],
):
    sand, silt, clay, bulk_density, soil_organic_matter = inputs
    result = calc_ptf_li2007(
        sand=sand,
        silt=silt,
        clay=clay,
        bulk_density=bulk_density,
        soil_organic_matter=soil_organic_matter,
    )

    assert isinstance(result, Li2007PTFResult)
    for field, expected_value in zip(FIELDS, expected, strict=True):
        assert getattr(result, field) == pytest.approx(
            expected_value,
            rel=RTOL,
            abs=ATOL,
        )


def test_calc_ptf_li2007_array():
    result = calc_ptf_li2007(
        sand=np.array([inputs[0] for inputs, _expected in CASES]),
        silt=np.array([inputs[1] for inputs, _expected in CASES]),
        clay=np.array([inputs[2] for inputs, _expected in CASES]),
        bulk_density=np.array([inputs[3] for inputs, _expected in CASES]),
        soil_organic_matter=np.array([inputs[4] for inputs, _expected in CASES]),
    )

    for index, field in enumerate(FIELDS):
        expected = np.array([expected[index] for _inputs, expected in CASES])
        npt.assert_allclose(
            getattr(result, field),
            expected,
            rtol=RTOL,
            atol=ATOL,
        )


def test_calc_ptf_li2007_broadcasting():
    result = calc_ptf_li2007(
        sand=np.array([85.0, 50.23]),
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        soil_organic_matter=0.65,
        bulk_density=np.array([1.20, 1.42]),
    )
    expected = [
        calc_ptf_li2007(
            sand=85.0,
            silt=10.0,
            clay=5.0,
            soil_organic_matter=0.65,
            bulk_density=1.20,
        ),
        calc_ptf_li2007(
            sand=50.23,
            silt=38.72,
            clay=11.05,
            soil_organic_matter=0.65,
            bulk_density=1.42,
        ),
    ]

    for field in FIELDS:
        npt.assert_allclose(
            getattr(result, field),
            np.array([getattr(item, field) for item in expected]),
            rtol=RTOL,
            atol=ATOL,
        )


def test_calc_ptf_li2007_out():
    out = Li2007PTFResult(*(np.empty(2, dtype=float) for _ in FIELDS))
    result = calc_ptf_li2007(
        sand=np.array([85.0, 50.23]),
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        soil_organic_matter=np.array([0.21, 0.65]),
        bulk_density=np.array([1.20, 1.42]),
        out=out,
    )

    assert result is not out
    for result_field, out_field in zip(result, out, strict=True):
        assert result_field is out_field

    npt.assert_allclose(
        result.theta_s,
        np.array([0.5256803583157499, 0.49659526127697506]),
        rtol=RTOL,
        atol=ATOL,
    )
    npt.assert_allclose(
        result.k_sat,
        np.array([6.549110367333547e-06, 4.5117324656202257e-07]),
        rtol=RTOL,
        atol=ATOL,
    )
