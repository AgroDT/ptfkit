from __future__ import annotations

import numpy as np
import numpy.testing as npt

from ptfkit.puckett1985 import (
    Puckett1985PTFResult,
    calc_ptf_puckett1985,
)


ATOL = 1.0e-12
RTOL = 1.0e-8
INPUTS = {
    'sand': 70.9,
    'fine_sand': 36.4,
    'clay': 11.8,
    'bulk_density': 1.67,
    'porosity': 0.380,
}
EXPECTED = np.array(
    [
        0.34288,
        0.33926,
        0.3938615,
        0.39330438,
        0.34432936,
        0.31153562,
        0.29292896,
        0.2513588,
        0.25187788,
        0.22746346,
        4.2399741e-06,
    ]
)
FIELDS = (
    'theta_0',
    'theta_1',
    'theta_5',
    'theta_10',
    'theta_30',
    'theta_60',
    'theta_100',
    'theta_500',
    'theta_1000',
    'theta_1500',
    'k_sat',
)


def test_scalar_golden_case_and_result_contract():
    result = calc_ptf_puckett1985(**INPUTS)

    assert isinstance(result, Puckett1985PTFResult)
    assert result._fields == FIELDS
    assert all(isinstance(value, np.floating) for value in result)
    npt.assert_allclose(result, EXPECTED, rtol=RTOL, atol=ATOL)


def test_array_broadcasting():
    result = calc_ptf_puckett1985(
        sand=np.full((2, 1), INPUTS['sand']),
        fine_sand=INPUTS['fine_sand'],
        clay=np.full((1, 3), INPUTS['clay']),
        bulk_density=INPUTS['bulk_density'],
        porosity=INPUTS['porosity'],
    )

    assert isinstance(result, Puckett1985PTFResult)
    for actual, expected in zip(result, EXPECTED, strict=True):
        assert isinstance(actual, np.ndarray)
        assert actual.shape == (2, 3)
        npt.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL)


def test_out_reuses_result_arrays():
    inputs = {name: np.full(2, value) for name, value in INPUTS.items()}
    out = Puckett1985PTFResult(*(np.empty(2) for _ in FIELDS))

    result = calc_ptf_puckett1985(**inputs, out=out)

    assert isinstance(result, Puckett1985PTFResult)
    for actual, target, expected in zip(result, out, EXPECTED, strict=True):
        assert actual is target
        npt.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL)
