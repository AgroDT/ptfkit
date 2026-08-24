from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Generic, TypeVar

import numpy as np


if TYPE_CHECKING:
    from collections.abc import Iterable

    from numpy.typing import NDArray


E = TypeVar('E', bound=Enum)


class EnumArray(Generic[E]):
    """A typed wrapper around an encoded NumPy enum array."""

    __slots__ = ('_codes', '_enum_type')
    _codes: NDArray[np.uint32]
    _enum_type: type[E]

    def __init__(self) -> None:
        """Reject direct construction without typed enum members."""
        message = 'construct enum arrays with EnumType.array(...)'
        raise TypeError(message)

    @classmethod
    def _from_members(cls, enum_type: type[E], values: Iterable[E]) -> EnumArray[E]:
        members = {member: ordinal for ordinal, member in enumerate(enum_type)}

        def ordinal(value: E) -> int:
            if not isinstance(value, enum_type):
                message = f'expected a {enum_type.__name__} member, got {type(value).__name__}'
                raise TypeError(message)
            return members[value]

        codes = np.fromiter((ordinal(value) for value in values), dtype=np.uint32)
        instance = object.__new__(cls)
        instance._enum_type = enum_type  # noqa: SLF001
        instance._codes = codes  # noqa: SLF001
        return instance

    @staticmethod
    def _encode_member(enum_type: type[E], value: E) -> np.uint32:
        for ordinal, member in enumerate(enum_type):
            if value is member:
                return np.uint32(ordinal)
        message = f'expected a {enum_type.__name__} member'
        raise TypeError(message)

    def _codes_for(self, enum_type: type[E]) -> NDArray[np.uint32]:
        if self._enum_type is not enum_type:
            message = (
                f'expected EnumArray[{enum_type.__name__}], '
                f'got EnumArray[{self._enum_type.__name__}]'
            )
            raise TypeError(message)
        return self._codes
