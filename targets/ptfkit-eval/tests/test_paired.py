import math
import random
from dataclasses import replace

import pytest

from ptfkit_eval import (
    ClusterBootstrapPlan,
    RetentionBootstrapError,
    RetentionCandidateComparisons,
    RetentionCohortError,
    RetentionComparison,
    RetentionMetricsError,
    TargetSpec,
    bootstrap_paired_retention_errors,
)


TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'mineral_soil', 'bulk_volume')
PLAN = ClusterBootstrapPlan(seed=19, minimum_groups=2, n_resamples=4, confidence_level=0.5)
POINT = RetentionComparison('a', 'one', 10, 0.5, 0.375, 'p1')
LEFT = RetentionCandidateComparisons(
    candidate_id='left',
    dataset_id='synthetic',
    protocol_id='exact',
    target=TARGET,
    comparisons=(
        POINT,
        replace(POINT, suction_kpa=100, predicted=0.875),
        replace(POINT, sample_id='two', predicted=0.625),
        replace(POINT, source_id='b', predicted=0.25),
    ),
)


class ExhaustivePairedDraws:
    """Four resamples AA, AB, BA, BB; exactly one shared draw sequence per pair."""

    def __init__(self, seed: int) -> None:
        """Check the registered seed and enumerate independent cluster draws."""
        assert seed == 19
        self.draws = iter((0, 0, 0, 1, 1, 0, 1, 1))

    def randrange(self, stop: int) -> int:
        """Fail if pairing consumes independent draws for the second candidate."""
        assert stop == 2
        return next(self.draws)


