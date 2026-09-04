from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, TypeVar, overload

import numpy as np

from ptfkit.enums import EnumArray


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    R = TypeVar('R', bound=NamedTuple)

    Expected = dict[str, float]
    PublishedTolerance = dict[str, float]
    VerificationCase = tuple[Mapping[str, Any], Expected, PublishedTolerance]
    VectorCasePart = tuple[
        dict[str, Any],
        Expected,
        PublishedTolerance,
    ]
    VectorCaseScalar = tuple[*VectorCasePart, np.ndarray]
    VectorCaseTuple = tuple[*VectorCasePart, R]


@overload
def prepare_vector_case(cases: Sequence[VerificationCase]) -> VectorCaseScalar: ...


@overload
def prepare_vector_case(
    cases: Sequence[VerificationCase], result_type: type[R]
) -> VectorCaseTuple: ...


def prepare_vector_case(
    cases: Sequence[VerificationCase],
    result_cls: type[R] | None = None,
) -> VectorCaseScalar | VectorCaseTuple:
    inputs, expected, published_tolerance = cases[0]
    vector_inputs = {
        name: (
            EnumArray._from_members(type(value), [value])  # noqa: SLF001
            if isinstance(value, Enum)
            else np.array([value])
        )
        for name, value in inputs.items()
    }
    out: np.ndarray | R

    if result_cls is None:
        out = np.empty(1, dtype=float)
    else:
        field_count = len(result_cls._fields)
        out = result_cls(*(np.empty(1, dtype=float) for _ in range(field_count)))

    return vector_inputs, expected, published_tolerance, out


def assert_close(actual: object, expected: float, published_tolerance: float) -> None:
    actual_float = float(actual)  # ty: ignore[invalid-argument-type]
    assert is_close(actual_float, expected, published_tolerance)


def is_close(actual: float, expected: float, published_tolerance: float = 0.0) -> bool:
    tolerance = published_tolerance + 1e-12 + 1e-5 * abs(expected)
    return abs(actual - expected) <= tolerance
