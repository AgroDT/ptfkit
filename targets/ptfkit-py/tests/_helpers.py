from __future__ import annotations

import numpy as np


TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Sequence

    GoldenCase = tuple[dict[str, float], dict[str, float], float, float]
    VectorCase = tuple[
        dict[str, np.ndarray],
        dict[str, float],
        float,
        float,
        np.ndarray | tuple[np.ndarray, ...],
    ]


def prepare_vector_case(cases: Sequence[GoldenCase], output_count: int) -> VectorCase:
    inputs, expected, rtol, atol = cases[0]
    vector_inputs = {name: np.array([value]) for name, value in inputs.items()}
    out: np.ndarray | tuple[np.ndarray, ...]
    if output_count == 1:
        out = np.empty(1, dtype=float)
    else:
        out = tuple(np.empty(1, dtype=float) for _ in range(output_count))
    return vector_inputs, expected, rtol, atol, out
