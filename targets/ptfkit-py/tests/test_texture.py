from __future__ import annotations

import numpy as np
import pytest

from ptfkit.cosby1984 import (
    Cosby1984UnivariatePTFResult,
    calc_ptf_cosby1984_univariate_usda_texture,
)
from ptfkit.texture import PreparedUsdaTexture, _codes_for_ptf, prepare_usda_texture


def test_exact_scalar_and_array_preparation_preserves_shape_and_codes() -> None:
    scalar = prepare_usda_texture('loam')
    array = prepare_usda_texture([['sand', 'loam'], ['silt', 'clay']])

    assert scalar.shape == ()
    assert array.shape == (2, 2)
    assert _codes_for_ptf(scalar).dtype == np.uint8
    assert _codes_for_ptf(scalar).item() == 3
    assert _codes_for_ptf(array).tolist() == [[0, 3], [5, 11]]
    assert not _codes_for_ptf(array).flags.writeable


@pytest.mark.parametrize(
    'invalid',
    [
        'Loam',
        ' loam',
        'loam ',
        'sandy  loam',
        'sandy-loam',
        'sandy_loam',
        'L',
        'fine sandy loam',
        'gravelly loam',
    ],
)
def test_preparation_rejects_every_noncanonical_form(invalid: str) -> None:
    with pytest.raises(ValueError, match=repr(invalid)):
        prepare_usda_texture(invalid)


def test_invalid_array_value_reports_its_index() -> None:
    with pytest.raises(ValueError, match=r"'Loam'.*index 1"):
        prepare_usda_texture(['sand', 'Loam'])


def test_prepared_values_are_sealed_and_reusable() -> None:
    prepared = prepare_usda_texture(['loam', 'sand'])
    first = calc_ptf_cosby1984_univariate_usda_texture(texture_class=prepared)
    second = calc_ptf_cosby1984_univariate_usda_texture(texture_class=prepared)
    assert np.array_equal(first.mean_b, second.mean_b)
    with pytest.raises(TypeError, match='prepare_usda_texture'):
        PreparedUsdaTexture(np.array([3], dtype=np.uint8), object())


@pytest.mark.parametrize('raw', ['loam', np.array(['loam']), np.array([3], dtype=np.uint8)])
def test_ptf_rejects_unprepared_inputs(raw: object) -> None:
    with pytest.raises(TypeError, match='prepare_usda_texture'):
        calc_ptf_cosby1984_univariate_usda_texture(texture_class=raw)  # ty: ignore[no-matching-overload]


def test_adapter_backed_ptf_scalar_array_and_out() -> None:
    scalar = calc_ptf_cosby1984_univariate_usda_texture(texture_class=prepare_usda_texture('loam'))
    assert scalar.mean_b == pytest.approx(5.613)

    prepared = prepare_usda_texture([['loam'], ['sand']])
    result = calc_ptf_cosby1984_univariate_usda_texture(texture_class=prepared)
    assert result.mean_b.shape == (2, 1)
    assert result.mean_b[:, 0] == pytest.approx([5.613, 3.705])

    out = Cosby1984UnivariatePTFResult(*(np.empty((2, 1)) for _ in range(7)))
    returned = calc_ptf_cosby1984_univariate_usda_texture(texture_class=prepared, out=out)
    for actual, expected in zip(returned, out, strict=True):
        assert actual is expected
    assert returned.mean_b[:, 0] == pytest.approx([5.613, 3.705])
