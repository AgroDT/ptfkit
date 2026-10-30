"""Descriptive errors for one eligible canonical retention cohort."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING

from .water import canonical_water_contract, within_water_bounds


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


class RetentionMetricsError(ValueError):
    """Raised when comparisons cannot define an unambiguous finite cohort."""


@dataclass(frozen=True)
class RetentionComparison:
    """One eligible comparison in kPa and the declared canonical water fraction.

    Sample identifiers are local to a source. All rows passed to a summary
    must belong to the same candidate, target contract, and evaluation protocol.
    Eligibility, physical compatibility, and lineage are the caller's concern.
    """

    source_id: str
    sample_id: str
    suction_kpa: float
    observed: float
    predicted: float
    profile_id: str | None = None
    water_quantity: str = 'volumetric_water_content'


@dataclass(frozen=True)
class ErrorMetrics:
    """Prediction-minus-observation errors in the cohort's canonical water unit."""

    mean_error: float
    mean_absolute_error: float
    root_mean_squared_error: float
    median_absolute_error: float


@dataclass(frozen=True)
class SampleErrorMetrics:
    """Errors and observed pressure support for one source-local sample."""

    source_id: str
    sample_id: str
    point_count: int
    minimum_suction_kpa: float
    maximum_suction_kpa: float
    metrics: ErrorMetrics
    profile_id: str | None = None


@dataclass(frozen=True)
class RetentionErrorSummary:
    """Descriptive cohort metrics with equal total weight per sample."""

    source_count: int
    sample_count: int
    point_count: int
    samples: tuple[SampleErrorMetrics, ...]
    metrics: ErrorMetrics
    profile_count: int
    samples_without_profile_count: int
    water_quantity: str = 'volumetric_water_content'


def summarize_retention_errors(
    comparisons: Iterable[RetentionComparison],
) -> RetentionErrorSummary:
    """Summarize one preselected cohort without choosing or ranking candidates.

    Within a sample, each distinct pressure has equal weight. Across samples,
    each sample has equal weight, regardless of its pressure-grid density.
    RMSE is the square root of the mean of sample mean squared errors, rather
    than the mean of sample RMSEs. The median uses the same point weights as
    the means; an exact half-weight split averages the two adjacent errors.

    Duplicate sample-pressure keys and nonfinite values are errors, never
    silently dropped. Finite predictions outside [0, 1] remain in the errors.
    These metrics describe observed pressure points, not log-pressure integrals,
    confidence intervals, prediction intervals, or applicability domains.
    """
    groups: dict[tuple[str, str], list[RetentionComparison]] = defaultdict(list)
    profiles: dict[tuple[str, str], str | None] = {}
    seen: set[tuple[str, str, float]] = set()
    quantity: str | None = None
    for point in comparisons:
        _validate_point(point)
        if quantity is not None and point.water_quantity != quantity:
            message = 'Retention comparisons must share one water quantity.'
            raise RetentionMetricsError(message)
        quantity = point.water_quantity
        key = (point.source_id, point.sample_id, point.suction_kpa)
        if key in seen:
            message = f'Duplicate source/sample/pressure comparison: {key!r}.'
            raise RetentionMetricsError(message)
        seen.add(key)
        sample = (point.source_id, point.sample_id)
        if sample in profiles and profiles[sample] != point.profile_id:
            message = f'Inconsistent profile identifiers for sample: {sample!r}.'
            raise RetentionMetricsError(message)
        profiles[sample] = point.profile_id
        groups[sample].append(point)
    if not groups or quantity is None:
        message = 'Retention metrics require at least one comparison.'
        raise RetentionMetricsError(message)

    weighted_errors: list[tuple[float, Fraction]] = []
    samples: list[SampleErrorMetrics] = []
    for (source_id, sample_id), points in sorted(groups.items()):
        points.sort(key=lambda point: point.suction_kpa)
        errors = [(point.predicted - point.observed, Fraction(1, len(points))) for point in points]
        weighted_errors.extend(errors)
        samples.append(
            SampleErrorMetrics(
                source_id,
                sample_id,
                len(points),
                points[0].suction_kpa,
                points[-1].suction_kpa,
                _metrics(errors),
                profiles[source_id, sample_id],
            )
        )
    return RetentionErrorSummary(
        water_quantity=quantity,
        source_count=len({source_id for source_id, _ in groups}),
        sample_count=len(samples),
        point_count=len(seen),
        samples=tuple(samples),
        metrics=_metrics(weighted_errors),
        profile_count=len(
            {(source, profile) for (source, _), profile in profiles.items() if profile}
        ),
        samples_without_profile_count=sum(profile is None for profile in profiles.values()),
    )


def _validate_point(point: RetentionComparison) -> None:
    if not point.source_id.strip() or not point.sample_id.strip():
        message = 'Source and sample identifiers must be nonempty.'
        raise RetentionMetricsError(message)
    if point.profile_id is not None and not point.profile_id.strip():
        message = 'A supplied profile identifier must be nonempty.'
        raise RetentionMetricsError(message)
    values = (point.suction_kpa, point.observed, point.predicted)
    if any(isinstance(value, bool) or not math.isfinite(value) for value in values):
        message = 'Pressure, observed water content, and prediction must be finite numbers.'
        raise RetentionMetricsError(message)
    try:
        canonical_water_contract(point.water_quantity)
    except ValueError as error:
        raise RetentionMetricsError(str(error)) from error
    if point.suction_kpa < 0 or not within_water_bounds(point.observed, point.water_quantity):
        message = (
            'Suction must be nonnegative and observed volume fraction must be in [0, 1]; '
            'gravimetric water content must be nonnegative.'
        )
        raise RetentionMetricsError(message)
    error = point.predicted - point.observed
    if not math.isfinite(error * error):
        message = 'Squared prediction error must be finite.'
        raise RetentionMetricsError(message)


def _metrics(errors: Sequence[tuple[float, Fraction]]) -> ErrorMetrics:
    total_weight = sum((weight for _, weight in errors), Fraction())
    return ErrorMetrics(
        mean_error=math.fsum(error * float(weight / total_weight) for error, weight in errors),
        mean_absolute_error=math.fsum(
            abs(error) * float(weight / total_weight) for error, weight in errors
        ),
        root_mean_squared_error=math.sqrt(
            math.fsum(error * error * float(weight / total_weight) for error, weight in errors)
        ),
        median_absolute_error=_weighted_median(errors, total_weight),
    )


def _weighted_median(errors: Sequence[tuple[float, Fraction]], total_weight: Fraction) -> float:
    absolute_errors = sorted((abs(error), weight) for error, weight in errors)
    cumulative = Fraction()
    for index, (error, weight) in enumerate(absolute_errors):
        cumulative += weight
        if cumulative > total_weight / 2:
            return error
        if cumulative == total_weight / 2:
            return error / 2 + absolute_errors[index + 1][0] / 2
    message = 'Cannot compute a median without positive weights.'
    raise RetentionMetricsError(message)
