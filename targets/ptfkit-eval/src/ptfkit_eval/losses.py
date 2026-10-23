"""Predeclared per-sample retention loss for grouped candidate selection."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING, Literal

from .metrics import summarize_retention_errors


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from .metrics import RetentionComparison


_MINIMUM_INTEGRATION_POINTS = 2


class RetentionLossError(ValueError):
    """Raised when a registered selection loss has an invalid domain or policy."""


def mean_finite_losses(values: Sequence[float]) -> float:
    """Average finite nonnegative sample losses without overflowing their sum."""
    if not values or any(not math.isfinite(value) or value < 0 for value in values):
        message = 'A loss mean requires nonempty finite nonnegative values.'
        raise RetentionLossError(message)
    try:
        return math.fsum(values) / len(values)
    except OverflowError:
        scale = max(values)
        return scale * (math.fsum(value / scale for value in values) / len(values))


def log10_pressure_span(lower: float, upper: float) -> float:
    """Preserve positive spans for nearby representable positive pressures."""
    if upper <= 2 * lower:
        return math.log1p((upper - lower) / lower) / math.log(10)
    return math.log10(upper) - math.log10(lower)


@dataclass(frozen=True, kw_only=True)
class LogPressureLossPlan:
    """Mean squared point error integrated linearly over log10 pressure."""

    lower_suction_kpa: float
    upper_suction_kpa: float
    minimum_points: int = 2
    method: Literal['log10_trapezoid_mse_v1'] = 'log10_trapezoid_mse_v1'

    def __post_init__(self) -> None:
        """Require a positive finite domain with exact observed endpoints."""
        if (
            not math.isfinite(self.lower_suction_kpa)
            or not math.isfinite(self.upper_suction_kpa)
            or isinstance(self.lower_suction_kpa, bool)
            or isinstance(self.upper_suction_kpa, bool)
            or not 0 < self.lower_suction_kpa < self.upper_suction_kpa
        ):
            message = 'Log-pressure loss requires finite ordered positive pressure bounds.'
            raise RetentionLossError(message)
        if (
            isinstance(self.minimum_points, bool)
            or not isinstance(self.minimum_points, int)
            or self.minimum_points < _MINIMUM_INTEGRATION_POINTS
        ):
            message = 'Log-pressure loss requires at least two distinct pressure points.'
            raise RetentionLossError(message)
        if self.method != 'log10_trapezoid_mse_v1':
            message = 'Unsupported retention selection loss.'
            raise RetentionLossError(message)


@dataclass(frozen=True)
class SampleCurveLoss:
    """One sample's registered pressure-domain loss or exact failure reason."""

    source_id: str
    sample_id: str
    point_count: int
    loss: float | None
    reason: Literal['insufficient_points', 'missing_domain_endpoints'] | None


def evaluate_log_pressure_loss(
    comparisons: Iterable[RetentionComparison],
    *,
    plan: LogPressureLossPlan,
) -> tuple[SampleCurveLoss, ...]:
    """Integrate squared errors on the observed grid and normalize by log span.

    No endpoints are interpolated or extrapolated. Samples require observations
    at both declared domain endpoints. Within a valid sample, the trapezoid rule
    integrates the piecewise-linear squared-error diagnostic over log10 pressure.
    Each sample later has equal selection weight. This differs deliberately from
    the descriptive point-grid RMSE API.
    """
    points = tuple(comparisons)
    if not points:
        return ()
    summarize_retention_errors(points)
    groups: dict[tuple[str, str], list[RetentionComparison]] = defaultdict(list)
    for point in points:
        groups[point.source_id, point.sample_id].append(point)
    result: list[SampleCurveLoss] = []
    span = log10_pressure_span(plan.lower_suction_kpa, plan.upper_suction_kpa)
    for (source, sample), sample_points in sorted(groups.items()):
        domain = sorted(
            (
                point
                for point in sample_points
                if plan.lower_suction_kpa <= point.suction_kpa <= plan.upper_suction_kpa
            ),
            key=lambda point: point.suction_kpa,
        )
        if len(domain) < plan.minimum_points:
            result.append(SampleCurveLoss(source, sample, len(domain), None, 'insufficient_points'))
            continue
        if (
            domain[0].suction_kpa != plan.lower_suction_kpa
            or domain[-1].suction_kpa != plan.upper_suction_kpa
        ):
            result.append(
                SampleCurveLoss(source, sample, len(domain), None, 'missing_domain_endpoints')
            )
            continue
        normalized_loss = math.fsum(
            log10_pressure_span(left.suction_kpa, right.suction_kpa)
            / (2 * span)
            * (point.predicted - point.observed) ** 2
            for left, right in pairwise(domain)
            for point in (left, right)
        )
        result.append(SampleCurveLoss(source, sample, len(domain), normalized_loss, None))
    return tuple(result)
