from __future__ import annotations

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.aimrun2009 import calc_ptf_aimrun2009


ATOL = 1e-12
RTOL = 1e-8
CASES = [
    ((43.88, 0.94, 12.07, 0.010), 7.358406556179513e-08),
    ((50.21, 1.19, 8.55, 0.007), 3.07872446717209e-08),
    ((58.81, 1.13, 5.12, 0.005), 2.3343051908963327e-08),
    ((47.50, 1.08, 1.43, 0.008), 3.831168764444974e-08),
]


@pytest.mark.parametrize(('inputs', 'expected'), CASES)
def test_calc_ptf_aimrun2009_scalar(inputs: tuple[float, float, float, float], expected: float):
    clay, bulk_density, organic_matter, gmd = inputs
    result = calc_ptf_aimrun2009(
        clay=clay,
        bulk_density=bulk_density,
        organic_matter=organic_matter,
        gmd=gmd,
    )

    assert result == pytest.approx(expected, rel=RTOL, abs=ATOL)


def test_calc_ptf_aimrun2009_array():
    result = calc_ptf_aimrun2009(
        clay=np.array([inputs[0] for inputs, _expected in CASES]),
        bulk_density=np.array([inputs[1] for inputs, _expected in CASES]),
        organic_matter=np.array([inputs[2] for inputs, _expected in CASES]),
        gmd=np.array([inputs[3] for inputs, _expected in CASES]),
    )
    expected = np.array([expected for _inputs, expected in CASES])

    npt.assert_allclose(result, expected, rtol=RTOL, atol=ATOL)


def test_calc_ptf_aimrun2009_broadcasting():
    result = calc_ptf_aimrun2009(
        clay=np.array([43.88, 50.21]),
        bulk_density=np.array([0.94, 1.19]),
        organic_matter=8.55,
        gmd=np.array([0.010, 0.007]),
    )
    expected = np.array(
        [
            calc_ptf_aimrun2009(
                clay=43.88,
                bulk_density=0.94,
                organic_matter=8.55,
                gmd=0.010,
            ),
            calc_ptf_aimrun2009(
                clay=50.21,
                bulk_density=1.19,
                organic_matter=8.55,
                gmd=0.007,
            ),
        ]
    )

    npt.assert_allclose(result, expected, rtol=RTOL, atol=ATOL)


def test_calc_ptf_aimrun2009_out():
    out = np.empty(2, dtype=float)
    result = calc_ptf_aimrun2009(
        clay=np.array([43.88, 50.21]),
        bulk_density=np.array([0.94, 1.19]),
        organic_matter=np.array([12.07, 8.55]),
        gmd=np.array([0.010, 0.007]),
        out=out,
    )

    assert result is out
    npt.assert_allclose(
        out,
        np.array([7.358406556179513e-08, 3.07872446717209e-08]),
        rtol=RTOL,
        atol=ATOL,
    )
