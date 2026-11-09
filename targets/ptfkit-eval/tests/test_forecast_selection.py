from dataclasses import replace
from typing import Literal

import pytest

from ptfkit_eval import (
    ConvexPairPlan,
    EvaluationDocumentError,
    FixedSelectionPlan,
    GroupedSample,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    select_grouped_forecast_candidates,
)


PLAN = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('one', 'zero'),
        folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    ),
    ensembles=(
        ConvexPairPlan(
            id='pair',
            left_candidate_id='one',
            right_candidate_id='zero',
            minimum_training_groups=1,
            minimum_mean_squared_contrast=1e-12,
        ),
    ),
)
TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')


def forecasts():
    # Two low groups of one sample, one high group of three samples. The
    # population weighting differs from equal weighting of the three groups.
    samples = tuple(
        GroupedSample(f'g{group}', f's{index}', 'profile')
        for group, count in enumerate((1, 1, 3))
        for index in range(count)
    )
    records = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id='mathematical',
            protocol_id='constants',
            target=TARGET,
            comparisons=tuple(
                RetentionComparison(
                    sample.source_id,
                    sample.sample_id,
                    pressure,
                    float(sample.source_id == 'g2'),
                    predicted,
                    sample.profile_id,
                )
                for sample in samples
                for pressure in (1, 100)
            ),
        )
        for identifier, predicted in (('one', 1.0), ('zero', 0.0))
    )
    return samples, records


def select(
    samples: tuple[GroupedSample, ...],
    records: tuple[RetentionCandidateComparisons, ...],
    *,
    kinds: dict[str, Literal['atomic', 'ensemble']] | None = None,
):
    return select_grouped_forecast_candidates(
        records,
        samples=samples,
        candidate_kinds={'one': 'atomic', 'zero': 'atomic'} if kinds is None else kinds,
        plan=PLAN,
    )


def test_mathematical_forecasts_refit_sample_weighted_training_only():
    samples, records = forecasts()
    result = select(samples, records)
    assert result.status == 'computed'
    assert len(result.folds) == 3
    for fold in result.folds:
        fit = fold.ensemble.outer_fit
        assert fit is not None
        held_out = {point.source_id for point in fold.ensemble.predictions}
        assert len(held_out) == 1
        # Holding out the high group leaves only zeros; otherwise training has
        # three ones and one zero. These weights detect group weighting and leaks.
        expected = 0.0 if held_out == {'g2'} else 0.75
        assert fit.left_weight == pytest.approx(expected)
        assert {point.predicted for point in fold.ensemble.predictions} == {expected}


@pytest.mark.parametrize('mismatch', ['unknown_sample', 'wrong_profile', 'duplicate_sample'])
def test_forecast_roster_mismatches_are_rejected(mismatch: str):
    samples, records = forecasts()
    if mismatch == 'duplicate_sample':
        samples = (*samples, samples[0])
    else:
        point = records[0].comparisons[0]
        point = replace(
            point,
            **({'sample_id': 'absent'} if mismatch == 'unknown_sample' else {'profile_id': None}),
        )
        records = (
            replace(records[0], comparisons=(point, *records[0].comparisons[1:])),
            records[1],
        )
    with pytest.raises(EvaluationDocumentError, match='roster'):
        select(samples, records)


@pytest.mark.parametrize(
    'kinds',
    [
        {'one': 'atomic'},
        {'one': 'atomic', 'zero': 'atomic', 'pair': 'ensemble'},
        {'one': 'ensemble', 'zero': 'atomic'},
    ],
)
def test_forecast_kinds_require_exact_roster_and_atomic_trainable_members(
    kinds: dict[str, Literal['atomic', 'ensemble']],
):
    samples, records = forecasts()
    with pytest.raises(EvaluationDocumentError, match=r'roster|atomic'):
        select(samples, records, kinds=kinds)


def test_missing_forecasts_preserve_sample_coverage_denominator():
    samples, records = forecasts()
    records = tuple(
        replace(
            record,
            comparisons=tuple(point for point in record.comparisons if point.source_id != 'g2'),
        )
        for record in records
    )
    result = select(samples, records)
    held_out_high = next(
        fold
        for fold in result.folds
        if fold.ensemble.outer_fit is not None
        and fold.ensemble.outer_fit.training_sample_count == 2
    )
    assert held_out_high.ensemble.assessment is not None
    assert held_out_high.ensemble.assessment.coverage == 0
    assert result.status == 'insufficient_evidence'
