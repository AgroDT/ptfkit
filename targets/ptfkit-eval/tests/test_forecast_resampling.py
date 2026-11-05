from dataclasses import replace

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    GroupedSample,
    GroupMembership,
    GroupMultiplicity,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    resample_grouped_forecasts,
)


SAMPLES = (
    GroupedSample('a', 's0', 'p1'),
    GroupedSample('a', 'missing', 'p1'),
    GroupedSample('a', 's2', 'p2'),
    GroupedSample('b', 's0', 'p1'),
)
GROUPS = (
    GroupMembership(('a', 'p1'), (('a', 's0'), ('a', 'missing'))),
    GroupMembership(('a', 'p2'), (('a', 's2'),)),
    GroupMembership(('b', 'p1'), (('b', 's0'),)),
)
COUNTS = tuple(
    GroupMultiplicity(group.group_id, count) for group, count in zip(GROUPS, (2, 0, 1), strict=True)
)
RECORDS = (
    RetentionCandidateComparisons(
        candidate_id='constant',
        dataset_id='mathematical',
        protocol_id='constants',
        target=TargetSpec(
            'volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume'
        ),
        comparisons=tuple(
            RetentionComparison(
                sample.source_id, sample.sample_id, pressure, 0.5, 0.25, sample.profile_id
            )
            for sample in SAMPLES
            if sample.sample_id != 'missing'
            for pressure in (1, 100)
        ),
    ),
)


def test_profile_occurrences_preserve_source_local_groups_and_missing_forecasts():
    result = resample_grouped_forecasts(
        RECORDS, samples=SAMPLES, groups=GROUPS, multiplicities=COUNTS, grouping='profile'
    )
    assert len(result.samples) == 5
    assert len(result.candidates[0].comparisons) == 6
    assert {(sample.source_id, sample.profile_id) for sample in result.samples} == {
        ('a', 'p1'),
        ('b', 'p1'),
    }
    assert [(item.original_sample_id, item.group_occurrence) for item in result.sample_map] == [
        ('missing', 0),
        ('s0', 0),
        ('missing', 1),
        ('s0', 1),
        ('s0', 0),
    ]
    assert len({sample.sample_id for sample in result.samples}) == 5
    copied_missing = {
        item.sample_id for item in result.sample_map if item.original_sample_id == 'missing'
    }
    assert len(copied_missing) == 2
    assert copied_missing.isdisjoint(point.sample_id for point in result.candidates[0].comparisons)
    # Provenance and each observed pressure/value survive; no new eligible rows.
    assert {
        (point.suction_kpa, point.observed, point.predicted)
        for point in result.candidates[0].comparisons
    } == {(1, 0.5, 0.25), (100, 0.5, 0.25)}
    assert result.candidates[0].target == RECORDS[0].target


@pytest.mark.parametrize(
    'counts',
    [
        COUNTS[:-1],
        (replace(COUNTS[0], group_id=('wrong', 'p1')), *COUNTS[1:]),
        (replace(COUNTS[0], count=-1), *COUNTS[1:]),
        (replace(COUNTS[0], count=True), *COUNTS[1:]),
    ],
)
def test_invalid_multiplicities_cannot_silently_change_the_draw(
    counts: tuple[GroupMultiplicity, ...],
):
    with pytest.raises(EvaluationDocumentError, match='multiplicities'):
        resample_grouped_forecasts(
            RECORDS, samples=SAMPLES, groups=GROUPS, multiplicities=counts, grouping='profile'
        )


@pytest.mark.parametrize(
    'bad_group',
    [
        replace(GROUPS[0], samples=(('a', 's0'),)),
        replace(GROUPS[0], samples=(*GROUPS[0].samples, ('a', 's0'))),
        replace(GROUPS[0], group_id=('a', 'p2')),
    ],
)
def test_invalid_original_membership_is_rejected(bad_group: GroupMembership):
    with pytest.raises(EvaluationDocumentError, match=r'roster|membership'):
        resample_grouped_forecasts(
            RECORDS,
            samples=SAMPLES,
            groups=(bad_group, *GROUPS[1:]),
            multiplicities=COUNTS,
            grouping='profile',
        )


def test_forecasts_outside_roster_are_rejected_even_for_zero_count_groups():
    bad = replace(
        RECORDS[0],
        comparisons=(
            *RECORDS[0].comparisons,
            RetentionComparison('outside', 's0', 1, 0.5, 0.25, 'p1'),
        ),
    )
    with pytest.raises(EvaluationDocumentError, match='roster'):
        resample_grouped_forecasts(
            (bad,), samples=SAMPLES, groups=GROUPS, multiplicities=COUNTS, grouping='profile'
        )
