from __future__ import annotations

from collections.abc import Callable

import numpy as np
import numpy.testing as npt
import pytest

from ptfkit.beniaich2023 import (
    Beniaich2023PTFResult,
    calc_ptf_beniaich2023_mlr1,
    calc_ptf_beniaich2023_mlr2,
    calc_ptf_beniaich2023_mlr3,
    calc_ptf_beniaich2023_mlr4,
    calc_ptf_beniaich2023_mlr5,
    calc_ptf_beniaich2023_slr1,
    calc_ptf_beniaich2023_slr2,
    calc_ptf_beniaich2023_slr3,
    calc_ptf_beniaich2023_slr4,
    calc_ptf_beniaich2023_slr5,
    calc_ptf_beniaich2023_slr6,
)


ATOL = 1.0e-12
RTOL = 1.0e-12
FIELDS = ('water_saturation', 'water_field_capacity', 'water_wilting_point')
Function = Callable[
    ...,
    Beniaich2023PTFResult[np.floating] | Beniaich2023PTFResult[np.ndarray],
]
Case = tuple[Function, dict[str, float], list[float]]
CASES: list[Case] = [
    (calc_ptf_beniaich2023_slr1, {'clay': 20.0}, [0.57427, 0.17577, 0.09621]),
    (calc_ptf_beniaich2023_slr2, {'silt': 30.0}, [0.68478, 0.24878, 0.16131]),
    (calc_ptf_beniaich2023_slr3, {'sand': 50.0}, [0.60070, 0.18480, 0.11077]),
    (
        calc_ptf_beniaich2023_slr4,
        {'clay': 20.0, 'silt': 30.0},
        [0.74501, 0.30678, 0.19915],
    ),
    (
        calc_ptf_beniaich2023_slr5,
        {'clay': 20.0, 'silt': 40.0},
        [0.68578, 0.241875, 0.16176],
    ),
    (
        calc_ptf_beniaich2023_slr6,
        {'soil_organic_matter': 2.0},
        [0.66749, 0.24009, 0.15562],
    ),
    (
        calc_ptf_beniaich2023_mlr1,
        {'silt': 30.0, 'sand': 50.0, 'soil_organic_matter': 2.0},
        [0.56266, 0.17238, 0.09366],
    ),
    (
        calc_ptf_beniaich2023_mlr2,
        {'sand': 50.0, 'soil_organic_matter': 2.0},
        [0.58954, 0.18025, 0.10825],
    ),
    (
        calc_ptf_beniaich2023_mlr3,
        {'silt': 30.0, 'soil_organic_matter': 2.0},
        [0.67031, 0.24275, 0.15755],
    ),
    (
        calc_ptf_beniaich2023_mlr4,
        {'clay': 20.0, 'soil_organic_matter': 2.0},
        [0.55890, 0.16859, 0.09157],
    ),
    (
        calc_ptf_beniaich2023_mlr5,
        {'clay': 20.0, 'silt': 30.0, 'soil_organic_matter': 2.0},
        [0.56229, 0.17200, 0.09379],
    ),
]


@pytest.mark.parametrize(('function', 'inputs', 'expected'), CASES)
def test_scalar_golden_cases_and_result_contract(
    function: Function, inputs: dict[str, float], expected: list[float]
):
    actual = function(**inputs)

    assert isinstance(actual, Beniaich2023PTFResult)
    assert actual._fields == FIELDS
    assert all(isinstance(value, np.floating) for value in actual)
    npt.assert_allclose(actual, expected, rtol=RTOL, atol=ATOL)


@pytest.mark.parametrize(('function', 'inputs', 'expected'), CASES)
def test_array_inputs_and_broadcasting(
    function: Function, inputs: dict[str, float], expected: list[float]
):
    names = list(inputs)
    array_inputs: dict[str, float | np.ndarray] = dict(inputs)
    array_inputs[names[0]] = np.full((2, 1), inputs[names[0]])
    if len(names) > 1:
        array_inputs[names[1]] = np.full((1, 3), inputs[names[1]])
    else:
        array_inputs[names[0]] = np.full((2, 3), inputs[names[0]])

    actual = function(**array_inputs)

    assert isinstance(actual, Beniaich2023PTFResult)
    for field, target in zip(actual, expected, strict=True):
        assert isinstance(field, np.ndarray)
        assert field.shape == (2, 3)
        npt.assert_allclose(field, target, rtol=RTOL, atol=ATOL)


@pytest.mark.parametrize(('function', 'inputs', 'expected'), CASES)
def test_out_reuses_result_arrays(
    function: Function, inputs: dict[str, float], expected: list[float]
):
    array_inputs = {name: np.full(2, value) for name, value in inputs.items()}
    out = Beniaich2023PTFResult(*(np.empty(2) for _ in FIELDS))

    actual = function(**array_inputs, out=out)

    assert isinstance(actual, Beniaich2023PTFResult)
    for field, target, expected_value in zip(actual, out, expected, strict=True):
        assert field is target
        npt.assert_allclose(field, expected_value, rtol=RTOL, atol=ATOL)


def test_wrapper_is_keyword_only():
    with pytest.raises(TypeError):
        calc_ptf_beniaich2023_slr1(20.0)