def test_paired_opposite_residuals_have_zero_absolute_metric_differences(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr('ptfkit_eval.paired.random.Random', ExhaustivePairedDraws)
    right = replace(
        LEFT,
        candidate_id='right',
        comparisons=tuple(
            replace(point, predicted=2 * point.observed - point.predicted)
            for point in LEFT.comparisons
        ),
    )
    result = bootstrap_paired_retention_errors(LEFT, right, plan=PLAN)
    assert result.group_count == 2
    assert result.status == 'computed'
    assert result.differences is not None
    assert result.differences.mean_error == pytest.approx(0)
    intervals = result.intervals
    assert intervals is not None
    # Whole-group weighted ME draws are 1/4, 0, 0, -1/2.
    assert (intervals.mean_error.lower, intervals.mean_error.upper) == pytest.approx(
        (-1 / 8, 1 / 16)
    )
    for metric in ('mean_absolute_error', 'root_mean_squared_error', 'median_absolute_error'):
        assert getattr(result.differences, metric) == 0
        interval = getattr(intervals, metric)
        assert (interval.lower, interval.upper) == (0, 0)


def test_nonlinear_metric_difference_is_taken_after_each_replicate_metric(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr('ptfkit_eval.paired.random.Random', ExhaustivePairedDraws)
    right = replace(
        LEFT,
        candidate_id='right',
        comparisons=tuple(replace(point, predicted=0.625) for point in LEFT.comparisons),
    )
    result = bootstrap_paired_retention_errors(LEFT, right, plan=PLAN)
    assert result.differences is not None
    assert result.differences.mean_error == pytest.approx(-1 / 8)
    assert result.differences.mean_absolute_error == pytest.approx(1 / 12)
    assert result.differences.root_mean_squared_error == pytest.approx(math.sqrt(5 / 96) - 1 / 8)
    assert result.differences.median_absolute_error == pytest.approx(1 / 16)
    intervals = result.intervals
    assert intervals is not None
    assert (
        intervals.mean_absolute_error.lower,
        intervals.mean_absolute_error.upper,
    ) == pytest.approx((13 / 64 - 1 / 8, 7 / 32 - 1 / 8))
    assert (
        intervals.root_mean_squared_error.lower,
        intervals.root_mean_squared_error.upper,
    ) == pytest.approx(
        (
            math.sqrt(3) / 32 + 0.75 * math.sqrt(5 / 96) - 1 / 8,
            0.75 * math.sqrt(5 / 96) + 1 / 16 - 1 / 8,
        )
    )
    assert (
        intervals.median_absolute_error.lower,
        intervals.median_absolute_error.upper,
    ) == pytest.approx((11 / 64 - 1 / 8, 13 / 64 - 1 / 8))


def test_reversing_pair_negates_differences_and_swaps_interval_endpoints():
    right = replace(
        LEFT,
        candidate_id='right',
        comparisons=tuple(replace(point, predicted=0.625) for point in LEFT.comparisons),
    )
    state = random.getstate()
    result = bootstrap_paired_retention_errors(LEFT, right, plan=PLAN)
    reverse = bootstrap_paired_retention_errors(right, LEFT, plan=PLAN)
    shuffled = bootstrap_paired_retention_errors(
        replace(LEFT, comparisons=LEFT.comparisons[::-1]),
        replace(right, comparisons=right.comparisons[::-1]),
        plan=PLAN,
    )
    assert result == shuffled
    assert random.getstate() == state
    assert result.intervals is not None
    assert reverse.intervals is not None
    for metric in (
        'mean_error',
        'mean_absolute_error',
        'root_mean_squared_error',
        'median_absolute_error',
    ):
        forward, backward = getattr(result.intervals, metric), getattr(reverse.intervals, metric)
        assert (forward.lower, forward.upper) == pytest.approx((-backward.upper, -backward.lower))


@pytest.mark.parametrize(
    'change',
    ['dataset', 'target', 'protocol', 'observed', 'profile', 'grid', 'duplicate', 'invalid'],
)
def test_malformed_pairs_are_rejected_before_insufficient_evidence(change: str):
    right = replace(LEFT, candidate_id='right')
    if change == 'dataset':
        right = replace(right, dataset_id='other')
    elif change == 'protocol':
        right = replace(right, protocol_id='other')
    elif change == 'target':
        right = replace(right, target=replace(TARGET, material_basis='other'))
    elif change == 'grid':
        right = replace(right, comparisons=right.comparisons[:-1])
    elif change == 'duplicate':
        right = replace(right, comparisons=(*right.comparisons, right.comparisons[0]))
    else:
        changes = {
            'observed': {'observed': 0.25},
            'profile': {'profile_id': 'other'},
            'invalid': {'predicted': math.nan},
        }
        right = replace(
            right,
            comparisons=(replace(right.comparisons[0], **changes[change]), *right.comparisons[1:]),
        )
    with pytest.raises((RetentionBootstrapError, RetentionCohortError, RetentionMetricsError)):
        bootstrap_paired_retention_errors(LEFT, right, plan=replace(PLAN, minimum_groups=99))


def test_evidence_gates_and_explicit_source_fallback():
    right = replace(LEFT, candidate_id='right')
    too_few = bootstrap_paired_retention_errors(LEFT, right, plan=replace(PLAN, minimum_groups=3))
    assert too_few.reason == 'too_few_groups'
    assert too_few.group_count == 2
    assert too_few.intervals is None
    assert too_few.differences is not None
    missing = replace(
        LEFT, comparisons=tuple(replace(point, profile_id=None) for point in LEFT.comparisons)
    )
    profile_plan = replace(PLAN, grouping='profile')
    rejected = bootstrap_paired_retention_errors(
        missing, replace(missing, candidate_id='right'), plan=profile_plan
    )
    assert rejected.reason == 'missing_profile_ids'
    fallback = bootstrap_paired_retention_errors(
        missing,
        replace(missing, candidate_id='right'),
        plan=replace(profile_plan, missing_profiles='source'),
    )
    assert fallback.status == 'computed'
    assert fallback.effective_grouping == 'source'
    assert fallback.group_count == 2
    empty = bootstrap_paired_retention_errors(
        replace(LEFT, comparisons=()),
        replace(right, comparisons=()),
        plan=PLAN,
    )
    assert empty.reason == 'empty_cohort'
    assert empty.differences is None
    assert empty.intervals is None
