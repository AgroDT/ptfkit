"""Whole-cluster paired differences of sample-balanced retention error metrics."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal

from .cohorts import RetentionCandidateComparisons, build_retention_cohorts
from .documents import object_mapping
from .metrics import ErrorMetrics, RetentionErrorSummary, _metrics
from .uncertainty import (
    ClusterBootstrapPlan,
    RetentionBootstrapError,
    RetentionMetricIntervals,
    _cluster_errors,
    _percentile_interval,
)


if TYPE_CHECKING:
    from .runner import RetentionRunResult


@dataclass(frozen=True, kw_only=True)
class PairedComparisonPlan:
    """A preregistered orientation on the exact common cohort of all run candidates."""

    left_candidate_id: str
    right_candidate_id: str
    method: Literal['paired_cluster_percentile_linear_v1'] = 'paired_cluster_percentile_linear_v1'
    cohort: Literal['run_common'] = 'run_common'

    def __post_init__(self) -> None:
        """Require distinct declared identities and supported cohort/resampling rules."""
        if (
            not self.left_candidate_id.strip()
            or not self.right_candidate_id.strip()
            or self.left_candidate_id == self.right_candidate_id
            or self.method != 'paired_cluster_percentile_linear_v1'
            or self.cohort != 'run_common'
        ):
            message = 'Paired comparisons require distinct candidate IDs and supported policies.'
            raise RetentionBootstrapError(message)


@dataclass(frozen=True)
class RetentionMetricDifferences:
    """Signed left-minus-right differences; every component may be negative."""

    mean_error: float
    mean_absolute_error: float
    root_mean_squared_error: float
    median_absolute_error: float


@dataclass(frozen=True)
class PairedRetentionBootstrap:
    """Paired point estimates and percentile intervals, with identical group draws."""

    left: RetentionCandidateComparisons
    right: RetentionCandidateComparisons
    plan: ClusterBootstrapPlan
    effective_grouping: Literal['source', 'profile']
    group_count: int
    left_summary: RetentionErrorSummary | None
    right_summary: RetentionErrorSummary | None
    differences: RetentionMetricDifferences | None
    intervals: RetentionMetricIntervals | None
    reason: Literal['empty_cohort', 'missing_profile_ids', 'too_few_groups'] | None
    method: str = 'paired_cluster_percentile_linear_v1'

    @property
    def status(self) -> str:
        """Distinguish missing interval evidence from a measured zero difference."""
        return 'computed' if self.intervals is not None else 'insufficient_evidence'


def bootstrap_paired_retention_errors(
    left: RetentionCandidateComparisons,
    right: RetentionCandidateComparisons,
    *,
    plan: ClusterBootstrapPlan,
) -> PairedRetentionBootstrap:
    """Resample the same whole clusters for both candidates on an identical grid.

    The caller constructs a common cohort first. Unequal grids are rejected,
    not implicitly intersected. Dataset, target, protocol, observations and
    profiles must agree; invalid records fail before evidence gates. Every
    replicate retains cluster multiplicity and equal sample-occurrence weights.
    Nonlinear RMSE/median differences are computed after both replicate metrics,
    not as metrics of pointwise residual differences. Percentile intervals are
    unadjusted and do not retrain or select candidates within a replicate.
    """
    cohorts = build_retention_cohorts((left, right))
    common = {cohort.candidate_id: cohort for cohort in cohorts.common}
    if any(cohort.exclusions for cohort in cohorts.common):
        message = 'Paired error intervals require identical source/sample/pressure grids.'
        raise RetentionBootstrapError(message)
    left_cohort, right_cohort = common[left.candidate_id], common[right.candidate_id]
    left = replace(left, comparisons=left_cohort.comparisons)
    right = replace(right, comparisons=right_cohort.comparisons)
    one, two = left_cohort.summary, right_cohort.summary
    difference = _difference(one.metrics, two.metrics) if one and two else None
    grouping = plan.grouping
    reason: Literal['empty_cohort', 'missing_profile_ids', 'too_few_groups'] | None = None
    group_count = 0
    if one is None:
        reason = 'empty_cohort'
    elif grouping == 'profile' and one.samples_without_profile_count:
        if plan.missing_profiles == 'reject':
            reason = 'missing_profile_ids'
        else:
            grouping = 'source'
    if reason is not None:
        return PairedRetentionBootstrap(
            left,
            right,
            plan,
            grouping,
            group_count,
            one,
            two,
            difference,
            None,
            reason,
        )
    left_clusters = _cluster_errors(left_cohort.comparisons, grouping)
    right_clusters = _cluster_errors(right_cohort.comparisons, grouping)
    group_count = len(left_clusters)
    if group_count < plan.minimum_groups:
        return PairedRetentionBootstrap(
            left,
            right,
            plan,
            grouping,
            group_count,
            one,
            two,
            difference,
            None,
            'too_few_groups',
        )
    generator = random.Random(plan.seed)  # noqa: S311 - Registered statistical resampling.
    replicates = []
    for _ in range(plan.n_resamples):
        draws = [generator.randrange(group_count) for _ in range(group_count)]
        replicates.append(
            _difference(
                _metrics([point for index in draws for point in left_clusters[index]]),
                _metrics([point for index in draws for point in right_clusters[index]]),
            )
        )
    tail = (1 - plan.confidence_level) / 2
    intervals = RetentionMetricIntervals(
        *(
            _percentile_interval([getattr(value, name) for value in replicates], tail)
            for name in (
                'mean_error',
                'mean_absolute_error',
                'root_mean_squared_error',
                'median_absolute_error',
            )
        )
    )
    return PairedRetentionBootstrap(
        left,
        right,
        plan,
        grouping,
        group_count,
        one,
        two,
        difference,
        intervals,
        None,
    )


def _difference(left: ErrorMetrics, right: ErrorMetrics) -> RetentionMetricDifferences:
    return RetentionMetricDifferences(
        left.mean_error - right.mean_error,
        left.mean_absolute_error - right.mean_absolute_error,
        left.root_mean_squared_error - right.root_mean_squared_error,
        left.median_absolute_error - right.median_absolute_error,
    )


def compare_retention_run_pairs(result: RetentionRunResult) -> tuple[PairedRetentionBootstrap, ...]:
    """Apply preregistered pairs to the run-wide common grid, including empty candidates."""
    if not result.plan.paired_comparisons:
        return ()
    protocol_id = str(object_mapping(result.plan.document['protocol'])['id'])
    records = tuple(
        RetentionCandidateComparisons(
            candidate_id=candidate.id,
            dataset_id=result.plan.dataset.dataset_id,
            protocol_id=protocol_id,
            target=result.plan.dataset.target,
            comparisons=tuple(
                point.comparison
                for point in result.points
                if point.candidate_id == candidate.id and point.comparison is not None
            ),
        )
        for candidate in result.plan.evaluation.candidates
    )
    cohorts = build_retention_cohorts(records)
    common = {cohort.candidate_id: cohort.comparisons for cohort in cohorts.common}
    index = {
        record.candidate_id: RetentionCandidateComparisons(
            candidate_id=record.candidate_id,
            dataset_id=record.dataset_id,
            protocol_id=record.protocol_id,
            target=record.target,
            comparisons=common[record.candidate_id],
        )
        for record in records
    }
    return tuple(
        bootstrap_paired_retention_errors(
            index[policy.left_candidate_id],
            index[policy.right_candidate_id],
            plan=result.plan.bootstrap,
        )
        for policy in result.plan.paired_comparisons
    )
