from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, NamedTuple, TypeVar, overload

import numpy as np

from ptfkit.enums import EnumArray


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

    R = TypeVar('R', bound=NamedTuple)

    Acceptance = dict[str, tuple[float, float, bool]]
    GoldenCase = tuple[Mapping[str, Any], Acceptance]
    VectorCasePart = tuple[
        dict[str, Any],
        Acceptance,
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
    inputs, acceptance = cases[0]
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

    return vector_inputs, acceptance, out
