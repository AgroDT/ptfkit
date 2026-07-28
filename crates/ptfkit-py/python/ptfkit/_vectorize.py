"""Small NumPy-facing adapters for scalar Rust PTF kernels."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import numpy as np


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from numpy import floating
    from numpy.typing import ArrayLike, NDArray


ResultT = TypeVar('ResultT')


def all_scalar(*values: ArrayLike) -> bool:
    """Return true when every input behaves like a scalar value."""
    return all(np.ndim(value) == 0 for value in values)


def vectorize_scalar_result(
    scalar_fn: Callable[..., float],
    array_fn: Callable[..., NDArray[floating]],
    *inputs: ArrayLike,
    out: ArrayLike | None = None,
) -> floating | NDArray[floating]:
    """Evaluate a scalar-output PTF with scalar fast path and NumPy broadcasting."""
    if out is None and all_scalar(*inputs):
        return scalar_fn(*(float(value) for value in inputs))

    arrays = np.broadcast_arrays(*inputs)
    result = np.asarray(array_fn(*arrays), dtype=float)

    if out is None:
        return result

    np.copyto(out, result)
    return out


def vectorize_namedtuple_result(
    scalar_fn: Callable[..., tuple[float, ...]],
    array_fn: Callable[..., tuple[NDArray[floating], ...]],
    result_type: type[ResultT],
    *inputs: ArrayLike,
    out: Sequence[NDArray[floating]] | None = None,
) -> ResultT:
    """Evaluate a multi-output PTF and return the public NamedTuple result type."""
    if out is None and all_scalar(*inputs):
        return result_type(*scalar_fn(*(float(value) for value in inputs)))

    arrays = np.broadcast_arrays(*inputs)
    result = tuple(np.asarray(field, dtype=float) for field in array_fn(*arrays))

    if out is None:
        return result_type(*result)

    out_items = tuple(out)
    for out_item, result_item in zip(out_items, result, strict=True):
        np.copyto(out_item, result_item)

    return result_type(*out_items)
