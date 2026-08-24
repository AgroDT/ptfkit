from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, TypeVar, overload

import numpy as np

from ptfkit.texture import prepare_usda_texture


if TYPE_CHECKING:
    from collections.abc import Sequence

    R = TypeVar('R', bound=NamedTuple)

    GoldenCase = tuple[dict[str, Any], dict[str, float], float, float]
    VectorCasePart = tuple[
        dict[str, Any],
        dict[str, float],
        float,
        float,
    ]
    VectorCaseScalar = tuple[*VectorCasePart, np.ndarray]
    VectorCaseTuple = tuple[*VectorCasePart, R]


@overload
def prepare_vector_case(
    cases: Sequence[GoldenCase], *, categorical_inputs: tuple[str, ...] = ()
) -> VectorCaseScalar: ...


@overload
def prepare_vector_case(
    cases: Sequence[GoldenCase],
    result_type: type[R],
    *,
    categorical_inputs: tuple[str, ...] = (),
) -> VectorCaseTuple: ...


def prepare_vector_case(
    cases: Sequence[GoldenCase],
    result_cls: type[R] | None = None,
    *,
    categorical_inputs: tuple[str, ...] = (),
) -> VectorCaseScalar | VectorCaseTuple:
    inputs, expected, rtol, atol = cases[0]
    vector_inputs = {
        name: prepare_usda_texture([value]) if name in categorical_inputs else np.array([value])
        for name, value in inputs.items()
    }
    out: np.ndarray | R

    if result_cls is None:
        out = np.empty(1, dtype=float)
    else:
        field_count = len(result_cls._fields)
        out = result_cls(*(np.empty(1, dtype=float) for _ in range(field_count)))

    return vector_inputs, expected, rtol, atol, out
