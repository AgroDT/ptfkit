from dataclasses import replace

import pytest

from ptfkit_eval import (
    ClusterBootstrapPlan,
    RetentionCandidateComparisons,
    RetentionCohortError,
    RetentionComparison,
    RetentionMetricsError,
    TargetSpec,
    bootstrap_retention_errors,
    build_retention_cohorts,
)


POINT = RetentionComparison('source', 'sample', 10.0, 0.5, 0.375, 'profile')
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')
CANDIDATE = RetentionCandidateComparisons(
    candidate_id='a',
    dataset_id='synthetic',
    protocol_id='retention_v1',
    target=TARGET,
    comparisons=(POINT,),
)


def test_common_cohort_matches_both_samples_and_pressure_points():
    candidate_a = replace(
        CANDIDATE,
        comparisons=(POINT, replace(POINT, suction_kpa=100), replace(POINT, sample_id='only_a')),
    )
    candidate_b = replace(
        CANDIDATE,
        candidate_id='b',
        comparisons=(replace(POINT, predicted=0.75), replace(POINT, sample_id='only_b')),
    )
    cohorts = build_retention_cohorts([candidate_b, candidate_a])

    assert [cohort.candidate_id for cohort in cohorts.maximal] == ['a', 'b']
    assert [len(cohort.comparisons) for cohort in cohorts.maximal] == [3, 2]
    assert [len(cohort.comparisons) for cohort in cohorts.common] == [1, 1]
    assert [len(cohort.exclusions) for cohort in cohorts.common] == [2, 1]
    assert cohorts.maximal[0].exclusions == ()
    assert cohorts.common[0].comparisons == (POINT,)
    assert cohorts.common[1].comparisons == (replace(POINT, predicted=0.75),)
    assert all(
        exclusion.code == 'point_not_shared_by_all_candidates'
        for cohort in cohorts.common
        for exclusion in cohort.exclusions
    )
    summary_a, summary_b = (cohort.summary for cohort in cohorts.common)
    assert summary_a is not None
    assert summary_b is not None
    assert (summary_a.sample_count, summary_b.sample_count) == (1, 1)
    assert summary_a.metrics.mean_error == pytest.approx(-1 / 8)
    assert summary_b.metrics.mean_error == pytest.approx(1 / 4)
    assert [point.sample_id for point in candidate_a.comparisons] == ['sample', 'sample', 'only_a']


def test_predicted_errors_do_not_choose_common_membership_and_order_is_irrelevant():
    candidate_b = replace(CANDIDATE, candidate_id='b', comparisons=(replace(POINT, predicted=9),))
    cohorts = build_retention_cohorts([CANDIDATE, candidate_b])

    assert cohorts == build_retention_cohorts([candidate_b, CANDIDATE])
    assert cohorts.common[1].comparisons[0].predicted == 9
    assert cohorts.common[1].status == 'ready'


def test_empty_candidate_is_retained_and_prevents_a_spurious_common_comparison():
    cohorts = build_retention_cohorts(
        [CANDIDATE, replace(CANDIDATE, candidate_id='b', comparisons=())]
    )

    assert cohorts.maximal[0].status == 'ready'
    assert cohorts.maximal[1].status == 'empty_cohort'
    assert all(cohort.status == 'empty_cohort' for cohort in cohorts.common)
    assert cohorts.common[0].exclusions[0].comparison == POINT


def test_same_sample_without_shared_pressure_has_no_common_points():
    cohorts = build_retention_cohorts(
        [
            CANDIDATE,
            replace(CANDIDATE, candidate_id='b', comparisons=(replace(POINT, suction_kpa=33),)),
        ]
    )

    assert all(cohort.status == 'empty_cohort' for cohort in cohorts.common)


@pytest.mark.parametrize(
    'candidate',
    [
        replace(CANDIDATE, dataset_id='other'),
        replace(CANDIDATE, protocol_id='other'),
        replace(CANDIDATE, target=replace(TARGET, material_basis='mineral_soil')),
        replace(CANDIDATE, target=replace(TARGET, unit='percent')),
        replace(CANDIDATE, comparisons=(replace(POINT, observed=0.25),)),
        replace(CANDIDATE, comparisons=(replace(POINT, profile_id='different'),)),
        replace(CANDIDATE, comparisons=(replace(POINT, suction_kpa=33, profile_id=None),)),
    ],
)
def test_rejects_incompatible_contracts_or_conflicting_observation_identity(
    candidate: RetentionCandidateComparisons,
):
    with pytest.raises(RetentionCohortError):
        build_retention_cohorts([CANDIDATE, replace(candidate, candidate_id='b')])


def test_rejects_duplicate_keys_before_intersection_can_hide_them():
    duplicate = replace(CANDIDATE, comparisons=(POINT, POINT))
    with pytest.raises(RetentionMetricsError, match='Duplicate'):
        build_retention_cohorts(
            [duplicate, replace(CANDIDATE, candidate_id='empty', comparisons=())]
        )


@pytest.mark.parametrize(
    'candidates', [[], [CANDIDATE, CANDIDATE], [replace(CANDIDATE, candidate_id='')]]
)
def test_rejects_missing_or_ambiguous_candidate_declarations(
    candidates: list[RetentionCandidateComparisons],
):
    with pytest.raises(RetentionCohortError):
        build_retention_cohorts(candidates)


def test_rejects_noncanonical_target_even_for_a_single_candidate():
    with pytest.raises(RetentionCohortError):
        build_retention_cohorts([replace(CANDIDATE, target=replace(TARGET, unit='percent'))])


def test_common_cohort_feeds_intervals_without_reintroducing_excluded_samples():
    shared = (POINT, replace(POINT, source_id='other'))
    cohorts = build_retention_cohorts(
        [
            replace(
                CANDIDATE, comparisons=(*shared, replace(POINT, source_id='only_a', predicted=5))
            ),
            replace(
                CANDIDATE,
                candidate_id='b',
                comparisons=tuple(replace(point, predicted=0.75) for point in shared),
            ),
        ]
    )
    plan = ClusterBootstrapPlan(seed=41, minimum_groups=2, n_resamples=16)
    results = [
        bootstrap_retention_errors(cohort.comparisons, plan=plan) for cohort in cohorts.common
    ]

    assert [result.group_count for result in results] == [2, 2]
    interval_a, interval_b = (result.intervals for result in results)
    assert interval_a is not None
    assert interval_b is not None
    assert (interval_a.mean_error.lower, interval_a.mean_error.upper) == (-0.125, -0.125)
    assert (interval_b.mean_error.lower, interval_b.mean_error.upper) == (0.25, 0.25)
