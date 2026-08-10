from __future__ import annotations

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.tiwary2014 import (
    Tiwary2014PTFResult,
    calc_ptf_tiwary2014_bsr,
    calc_ptf_tiwary2014_igp,
)


ATOL = 1e-12
RTOL = 1e-10
BSR_INPUTS = {
    'clay': 54.9,
    'ph': 7.6,
    'cation_exchange_capacity': 61.6,
    'esp': 7.3,
    'emp': 21.4,
    'excm': 3.32,
}
BSR_EXPECTED = Tiwary2014PTFResult(41.1729, 36.8273, 21.6976, 5.373367e-06)
IGP_INPUTS = {'sand': 37.3, 'bulk_density': 1.674, 'esp': 4.6}
IGP_EXPECTED = 5.103578e-07


def test_bsr_scalar_golden_case():
    result = calc_ptf_tiwary2014_bsr(**BSR_INPUTS)

    assert isinstance(result, Tiwary2014PTFResult)
    assert result._fields == ('w_33', 'w_100', 'w_1500', 'k_sat')
    assert all(isinstance(value, np.floating) for value in result)
    npt.assert_allclose(result, BSR_EXPECTED, rtol=RTOL, atol=ATOL)


def test_bsr_array_and_broadcasting():
    result = calc_ptf_tiwary2014_bsr(
        **{
            **BSR_INPUTS,
            'clay': np.array([[54.9], [55.9]]),
            'esp': np.array([[7.3, 8.3]]),
        }
    )

    assert isinstance(result, Tiwary2014PTFResult)
    assert all(isinstance(value, np.ndarray) for value in result)
    assert all(value.shape == (2, 2) for value in result)
    for row, clay in enumerate((54.9, 55.9)):
        for column, esp in enumerate((7.3, 8.3)):
            expected = calc_ptf_tiwary2014_bsr(**{**BSR_INPUTS, 'clay': clay, 'esp': esp})
            npt.assert_allclose(
                [value[row, column] for value in result], expected, rtol=RTOL, atol=ATOL
            )


def test_bsr_out():
    array_inputs = {name: np.array([value, value + 1.0]) for name, value in BSR_INPUTS.items()}
    expected = calc_ptf_tiwary2014_bsr(**array_inputs)
    out = Tiwary2014PTFResult(*(np.empty(2) for _ in BSR_EXPECTED))

    result = calc_ptf_tiwary2014_bsr(**array_inputs, out=out)

    assert isinstance(result, Tiwary2014PTFResult)
    assert all(actual is target for actual, target in zip(result, out, strict=True))
    for actual, expected_field in zip(result, expected, strict=True):
        npt.assert_allclose(actual, expected_field, rtol=RTOL, atol=ATOL)


def test_igp_scalar_golden_case():
    result = calc_ptf_tiwary2014_igp(**IGP_INPUTS)

    assert isinstance(result, np.floating)
    assert result == pytest.approx(IGP_EXPECTED, rel=RTOL, abs=ATOL)


def test_igp_array_and_broadcasting():
    result = calc_ptf_tiwary2014_igp(
        sand=np.array([[37.3], [38.3]]),
        bulk_density=np.array([[1.674, 1.774]]),
        esp=4.6,
    )
    expected = np.array(
        [
            [
                calc_ptf_tiwary2014_igp(sand=sand, bulk_density=bulk_density, esp=4.6)
                for bulk_density in (1.674, 1.774)
            ]
            for sand in (37.3, 38.3)
        ]
    )

    assert isinstance(result, np.ndarray)
    npt.assert_allclose(result, expected, rtol=RTOL, atol=ATOL)


def test_igp_out():
    inputs = {name: np.array([value, value + 1.0]) for name, value in IGP_INPUTS.items()}
    expected = calc_ptf_tiwary2014_igp(**inputs)
    out = np.empty(2)

    result = calc_ptf_tiwary2014_igp(**inputs, out=out)

    assert result is out
    npt.assert_allclose(out, expected, rtol=RTOL, atol=ATOL)
