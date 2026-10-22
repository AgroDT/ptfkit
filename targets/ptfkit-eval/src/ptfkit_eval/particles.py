"""Exact particle-size interval composition for predictor contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ParticleSizeInterval:
    """One particle-diameter interval in canonical micrometres."""

    lower: float | None
    upper: float | None
    lower_inclusive: bool
    upper_inclusive: bool

    def __post_init__(self) -> None:
        """Reject non-physical or empty intervals before composition."""
        for label, value in (('lower', self.lower), ('upper', self.upper)):
            if value is not None and (not math.isfinite(value) or value < 0):
                message = f'Particle-size {label} bound must be finite and non-negative.'
                raise ValueError(message)
        if self.lower is not None and self.upper is not None and self.lower >= self.upper:
            message = 'Particle-size lower bound must be smaller than the upper bound.'
            raise ValueError(message)


def exact_particle_size_cover(
    target: ParticleSizeInterval,
    available: tuple[ParticleSizeInterval, ...],
) -> tuple[int, ...] | None:
    """Return the shortest exact, non-overlapping cover of ``target``.

    Returned integers are positions in ``available``. A shared internal
    boundary must belong to exactly one adjacent interval; gaps, overlaps,
    extrapolation, and near-equal numeric boundaries are rejected.
    """
    paths: list[tuple[int, ...]] = []

    def extend(path: tuple[int, ...], current: ParticleSizeInterval) -> None:
        if _same_upper(current, target):
            paths.append(path)
            return
        if _upper_after(current, target):
            return
        for index, candidate in enumerate(available):
            if index in path or not _joins(current, candidate):
                continue
            extend((*path, index), candidate)

    for index, candidate in enumerate(available):
        if _same_lower(candidate, target):
            extend((index,), candidate)
    return min(paths, key=lambda path: (len(path), path)) if paths else None


def _same_lower(left: ParticleSizeInterval, right: ParticleSizeInterval) -> bool:
    return _number(left.lower) == _number(right.lower) and (
        left.lower_inclusive == right.lower_inclusive
    )


def _same_upper(left: ParticleSizeInterval, right: ParticleSizeInterval) -> bool:
    return _number(left.upper) == _number(right.upper) and (
        left.upper_inclusive == right.upper_inclusive
    )


def _upper_after(interval: ParticleSizeInterval, target: ParticleSizeInterval) -> bool:
    if interval.upper is None:
        return target.upper is not None
    if target.upper is None:
        return False
    return Decimal(str(interval.upper)) > Decimal(str(target.upper))


def _joins(left: ParticleSizeInterval, right: ParticleSizeInterval) -> bool:
    return (
        left.upper is not None
        and _number(left.upper) == _number(right.lower)
        and left.upper_inclusive != right.lower_inclusive
    )


def _number(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))
