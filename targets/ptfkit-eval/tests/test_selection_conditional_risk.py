from fractions import Fraction
from typing import cast

import pytest

from ptfkit_eval import (
    BoundedGroupLoss,
    ConditionalOuterFoldLoss,
    ConditionalOuterRiskPlan,
    ConvexPairFit,
    ConvexPairPlan,
    FixedSelectionPlan,
    GroupedSample,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    bound_conditional_outer_risks,
    build_nested_group_folds,
    select_grouped_forecast_candidates,
)


@pytest.mark.parametrize('high_counts', [(10, 10), (1, 19)])
def test_actual_nested_convex_fits_feed_conditional_risk_bounds(high_counts: tuple[int, int]):
    split_plan = NestedGroupPlan(seed=17, outer_folds=2, inner_folds=2, minimum_training_groups=1)
    skeleton = tuple(GroupedSample(f'g{index}', 's0') for index in range(40))
    splits = build_nested_group_folds(skeleton, plan=split_plan)
    high = {
        source
        for fold, count in zip(splits.folds, high_counts, strict=True)
        for source, _ in fold.test_groups[:count]
    }
    samples = tuple(
        GroupedSample(sample.source_id, f's{index}')
        for sample in skeleton
        for index in range(3 if sample.source_id in high else 1)
    )
    records = tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id='mathematical',
            protocol_id='constants',
            target=TargetSpec(
                'volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume'
            ),
            comparisons=tuple(
                RetentionComparison(
                    sample.source_id,
                    sample.sample_id,
                    pressure,
                    float(sample.source_id in high),
                    predicted,
                )
                for sample in samples
                for pressure in (1, 100)
            ),
        )
        for identifier, predicted in (('one', 1.0), ('zero', 0.0))
    )
    loss_plan = LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100)
    plan = LearnedSelectionPlan(
        fixed=FixedSelectionPlan(candidate_ids=('one', 'zero'), folds=split_plan, loss=loss_plan),
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
    selected = select_grouped_forecast_candidates(
        records, samples=samples, candidate_kinds={'one': 'atomic', 'zero': 'atomic'}, plan=plan
    )
    groups = {group.group_id: group.samples for group in selected.splits.groups}
    evidence = []
    known_risks = []
    for fold, split, training_high_count in zip(
        selected.folds,
        selected.splits.folds,
        reversed(high_counts),
        strict=True,
    ):
        expected_weight = Fraction(3 * training_high_count, 20 + 2 * training_high_count)
        assert isinstance(fold.ensemble.outer_fit, ConvexPairFit)
        assert fold.ensemble.outer_fit.left_weight == pytest.approx(float(expected_weight))
        assert fold.ensemble.assessment is not None
        sample_losses = {
            (sample.source_id, sample.sample_id): sample.loss
            for sample in fold.ensemble.assessment.samples
        }
        assert all(value is not None for value in sample_losses.values())
        evidence.append(
            ConditionalOuterFoldLoss(
                fold.fold_id,
                split.training_groups,
                tuple(
                    BoundedGroupLoss(
                        group, tuple(cast('float', sample_losses[key]) for key in groups[group])
                    )
                    for group in split.test_groups
                ),
            )
        )
        known_risks.append((expected_weight**2 + 3 * (1 - expected_weight) ** 2) / 4)
    result = bound_conditional_outer_risks(
        tuple(evidence),
        plan=ConditionalOuterRiskPlan(
            population_id='mathematical_iid_groups',
            grouping='source',
            loss=loss_plan,
            maximum_sample_loss=1,
            maximum_group_size=3,
        ),
    )
    assert result.group_count == 40
    assert result.sample_count == 40 + 2 * sum(high_counts)
    interval = result.equal_fold_mean_risk_interval
    assert interval.lower <= float(sum(known_risks) / 2) <= interval.upper
    assert interval.upper - interval.lower < 1
