from __future__ import annotations

from typing import Any

from numpy import asarray, float64, ufunc


def call(function: ufunc, *inputs: object, out: object) -> Any:  # noqa: ANN401
    inputs = tuple(asarray(value, dtype=float64) for value in inputs)
    if out is None:
        return function(*inputs)
    if isinstance(out, tuple):
        out = tuple(out)
    return function(*inputs, out=out)
