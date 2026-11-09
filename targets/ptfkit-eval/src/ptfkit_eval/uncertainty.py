"""Registered cluster-percentile confidence intervals for retention error metrics."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from fractions import Fraction
from typing import TYPE_CHECKING, Literal

from .metrics import ErrorMetrics, RetentionErrorSummary, _metrics, summarize_retention_errors


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from .metrics import RetentionComparison


class RetentionBootstrapError(ValueError):
    """Raised when a bootstrap plan is malformed."""


@dataclass(frozen=True, kw_only=True)
class ClusterBootstrapPlan:
    """Predeclared cluster resampling policy for one eligible cohort.

    ``minimum_groups`` is an explicit evidence gate, not a coverage guarantee.
    Grouping by profile nests profile identifiers within source. If any sample
    lacks a profile, ``source`` fallback regroups the entire cohort by source.
    The default ``reject`` policy instead returns insufficient evidence.
    """

    seed: int
    minimum_groups: int
    grouping: Literal['source', 'profile'] = 'source'
    missing_profiles: Literal['reject', 'source'] = 'reject'
    confidence_level: float = 0.95
    n_resamples: int = 2000

    def __post_init__(self) -> None:
        """Validate all statistical choices before examining comparisons."""
        for name, value, minimum in (
            ('minimum_groups', self.minimum_groups, 2),
            ('n_resamples', self.n_resamples, 2),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                message = f'{name} must be an integer of at least {minimum}.'
                raise RetentionBootstrapError(message)
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            message = 'seed must be an explicitly supplied integer.'
            raise RetentionBootstrapError(message)
        if (
            isinstance(self.confidence_level, bool)
            or not math.isfinite(self.confidence_level)
            or not 0 < self.confidence_level < 1
        ):
            message = 'confidence_level must be finite and strictly between zero and one.'
            raise RetentionBootstrapError(message)
        if self.grouping not in ('source', 'profile'):
            message = 'grouping must be source or profile.'
            raise RetentionBootstrapError(message)
        if self.missing_profiles not in ('reject', 'source'):
            message = 'missing_profiles must be reject or source.'
            raise RetentionBootstrapError(message)


@dataclass(frozen=True)
class MetricConfidenceInterval:
    """Two-sided percentile confidence bounds for a population error metric."""

    lower: float
    upper: float


@dataclass(frozen=True)
class RetentionMetricIntervals:
    """Confidence bounds for each sample-balanced descriptive error metric."""

    mean_error: MetricConfidenceInterval
    mean_absolute_error: MetricConfidenceInterval
    root_mean_squared_error: MetricConfidenceInterval
    median_absolute_error: MetricConfidenceInterval


@dataclass(frozen=True)
class RetentionBootstrapResult:
    """A confidence calculation with its evidence gate and complete plan."""

    plan: ClusterBootstrapPlan
    summary: RetentionErrorSummary | None
    effective_grouping: Literal['source', 'profile']
    group_count: int
    intervals: RetentionMetricIntervals | None
    reason: Literal['empty_cohort', 'missing_profile_ids', 'too_few_groups'] | None
    method: Literal['cluster_percentile_linear_v1'] = 'cluster_percentile_linear_v1'

    @property
    def status(self) -> Literal['computed', 'insufficient_evidence']:
        """Distinguish estimated intervals from missing scientific evidence."""
        return 'computed' if self.intervals is not None else 'insufficient_evidence'


def bootstrap_retention_errors(
    comparisons: Iterable[RetentionComparison],
    *,
    plan: ClusterBootstrapPlan,
) -> RetentionBootstrapResult:
    """Resample whole clusters with replacement, preserving all within-cluster rows.

    Each replicate draws the original number of clusters uniformly. Repeated
    clusters retain their multiplicity. Within each replicate, every sample
    occurrence has equal weight and every pressure within it has equal weight.
    The estimand is the existing sample-balanced metric, not a mean of source
    means. Bounds are equal-tail percentiles with linear interpolation at
    ``(n_resamples - 1) * probability``. These are metric confidence intervals;
    they do not estimate prediction or parameter uncertainty or expand domains.
    """
    points = tuple(comparisons)
    if not points:
        return RetentionBootstrapResult(plan, None, plan.grouping, 0, None, 'empty_cohort')
    summary = summarize_retention_errors(points)
    grouping = plan.grouping
    if grouping == 'profile' and summary.samples_without_profile_count:
        if plan.missing_profiles == 'reject':
            return RetentionBootstrapResult(plan, summary, grouping, 0, None, 'missing_profile_ids')
        grouping = 'source'
    clusters = _cluster_errors(points, grouping)
    if len(clusters) < plan.minimum_groups:
        return RetentionBootstrapResult(
            plan, summary, grouping, len(clusters), None, 'too_few_groups'
        )

    generator = random.Random(plan.seed)  # noqa: S311 - Reproducible statistical resampling.
    replicates: list[ErrorMetrics] = []
    for _ in range(plan.n_resamples):
        errors = [error for _ in clusters for error in clusters[generator.randrange(len(clusters))]]
        replicates.append(_metrics(errors))
    tail = (1 - plan.confidence_level) / 2
    intervals = RetentionMetricIntervals(
        *(
            _percentile_interval([getattr(metrics, name) for metrics in replicates], tail)
            for name in (
                'mean_error',
                'mean_absolute_error',
                'root_mean_squared_error',
                'median_absolute_error',
            )
        )
    )
    return RetentionBootstrapResult(plan, summary, grouping, len(clusters), intervals, None)


def _cluster_errors(
    points: Sequence[RetentionComparison], grouping: Literal['source', 'profile']
) -> tuple[tuple[tuple[float, Fraction], ...], ...]:
    samples: dict[tuple[str, str], list[RetentionComparison]] = defaultdict(list)
    for point in points:
        samples[point.source_id, point.sample_id].append(point)
    clusters: dict[tuple[str, str], list[tuple[float, Fraction]]] = defaultdict(list)
    for (source, _), sample_points in sorted(samples.items()):
        sample_points.sort(key=lambda point: point.suction_kpa)
        profile = sample_points[0].profile_id
        cluster = (source, profile if grouping == 'profile' and profile is not None else '')
        clusters[cluster].extend(
            (point.predicted - point.observed, Fraction(1, len(sample_points)))
            for point in sample_points
        )
    return tuple(tuple(clusters[key]) for key in sorted(clusters))


def _percentile_interval(values: list[float], tail: float) -> MetricConfidenceInterval:
    values.sort()
    return MetricConfidenceInterval(_quantile(values, tail), _quantile(values, 1 - tail))


def _quantile(values: Sequence[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    fraction = position - lower
    return values[lower] * (1 - fraction) + values[upper] * fraction
