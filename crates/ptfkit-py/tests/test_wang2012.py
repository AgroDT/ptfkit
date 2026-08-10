from __future__ import annotations

import numpy as np
import numpy.testing as npt

from ptfkit.wang2012 import Wang2012PTFResult, calc_ptf_wang2012


ATOL = 1.0e-12
RTOL = 1.0e-6
INPUTS = {
    'sand': 85.0,
    'silt': 10.0,
    'clay': 5.0,
    'bulk_density': 1.22,
    'soil_organic_carbon': 0.033,
    'altitude': 1193.0,
}
EXPECTED = np.array([0.61540575, 0.38491949, 3.872974e-05])
FIELDS = ('theta_s', 'theta_fc', 'k_sat')


def test_scalar_golden_case_and_result_contract():
    result = calc_ptf_wang2012(**INPUTS)

    assert isinstance(result, Wang2012PTFResult)
    assert result._fields == FIELDS
    assert all(isinstance(value, np.floating) for value in result)
    npt.assert_allclose(result, EXPECTED, rtol=RTOL, atol=ATOL)


def test_array_broadcasting():
    result = calc_ptf_wang2012(
        sand=np.full((2, 1), INPUTS['sand']),
        silt=np.full((1, 3), INPUTS['silt']),
        clay=INPUTS['clay'],
        bulk_density=INPUTS['bulk_density'],
        soil_organic_carbon=INPUTS['soil_organic_carbon'],
        altitude=INPUTS['altitude'],
    )

    assert isinstance(result, Wang2012PTFResult)
    for actual, expected in zip(result, EXPECTED, strict=True):
        assert isinstance(actual, np.ndarray)
        assert actual.shape == (2, 3)
        npt.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL)


def test_out_reuses_result_arrays():
    inputs = {name: np.full(2, value) for name, value in INPUTS.items()}
    out = Wang2012PTFResult(*(np.empty(2) for _ in FIELDS))

    result = calc_ptf_wang2012(**inputs, out=out)

    assert isinstance(result, Wang2012PTFResult)
    for actual, target, expected in zip(result, out, EXPECTED, strict=True):
        assert actual is target
        npt.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL)
