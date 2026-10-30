"""Deterministic pressure-based restart locations for piecewise retention fits."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable

    import numpy as np


@dataclass(frozen=True)
class PressureIntervalTrial:
    """Local optimizer limits, separate from scientific parameter bounds."""

    initial: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    air_entry_interval: tuple[float, float] | None = None


def pressure_interval_trials(
    starts: list[np.ndarray],
    lower: np.ndarray,
    upper: np.ndarray,
    *,
    air_index: int,
    pressures: Iterable[float],
) -> list[PressureIntervalTrial]:
    """Keep original solves, then repeat each start inside every pressure cell."""
    trials = [PressureIntervalTrial(start, lower, upper) for start in starts]
    knots = sorted(
        {
            float(lower[air_index]),
            float(upper[air_index]),
            *(float(value) for value in pressures if lower[air_index] < value < upper[air_index]),
        }
    )
    for left, right in pairwise(knots):
        for start in starts:
            initial, local_lower, local_upper = start.copy(), lower.copy(), upper.copy()
            initial[air_index] = math.exp((math.log(left) + math.log(right)) / 2)
            local_lower[air_index], local_upper[air_index] = left, right
            trials.append(PressureIntervalTrial(initial, local_lower, local_upper, (left, right)))
    return trials


def pressure_partition_values(
    pressures: Iterable[float], lower: float, upper: float
) -> tuple[float, ...]:
    """Sample every interior pressure knot and geometric midpoint in the fit box.

    Positive bounds come from a validated air-entry parameter box. Only pressure
    locations participate; observed water content never determines restarts.
    """
    knots = sorted({lower, upper, *(float(value) for value in pressures if lower < value < upper)})
    midpoints = (
        math.exp((math.log(left) + math.log(right)) / 2) for left, right in pairwise(knots)
    )
    return tuple(sorted({*knots[1:-1], *(value for value in midpoints if lower < value < upper)}))
