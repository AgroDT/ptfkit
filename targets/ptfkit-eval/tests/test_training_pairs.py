import math
from dataclasses import replace
from decimal import Decimal

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    GroupMembership,
    IndependentTrainingBlock,
    IndependentTrainingRiskPlan,
    LogPressureLossPlan,
    PairedTrainingRiskPlan,
    TrainingRiskTestGroup,
    bound_paired_independent_training_risk,
)


def plan(*, total: bool = False, scale: float = 1):
    return PairedTrainingRiskPlan(
        left_learner_id='atomic',
        right_learner_id='ensemble',
        bounds=IndependentTrainingRiskPlan(
            population_id='controlled_paired_blocks',
            learner_id='joint_training_procedure',
            grouping='source',
            loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
            maximum_sample_loss=scale,
            minimum_group_size=2,
            maximum_group_size=2,
            training_groups_per_block=1,
            test_groups_per_block=1,
            n_blocks=1000,
            total_learner=total,
        ),
    )


def group(source: str):
    return GroupMembership((source, ''), ((source, 's0'), (source, 's1')))


def records(*, right_failures: bool = False, scale: float = 1):
    left, right = [], []
    for i in range(1000):
        training, test = group(f'b{i}_training'), group(f'b{i}_test')
        failed = right_failures and i % 2 == 0
        left.append(
            IndependentTrainingBlock(
                f'b{i}',
                (training,),
                (TrainingRiskTestGroup(test, ((1 if failed else 0.75) * scale,) * 2),),
            )
        )
        right.append(
            IndependentTrainingBlock(
                f'b{i}',
                (training,),
                (TrainingRiskTestGroup(test, None if failed else (0.25 * scale,) * 2),),
                'unidentifiable_boundary' if failed else None,
            )
        )
    return tuple(left), tuple(right)


def test_total_joint_learner_has_signed_paired_difference_with_independent_radius_oracle():
    left, right = records()
    result = bound_paired_independent_training_risk(left, right, plan=plan(total=True))
    assert result.status == 'computed'
    interval = result.unconditional_mean_risk_difference_interval
    assert interval is not None
    radius = float((Decimal(120).ln() / 2000).sqrt())
    assert interval.lower == pytest.approx(0.5 - 2 * radius)
    assert interval.upper == pytest.approx(0.5 + 2 * radius)
    assert result.joint_success_mean_risk_difference_interval == interval
    reverse = bound_paired_independent_training_risk(
        right,
        left,
        plan=replace(plan(total=True), left_learner_id='ensemble', right_learner_id='atomic'),
    )
    opposite = reverse.unconditional_mean_risk_difference_interval
    assert opposite is not None
    assert opposite.lower == pytest.approx(-interval.upper)
    assert opposite.upper == pytest.approx(-interval.lower)


def test_unknown_totality_retains_probability_uncertainty_despite_observed_success():
    left, right = records()
    result = bound_paired_independent_training_risk(left, right, plan=plan())
    assert result.unconditional_mean_risk_difference_interval is None
    interval = result.joint_success_mean_risk_difference_interval
    assert interval is not None
    radius = float((Decimal(120).ln() / 2000).sqrt())
    assert interval.lower == pytest.approx(0.5 - 2 * radius)
    assert interval.upper == pytest.approx(2 * (0.75 + radius) / (1 - radius) - 1)
    mass = result.risk_difference_mass_on_joint_success_interval
    assert mass is not None
    assert mass.lower == pytest.approx(0.5 - 2 * radius)
    assert mass.upper == pytest.approx(0.5 + 3 * radius)


def test_equal_binary_differences_at_different_absolute_losses_have_identical_transformed_law():
    left, right = records()

    def losses(
        blocks: tuple[IndependentTrainingBlock, ...], value: float
    ) -> tuple[IndependentTrainingBlock, ...]:
        return tuple(
            replace(b, test_groups=(replace(b.test_groups[0], sample_losses=(value, value)),))
            for b in blocks
        )

    low = bound_paired_independent_training_risk(
        losses(left, 1 / 16),
        losses(right, 0),
        plan=plan(scale=3 / 16),
    )
    high = bound_paired_independent_training_risk(
        losses(left, 3 / 16),
        losses(right, 1 / 8),
        plan=plan(scale=3 / 16),
    )
    assert low == high


def test_pair_conditions_on_joint_success_instead_of_subtracting_marginal_success_risks():
    left, right = records(right_failures=True)
    result = bound_paired_independent_training_risk(left, right, plan=plan())
    transformed = result.transformed_bound
    assert transformed is not None
    assert transformed.training_failure_count == 500
    assert transformed.test_sample_count == 2000
    assert transformed.moments is not None
    assert transformed.moments.mean_training_success == 0.5
    # Jointly successful cases have losses .75/.25 and transformed loss .75.
    # Left-only successful cases have loss 1 and cannot enter that comparison.
    assert transformed.moments.normalized_mean_successful_loss_sum == 0.375
    mass = result.risk_difference_mass_on_joint_success_interval
    assert mass is not None
    radius = float((Decimal(120).ln() / 2000).sqrt())
    assert mass.lower == pytest.approx(0.25 - 3 * radius)
    assert mass.upper == pytest.approx(0.25 + 3 * radius)
    assert result.unconditional_mean_risk_difference_interval is None
    # Unavailable test losses for the left model do not change a pair already
    # undefined by right training failure. No failed block is dropped.
    missing = tuple(
        replace(block, test_groups=(replace(block.test_groups[0], sample_losses=None),))
        if i % 2 == 0
        else block
        for i, block in enumerate(left)
    )
    assert bound_paired_independent_training_risk(missing, right, plan=plan()) == result


def test_missing_jointly_successful_test_losses_suppress_all_intervals():
    left, right = records()
    left = (
        replace(left[0], test_groups=(replace(left[0].test_groups[0], sample_losses=None),)),
        *left[1:],
    )
    result = bound_paired_independent_training_risk(left, right, plan=plan())
    assert result.reason == 'incomplete_successful_block_test_losses'
    assert result.joint_success_mean_risk_difference_interval is None
    assert result.risk_difference_mass_on_joint_success_interval is None


def test_individual_bound_violations_cannot_cancel_inside_a_zero_difference():
    left, _ = records(scale=2)
    result = bound_paired_independent_training_risk(left, left, plan=plan())
    assert result.reason == 'observed_sample_loss_bound_violation'
    assert result.transformed_bound is None


def test_paired_roles_must_be_identical_not_merely_equal_size():
    left, right = records()
    right = (replace(right[0], training_groups=(group('other_original'),)), *right[1:])
    with pytest.raises(EvaluationDocumentError, match='identical original training/test roles'):
        bound_paired_independent_training_risk(left, right, plan=plan())


def test_contradicted_joint_totality_and_extreme_finite_signed_loss_are_explicit():
    left, right = records(right_failures=True)
    result = bound_paired_independent_training_risk(left, right, plan=plan(total=True))
    assert result.reason == 'total_learner_assertion_violated'
    assert result.unconditional_mean_risk_difference_interval is None
    left, right = records(scale=1e308)
    result = bound_paired_independent_training_risk(left, right, plan=plan(total=True, scale=1e308))
    interval = result.unconditional_mean_risk_difference_interval
    assert interval is not None
    assert math.isfinite(interval.lower)
    assert math.isfinite(interval.upper)
    assert 0 < interval.lower < 5e307 < interval.upper < 1e308
