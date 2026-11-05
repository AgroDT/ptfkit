import math
from dataclasses import replace
from decimal import Decimal

import pytest

from ptfkit_eval import (
    ConvexPairPlan,
    FixedSelectionPlan,
    GroupedSample,
    IndependentTrainingRiskPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    PointErrorLossPlan,
    PointSelectionBlock,
    PointSelectionTrainingRisk,
    RetentionCandidateComparisons,
    RetentionComparison,
    TargetSpec,
    allocate_independent_training_blocks,
    assess_independent_forecast_training,
)


@pytest.mark.parametrize('total', [False, True])
def test_complete_point_training_has_hand_derived_equal_grid_losses_and_pooled_rmse_bounds(
    *,
    total: bool,
):
    loss = LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100)
    selector = LearnedSelectionPlan(
        fixed=FixedSelectionPlan(
            candidate_ids=('one', 'zero'),
            loss=loss,
            folds=NestedGroupPlan(seed=17, outer_folds=3, inner_folds=2, minimum_training_groups=1),
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
    bounds = IndependentTrainingRiskPlan(
        population_id='controlled_equal_point_population',
        learner_id='constant_pair',
        grouping='source',
        loss=PointErrorLossPlan(selection_loss=loss, metric='mse'),
        maximum_sample_loss=1,
        minimum_group_size=1,
        maximum_group_size=1,
        training_groups_per_block=2,
        test_groups_per_block=1,
        n_blocks=20,
        total_learner=total,
    )
    samples = tuple(GroupedSample(f'g{i}', 's0') for i in range(60))
    allocation = allocate_independent_training_blocks(samples, plan=bounds, seed=71)
    test = {
        key for block in allocation.blocks for group in block.test_groups for key in group.samples
    }
    forecasts = tuple(
        RetentionCandidateComparisons(
            candidate_id=name,
            dataset_id='controlled',
            protocol_id='irregular_grid',
            target=TargetSpec(
                'volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume'
            ),
            comparisons=tuple(
                RetentionComparison(
                    s.source_id,
                    s.sample_id,
                    pressure,
                    observed if (s.source_id, s.sample_id) in test else 0.5,
                    prediction,
                )
                for s in samples
                for pressure, observed in ((1, 0.5), (2, 0.25), (100, 0))
            ),
        )
        for name, prediction in (('one', 1), ('zero', 0))
    )
    results = []
    for metric, expected in (('mse', 5 / 48), ('mae', 1 / 4)):
        result = assess_independent_forecast_training(
            forecasts,
            samples=samples,
            candidate_kinds={'one': 'atomic', 'zero': 'atomic'},
            selection_plan=selector,
            bounds=replace(bounds, loss=PointErrorLossPlan(selection_loss=loss, metric=metric)),
            strategy='ensemble',
            seed=71,
        )
        assert isinstance(result, PointSelectionTrainingRisk)
        results.append(result)
        assert result.bound.training_failure_count == 0
        assert result.bound.test_sample_count == 20
        for block in result.blocks:
            assert isinstance(block, PointSelectionBlock)
            assert block.point_losses[0].loss == pytest.approx(expected)
            assert block.point_losses[0].point_count == 3
            assert block.evidence.test_groups[0].sample_losses == pytest.approx((expected,))
        moments = result.bound.moments
        assert moments is not None
        assert moments.normalized_mean_successful_loss_sum == pytest.approx(expected)
        radius = float((Decimal(120).ln() / 40).sqrt())
        interval = result.bound.successful_training_mean_risk_interval
        assert interval is not None
        assert interval.lower == 0
        assert interval.upper == pytest.approx(
            min(1, (expected + radius) / (1 if total else 1 - radius))
        )
        if metric == 'mse':
            pooled = result.successful_training_pooled_rmse_interval
            unconditional = result.unconditional_pooled_rmse_interval
            assert pooled is not None
            assert pooled.upper == pytest.approx(math.sqrt(interval.upper))
            if total:
                assert unconditional is not None
                assert unconditional.upper == pytest.approx(math.sqrt(expected + radius))
            else:
                assert unconditional is None
        else:
            assert result.successful_training_pooled_rmse_interval is None
            assert result.unconditional_pooled_rmse_interval is None
    assert [b.selection for b in results[0].blocks] == [b.selection for b in results[1].blocks]
