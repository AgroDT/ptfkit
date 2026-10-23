import math
import random
from dataclasses import replace

import pytest

from ptfkit_eval import (
    ClusterBootstrapPlan,
    RetentionBootstrapError,
    RetentionComparison,
    RetentionMetricsError,
    bootstrap_retention_errors,
)


POINT = RetentionComparison('a', 'one', 10.0, 0.5, 0.375, 'p1')
PLAN = ClusterBootstrapPlan(seed=19, minimum_groups=2, n_resamples=32)


class ExhaustiveTwoClusterDraws:
    """Enumerate AA, AB, BA, BB to make percentile bounds hand-calculable."""

    def __init__(self, seed: int) -> None:
        """Require the declared seed and register all two-cluster draws."""
        assert seed == 19
        self.draws = iter([0, 0, 0, 1, 1, 0, 1, 1])

    def randrange(self, stop: int) -> int:
        """Return the next prescribed cluster index."""
        assert stop == 2
        return next(self.draws)


def test_resamples_whole_clusters_with_multiplicity_and_sample_balanced_errors(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr('ptfkit_eval.uncertainty.random.Random', ExhaustiveTwoClusterDraws)
    points = [
        POINT,
        replace(POINT, suction_kpa=100, predicted=0.875),
        replace(POINT, sample_id='two', predicted=0.625),
        replace(POINT, source_id='b', predicted=0.25),
    ]
    result = bootstrap_retention_errors(
        points,
        plan=replace(PLAN, n_resamples=4, confidence_level=0.5),
    )

    assert result.status == 'computed'
    assert result.group_count == 2
    assert result.effective_grouping == 'source'
    assert result.summary is not None
    assert result.summary.sample_count == 3
    assert result.summary.metrics.mean_error == pytest.approx(0)
    intervals = result.intervals
    assert intervals is not None
    # A has two samples, B one. AB/BA ME=0, rather than the mean of source MEs.
    assert (intervals.mean_error.lower, intervals.mean_error.upper) == pytest.approx(
        (-1 / 16, 1 / 32)
    )
    assert (
        intervals.mean_absolute_error.lower,
        intervals.mean_absolute_error.upper,
    ) == pytest.approx((13 / 64, 7 / 32))
    mixed_rmse = math.sqrt(5 / 96)
    assert (
        intervals.root_mean_squared_error.lower,
        intervals.root_mean_squared_error.upper,
    ) == pytest.approx((math.sqrt(3) / 32 + 0.75 * mixed_rmse, 0.75 * mixed_rmse + 1 / 16))
    assert (
        intervals.median_absolute_error.lower,
        intervals.median_absolute_error.upper,
    ) == pytest.approx((11 / 64, 13 / 64))


def test_fixed_seed_is_order_independent_and_does_not_touch_global_random_state():
    points = [POINT, replace(POINT, source_id='b', predicted=0.75)]
    state = random.getstate()
    result = bootstrap_retention_errors(points, plan=PLAN)

    assert result == bootstrap_retention_errors(reversed(points), plan=PLAN)
    assert random.getstate() == state
    assert result.plan == PLAN
    assert result.method == 'cluster_percentile_linear_v1'


def test_profile_ids_are_nested_within_source_and_samples_remain_in_their_profile():
    points = [
        POINT,
        replace(POINT, sample_id='two'),
        replace(POINT, profile_id='p2', sample_id='three'),
        replace(POINT, source_id='b'),
    ]
    result = bootstrap_retention_errors(
        points, plan=replace(PLAN, grouping='profile', minimum_groups=3)
    )

    assert result.status == 'computed'
    assert result.group_count == 3
    assert result.summary is not None
    assert result.summary.profile_count == 3
    assert result.summary.samples_without_profile_count == 0
    assert result.effective_grouping == 'profile'


def test_source_fallback_regroups_every_sample_instead_of_mixing_sources_and_profiles():
    points = [
        POINT,
        replace(POINT, sample_id='two', profile_id='p2'),
        replace(POINT, source_id='b', profile_id=None),
    ]
    result = bootstrap_retention_errors(
        points,
        plan=replace(PLAN, grouping='profile', missing_profiles='source'),
    )

    assert result.group_count == 2
    assert result.effective_grouping == 'source'
    assert result.status == 'computed'
    assert result.summary is not None
    assert result.summary.samples_without_profile_count == 1
    assert result.summary.profile_count == 2
    assert result.intervals == bootstrap_retention_errors(points, plan=PLAN).intervals


def test_missing_profiles_do_not_silently_trigger_fallback():
    result = bootstrap_retention_errors(
        [POINT, replace(POINT, source_id='b', profile_id=None)],
        plan=replace(PLAN, grouping='profile'),
    )

    assert result.status == 'insufficient_evidence'
    assert result.reason == 'missing_profile_ids'
    assert result.intervals is None


def test_evidence_gate_counts_clusters_instead_of_points_or_samples():
    result = bootstrap_retention_errors(
        [replace(POINT, sample_id=str(index)) for index in range(10)],
        plan=PLAN,
    )

    assert result.status == 'insufficient_evidence'
    assert result.group_count == 1
    assert result.reason == 'too_few_groups'
    assert result.intervals is None
    assert result.summary is not None
    assert result.summary.sample_count == 10


def test_empty_common_cohort_reports_insufficient_evidence():
    result = bootstrap_retention_errors([], plan=PLAN)

    assert result.reason == 'empty_cohort'
    assert result.status == 'insufficient_evidence'
    assert result.summary is None
    assert result.intervals is None


@pytest.mark.parametrize(
    'plan_changes',
    [
        {'minimum_groups': 1},
        {'minimum_groups': True},
        {'minimum_groups': 2.5},
        {'n_resamples': 1},
        {'n_resamples': True},
        {'seed': True},
        {'seed': 2.5},
        {'confidence_level': 0},
        {'confidence_level': 1},
        {'confidence_level': math.nan},
        {'confidence_level': math.inf},
        {'confidence_level': True},
        {'grouping': 'sample'},
        {'missing_profiles': 'ignore'},
    ],
)
def test_rejects_invalid_plans(plan_changes: dict[str, object]):
    with pytest.raises(RetentionBootstrapError):
        replace(PLAN, **plan_changes)


@pytest.mark.parametrize(
    'points',
    [[POINT, POINT], [POINT, replace(POINT, suction_kpa=100, profile_id='conflicting')]],
)
def test_validation_runs_before_the_insufficient_group_gate(points: list[RetentionComparison]):
    with pytest.raises(RetentionMetricsError):
        bootstrap_retention_errors(points, plan=PLAN)
