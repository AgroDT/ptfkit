import math
from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from ptfkit_eval import (
    BoundedGroupLoss,
    ConditionalOuterFoldLoss,
    ConditionalOuterRiskPlan,
    EvaluationDocumentError,
    LogPressureLossPlan,
    bound_conditional_outer_risks,
)


PLAN = ConditionalOuterRiskPlan(
    population_id='mathematical_iid_groups',
    grouping='source',
    loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    maximum_sample_loss=1,
    maximum_group_size=3,
)


def two_folds(groups: tuple[BoundedGroupLoss, ...]):
    half = len(groups) // 2
    return (
        ConditionalOuterFoldLoss(
            0, tuple(group.group_id for group in groups[half:]), groups[:half]
        ),
        ConditionalOuterFoldLoss(
            1, tuple(group.group_id for group in groups[:half]), groups[half:]
        ),
    )


def test_equal_size_bound_uses_groups_and_simultaneous_family_budget():
    groups = tuple(
        BoundedGroupLoss((f'g{index}', ''), (0.1 if index < 1000 else 0.4,) * 3)
        for index in range(2000)
    )
    result = bound_conditional_outer_risks(
        two_folds(groups), plan=replace(PLAN, minimum_group_size=3)
    )
    # Two numerator events plus one denominator event: the two-sided tail
    # budget gives ln(2 * 3 / .05). Exact population size removes denominator noise.
    with localcontext() as context:
        context.prec = 60
        radius = float((Decimal(120).ln() / Decimal(2000)).sqrt())
    assert result.group_count == 2000
    assert result.sample_count == 6000
    assert result.normalized_denominator_radius == 0
    for fold, mean in zip(result.folds, (0.1, 0.4), strict=True):
        assert fold.group_count == 1000
        assert fold.sample_count == 3000
        assert fold.normalized_numerator_radius == pytest.approx(radius)
        assert fold.risk_interval.lower == pytest.approx(mean - radius)
        assert fold.risk_interval.upper == pytest.approx(mean + radius)
    assert result.equal_fold_mean_risk_interval.lower == pytest.approx(0.25 - radius)
    assert result.equal_fold_mean_risk_interval.upper == pytest.approx(0.25 + radius)
    assert result.target == 'equal_fold_mean_conditional_sample_risk'


def test_informative_group_size_bounds_ratio_target_instead_of_group_mean():
    groups = tuple(
        BoundedGroupLoss((f'g{index}', ''), (1.0,) * 3 if index % 2 else (0.0,))
        for index in range(2000)
    )
    result = bound_conditional_outer_risks(two_folds(groups), plan=PLAN)
    # Equiprobable (N=1,S=0) and (N=3,S=3) have risk E[S]/E[N]=3/4,
    # whereas averaging per-group errors would target 1/2.
    interval = result.equal_fold_mean_risk_interval
    assert 0.5 < interval.lower < 0.75 < interval.upper < 1
    assert result.normalized_mean_group_size == pytest.approx(2 / 3)
    assert result.normalized_expected_group_size_interval.lower < 2 / 3
    assert result.normalized_expected_group_size_interval.upper > 2 / 3
    assert result.normalized_denominator_radius > 0


def test_small_group_evidence_retains_a_valid_vacuous_interval():
    groups = (BoundedGroupLoss(('a', ''), (0.0,)), BoundedGroupLoss(('b', ''), (1.0,)))
    result = bound_conditional_outer_risks(two_folds(groups), plan=PLAN)
    assert result.equal_fold_mean_risk_interval.lower == 0
    assert result.equal_fold_mean_risk_interval.upper == PLAN.maximum_sample_loss


def test_large_finite_loss_bounds_do_not_overflow_group_sums():
    groups = (BoundedGroupLoss(('a', ''), (1e308,) * 3), BoundedGroupLoss(('b', ''), (1e308,) * 3))
    result = bound_conditional_outer_risks(
        two_folds(groups), plan=replace(PLAN, maximum_sample_loss=1e308, minimum_group_size=3)
    )
    assert result.equal_fold_mean_risk_interval.lower == 0
    assert result.equal_fold_mean_risk_interval.upper == 1e308
    assert all(math.isfinite(fold.risk_interval.upper) for fold in result.folds)


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('maximum_sample_loss', 0),
        ('maximum_sample_loss', math.inf),
        ('maximum_sample_loss', True),
        ('maximum_group_size', 0),
        ('maximum_group_size', 2**54),
        ('minimum_group_size', 4),
        ('confidence_level', 1),
        ('population_id', ''),
    ],
)
def test_population_assertions_must_be_explicit_and_valid(field: str, value: object):
    with pytest.raises(EvaluationDocumentError, match='population'):
        replace(PLAN, **{field: value})


@pytest.mark.parametrize(
    'defect',
    [
        'duplicate_test_group',
        'training_leak',
        'duplicate_training',
        'empty_fold',
        'duplicate_fold',
        'oversized_group',
        'nonfinite_loss',
        'above_loss_bound',
        'negative_loss',
    ],
)
def test_malformed_or_bound_violating_evidence_is_rejected(defect: str):
    groups = (BoundedGroupLoss(('a', ''), (0.25,)), BoundedGroupLoss(('b', ''), (0.75,)))
    first, second = two_folds(groups)
    if defect == 'duplicate_test_group':
        second = replace(second, test_groups=first.test_groups)
    elif defect == 'training_leak':
        first = replace(first, training_groups=(('a', ''), ('b', '')))
    elif defect == 'duplicate_training':
        first = replace(first, training_groups=(('b', ''), ('b', '')))
    elif defect == 'empty_fold':
        first = replace(first, test_groups=())
    elif defect == 'duplicate_fold':
        second = replace(second, fold_id=first.fold_id)
    else:
        losses = {
            'oversized_group': (0.25,) * 4,
            'nonfinite_loss': (math.nan,),
            'above_loss_bound': (1.01,),
            'negative_loss': (-0.01,),
        }[defect]
        first = replace(first, test_groups=(replace(groups[0], sample_losses=losses),))
    with pytest.raises(EvaluationDocumentError):
        bound_conditional_outer_risks((first, second), plan=PLAN)
