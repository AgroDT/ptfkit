from __future__ import annotations

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.jabro1992 import calc_ptf_jabro1992


ATOL = 1e-12
RTOL = 1e-8
CASES = [
    ((10.0, 5.0, 1.26), 0.0003849640675896946),
    ((38.72, 11.05, 1.42), 9.804037952717678e-06),
    ((52.0, 30.0, 1.97), 7.292435947882127e-09),
    ((0.2, 44.0, 1.61), 2.032824027706267e-05),
]


@pytest.mark.parametrize(('inputs', 'expected'), CASES)
def test_calc_ptf_jabro1992_scalar(inputs: tuple[float, float, float], expected: float):
    silt, clay, bulk_density = inputs
    result = calc_ptf_jabro1992(silt=silt, clay=clay, bulk_density=bulk_density)

    assert result == pytest.approx(expected, rel=RTOL, abs=ATOL)


def test_calc_ptf_jabro1992_array():
    result = calc_ptf_jabro1992(
        silt=np.array([inputs[0] for inputs, _expected in CASES]),
        clay=np.array([inputs[1] for inputs, _expected in CASES]),
        bulk_density=np.array([inputs[2] for inputs, _expected in CASES]),
    )
    expected = np.array([expected for _inputs, expected in CASES])

    npt.assert_allclose(result, expected, rtol=RTOL, atol=ATOL)


def test_calc_ptf_jabro1992_broadcasting():
    result = calc_ptf_jabro1992(
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        bulk_density=1.42,
    )
    expected = np.array(
        [
            calc_ptf_jabro1992(silt=10.0, clay=5.0, bulk_density=1.42),
            calc_ptf_jabro1992(silt=38.72, clay=11.05, bulk_density=1.42),
        ]
    )

    npt.assert_allclose(result, expected, rtol=RTOL, atol=ATOL)


def test_calc_ptf_jabro1992_out():
    out = np.empty(2, dtype=float)
    result = calc_ptf_jabro1992(
        silt=np.array([10.0, 38.72]),
        clay=np.array([5.0, 11.05]),
        bulk_density=np.array([1.26, 1.42]),
        out=out,
    )

    assert result is out
    npt.assert_allclose(
        out,
        np.array([0.0003849640675896946, 9.804037952717678e-06]),
        rtol=RTOL,
        atol=ATOL,
    )
