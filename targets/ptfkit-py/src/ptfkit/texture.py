"""Strict preparation of USDA texture classes for adapter-backed PTFs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias, cast

from ptfkit._ptfkit import _prepare_usda_texture


if TYPE_CHECKING:
    from numpy import ndarray


UsdaTextureClass: TypeAlias = Literal[
    'sand',
    'loamy sand',
    'sandy loam',
    'loam',
    'silt loam',
    'silt',
    'sandy clay loam',
    'clay loam',
    'silty clay loam',
    'sandy clay',
    'silty clay',
    'clay',
]

_TOKEN = object()


class PreparedUsdaTexture:
    """Validated, reusable native USDA category codes."""

    __slots__ = ('__codes',)

    def __init__(self, codes: ndarray, token: object) -> None:
        """Store validated native codes for the private construction token."""
        if token is not _TOKEN:
            msg = 'Use prepare_usda_texture() to create prepared texture values.'
            raise TypeError(msg)
        self.__codes = codes

    def __init_subclass__(cls) -> None:
        """Prevent subclasses from weakening the prepared-value invariant."""
        msg = 'PreparedUsdaTexture cannot be subclassed.'
        raise TypeError(msg)

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape retained from the prepared scalar, array, or sequence."""
        return self.__codes.shape


def prepare_usda_texture(values: object) -> PreparedUsdaTexture:
    """Validate exact canonical strings and return reusable native category codes."""
    return PreparedUsdaTexture(_prepare_usda_texture(values), _TOKEN)


def _codes_for_ptf(value: PreparedUsdaTexture) -> ndarray:
    if type(value) is not PreparedUsdaTexture:
        msg = 'categorical PTF inputs require prepare_usda_texture() output'
        raise TypeError(msg)
    return cast('ndarray', object.__getattribute__(value, '_PreparedUsdaTexture__codes'))


__all__ = ['PreparedUsdaTexture', 'UsdaTextureClass', 'prepare_usda_texture']
