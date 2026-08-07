from __future__ import annotations

from collections.abc import Callable

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.pidgeon1972 import (
    calc_ptf_pidgeon1972_awc,
    calc_ptf_pidgeon1972_awc_coarse_sand,
    calc_ptf_pidgeon1972_awc_fine_sand,
    calc_ptf_pidgeon1972_awc_sand_organic_matter,
    calc_ptf_pidgeon1972_awc_very_fine_sand,
    calc_ptf_pidgeon1972_eawc,
    calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter,
    calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter,
    calc_ptf_pidgeon1972_eawc_sand,
    calc_ptf_pidgeon1972_eawc_sand_organic_matter,
    calc_ptf_pidgeon1972_fc,
    calc_ptf_pidgeon1972_fc_sand,
    calc_ptf_pidgeon1972_fc_sand_organic_matter,
    calc_ptf_pidgeon1972_fc_vol_sand_organic_matter,
    calc_ptf_pidgeon1972_pwp,
    calc_ptf_pidgeon1972_pwp_sand,
    calc_ptf_pidgeon1972_pwp_sand_organic_matter,
)


ATOL = 1e-12
RTOL = 1e-12
Case = tuple[Callable[..., np.floating | np.ndarray], dict[str, float], float]
CASES: list[Case] = [
    (calc_ptf_pidgeon1972_fc, {'silt': 30.0, 'clay': 20.0, 'organic_matter': 2.0}, 21.26),
    (calc_ptf_pidgeon1972_fc_sand, {'sand': 50.0}, 23.66),
    (
        calc_ptf_pidgeon1972_fc_sand_organic_matter,
        {'sand': 50.0, 'organic_matter': 2.0},
        23.27,
    ),
    (
        calc_ptf_pidgeon1972_fc_vol_sand_organic_matter,
        {'sand': 50.0, 'organic_matter': 2.0},
        31.19,
    ),
    (calc_ptf_pidgeon1972_pwp, {'silt': 30.0, 'clay': 20.0, 'organic_matter': 2.0}, 11.11),
    (calc_ptf_pidgeon1972_pwp_sand, {'sand': 50.0}, 13.91),
    (
        calc_ptf_pidgeon1972_pwp_sand_organic_matter,
        {'sand': 50.0, 'organic_matter': 2.0},
        15.28,
    ),
    (calc_ptf_pidgeon1972_awc, {'clay': 20.0, 'organic_matter': 2.0}, 151.48),
    (
        calc_ptf_pidgeon1972_awc_sand_organic_matter,
        {'sand': 50.0, 'organic_matter': 2.0},
        109.24,
    ),
    (calc_ptf_pidgeon1972_awc_coarse_sand, {'coarse_sand': 20.0}, 115.1),
    (calc_ptf_pidgeon1972_awc_fine_sand, {'fine_sand': 20.0}, 119.9),
    (calc_ptf_pidgeon1972_awc_very_fine_sand, {'very_fine_sand': 10.0}, 112.7),
    (calc_ptf_pidgeon1972_eawc, {'silt': 30.0, 'clay': 20.0, 'organic_matter': 2.0}, 16.12),
    (calc_ptf_pidgeon1972_eawc_sand, {'sand': 50.0}, 51.7),
    (
        calc_ptf_pidgeon1972_eawc_sand_organic_matter,
        {'sand': 50.0, 'organic_matter': 2.0},
        56.26,
    ),
    (
        calc_ptf_pidgeon1972_eawc_coarse_sand_organic_matter,
        {'coarse_sand': 20.0, 'organic_matter': 2.0},
        53.72,
    ),
    (
        calc_ptf_pidgeon1972_eawc_fine_sand_organic_matter,
        {'fine_sand': 20.0, 'organic_matter': 2.0},
        59.58,
    ),
]


@pytest.mark.parametrize(('function', 'kwargs', 'expected'), CASES)
def test_scalar(
    function: Callable[..., np.floating | np.ndarray], kwargs: dict[str, float], expected: float
):
    result = function(**kwargs)

    assert isinstance(result, np.floating)
    assert result == pytest.approx(expected, rel=RTOL, abs=ATOL)


@pytest.mark.parametrize(('function', 'kwargs', '_expected'), CASES)
def test_array_and_broadcasting(
    function: Callable[..., np.floating | np.ndarray],
    kwargs: dict[str, float],
    _expected: float,
):
    first_name, *remaining_names = kwargs
    array_kwargs: dict[str, float | np.ndarray] = {
        first_name: np.array([kwargs[first_name], kwargs[first_name] + 1.0]),
        **{name: kwargs[name] for name in remaining_names},
    }
    result = function(**array_kwargs)
    expected = np.array(
        [
            function(**kwargs),
            function(**{**kwargs, first_name: kwargs[first_name] + 1.0}),
        ]
    )

    assert isinstance(result, np.ndarray)
    npt.assert_allclose(result, expected, rtol=RTOL, atol=ATOL)


@pytest.mark.parametrize(('function', 'kwargs', '_expected'), CASES)
def test_out(
    function: Callable[..., np.floating | np.ndarray],
    kwargs: dict[str, float],
    _expected: float,
):
    array_kwargs = {name: np.array([value, value + 1.0]) for name, value in kwargs.items()}
    expected = function(**array_kwargs)
    assert isinstance(expected, np.ndarray)
    out = np.empty(2, dtype=float)

    result = function(**array_kwargs, out=out)

    assert result is out
    npt.assert_allclose(out, expected, rtol=RTOL, atol=ATOL)
