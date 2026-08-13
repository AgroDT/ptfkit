from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, TypeVar, overload

import numpy as np


if TYPE_CHECKING:
    from collections.abc import Sequence

    R = TypeVar('R', bound=NamedTuple)

    GoldenCase = tuple[dict[str, float], dict[str, float], float, float]
    VectorCasePart = tuple[
        dict[str, np.ndarray],
        dict[str, float],
        float,
        float,
    ]
    VectorCaseScalar = tuple[*VectorCasePart, np.ndarray]
    VectorCaseTuple = tuple[*VectorCasePart, R]


@overload
def prepare_vector_case(cases: Sequence[GoldenCase]) -> VectorCaseScalar: ...


@overload
def prepare_vector_case(cases: Sequence[GoldenCase], result_type: type[R]) -> VectorCaseTuple: ...


def prepare_vector_case(
    cases: Sequence[GoldenCase],
    result_cls: type[R] | None = None,
) -> VectorCaseScalar | VectorCaseTuple:
    inputs, expected, rtol, atol = cases[0]
    vector_inputs = {name: np.array([value]) for name, value in inputs.items()}
    out: np.ndarray | R

    if result_cls is None:
        out = np.empty(1, dtype=float)
    else:
        field_count = len(result_cls._fields)
        out = result_cls(*(np.empty(1, dtype=float) for _ in range(field_count)))

    return vector_inputs, expected, rtol, atol, out
