import numpy as np
import pytest

from ptfkit import _ptfkit
from ptfkit.li2007 import calc_ptf_li2007

calc_ptf_li2007_batch = getattr(_ptfkit, 'calc_ptf_li2007_batch')


@pytest.mark.parametrize('samples', [1, 3, 4, 5, 17])
def test_calc_ptf_li2007_batch_matches_generated_ufunc(samples: int):
    values = np.linspace(1.0, 10.0, samples)
    expected = calc_ptf_li2007(
        sand=values + 20.0,
        silt=values + 10.0,
        clay=values,
        bulk_density=values / 10.0 + 1.0,
        soil_organic_matter=values / 10.0 + 0.1,
    )
    actual = calc_ptf_li2007_batch(
        values + 20.0,
        values + 10.0,
        values,
        values / 10.0 + 1.0,
        values / 10.0 + 0.1,
    )

    for actual_output, expected_output in zip(actual, expected, strict=True):
        np.testing.assert_allclose(actual_output, expected_output, rtol=2e-14, atol=0.0)


def test_calc_ptf_li2007_batch_uses_provided_output_arrays():
    values = np.linspace(1.0, 10.0, 5)
    output = tuple(np.empty_like(values) for _ in range(4))

    actual = calc_ptf_li2007_batch(
        values + 20.0,
        values + 10.0,
        values,
        values / 10.0 + 1.0,
        values / 10.0 + 0.1,
        out=output,
    )

    assert all(
        actual_output is expected_output
        for actual_output, expected_output in zip(actual, output, strict=True)
    )
