from __future__ import annotations

from enum import Enum

import numpy as np
import pytest

from ptfkit.clapp1978 import UsdaTextureClass, calc_ptf_clapp1978
from ptfkit.enums import EnumArray


class OtherEnum(Enum):
    VALUE = 'value'


def test_enum_values_preserve_canonical_text() -> None:
    assert UsdaTextureClass.SAND.value == 'sand'
    assert UsdaTextureClass.LOAMY_SAND.value == 'loamy sand'


def test_enum_array_is_encoded_once_and_reusable() -> None:
    textures = UsdaTextureClass.array(
        [UsdaTextureClass.SAND, UsdaTextureClass.LOAMY_SAND, UsdaTextureClass.CLAY]
    )

    first = calc_ptf_clapp1978(soil_texture=textures)
    codes = textures._codes_for(UsdaTextureClass)  # noqa: SLF001
    second = calc_ptf_clapp1978(soil_texture=textures)

    assert first.b.tolist() == [4.05, 4.38, 11.4]
    assert second.b.tolist() == first.b.tolist()
    assert textures._codes_for(UsdaTextureClass) is codes  # noqa: SLF001


@pytest.mark.parametrize('value', ['sand', 0, np.array([0], dtype=np.uint32), OtherEnum.VALUE])
def test_enum_input_rejects_untyped_values(value: object) -> None:
    with pytest.raises(TypeError, match='expected UsdaTextureClass'):
        calc_ptf_clapp1978(soil_texture=value)  # ty: ignore[no-matching-overload]


def test_enum_input_rejects_an_array_of_another_enum() -> None:
    values = EnumArray._from_members(OtherEnum, [OtherEnum.VALUE])  # noqa: SLF001

    with pytest.raises(TypeError, match=r'expected EnumArray\[UsdaTextureClass\]'):
        calc_ptf_clapp1978(soil_texture=values)
