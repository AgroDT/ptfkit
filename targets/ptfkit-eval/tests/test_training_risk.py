from dataclasses import replace
from decimal import Decimal, localcontext

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    GroupMembership,
    IndependentTrainingBlock,
    IndependentTrainingRiskPlan,
    LogPressureLossPlan,
    TrainingRiskTestGroup,
    bound_independent_training_risk,
)


def plan(count: int = 1000, *, total: bool = False):
    return IndependentTrainingRiskPlan(
        population_id='mathematical_independent_blocks',
        learner_id='controlled_training_algorithm_v1',
        grouping='source',
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
        maximum_sample_loss=1,
        minimum_group_size=1,
        maximum_group_size=3,
        training_groups_per_block=1,
        test_groups_per_block=2,
        n_blocks=count,
        total_learner=total,
    )


def group(source: str, size: int):
    return GroupMembership((source, ''), tuple((source, f's{index}') for index in range(size)))


def blocks(count: int = 1000, *, failures: bool = True):
    output = []
    for index in range(count):
        high = index % 2 == 0
        failed = failures and index % 4 == 0
        size = 3 if high else 1
        output.append(
            IndependentTrainingBlock(
                f'b{index}',
                (group(f'b{index}_train', 1),),
                tuple(
                    TrainingRiskTestGroup(
                        group(f'b{index}_test{test}', size),
                        None if failed else (float(high),) * size,
                    )
                    for test in range(2)
                ),
                'unidentifiable_boundary' if failed else None,
            )
        )
    return tuple(output)


def test_all_blocks_including_failed_training_enter_mass_normalization_and_probability():
    result = bound_independent_training_risk(blocks(), plan=plan())
    assert result.status == 'computed'
    assert result.training_failure_count == 250
    assert result.test_sample_count == 4000
    assert result.moments is not None
    assert result.moments.normalized_mean_successful_loss_sum == pytest.approx(1 / 4)
    assert result.moments.normalized_mean_test_group_size == pytest.approx(2 / 3)
    assert result.moments.mean_training_success == 3 / 4
    assert result.unconditional_model_risk_interval is None
    with localcontext() as context:
        context.prec = 60
        radius = (Decimal(120).ln() / 2000).sqrt()
        size_radius = Decimal(2) / 3 * (Decimal(120).ln() / 4000).sqrt()
        lower = (Decimal(1) / 4 - radius) / (Decimal(2) / 3 + size_radius)
        upper = (Decimal(1) / 4 + radius) / (Decimal(2) / 3 - size_radius)
        assert result.moments.normalized_successful_loss_radius == pytest.approx(float(radius))
        assert result.moments.normalized_group_size_radius == pytest.approx(float(size_radius))
        assert result.risk_mass_on_success_interval is not None
        assert result.risk_mass_on_success_interval.lower == pytest.approx(float(lower))
        assert result.risk_mass_on_success_interval.upper == pytest.approx(float(upper))
        assert result.successful_training_mean_risk_interval is not None
        assert result.successful_training_mean_risk_interval.lower == pytest.approx(
            float(lower / (Decimal(3) / 4 + radius))
        )
        assert result.successful_training_mean_risk_interval.upper == pytest.approx(
            float(upper / (Decimal(3) / 4 - radius))
        )


def test_total_learner_assertion_enables_training_average_sample_risk_with_informative_sizes():
    evidence = blocks(failures=False)
    result = bound_independent_training_risk(evidence, plan=plan(total=True))
    interval = result.unconditional_model_risk_interval
    assert interval is not None
    # Always predicting zero under equiprobable (N=1,target=0)/(N=3,target=1)
    # groups has training-average sample risk 3/4, not group-average risk 1/2.
    assert 0.5 < interval.lower < 0.75 < interval.upper < 1
    assert result.training_success_probability_interval is not None
    assert result.training_success_probability_interval.lower == 1
    assert result.training_success_probability_interval.upper == 1
    observed_success_only = bound_independent_training_risk(evidence, plan=plan())
    assert observed_success_only.unconditional_model_risk_interval is None


def test_all_failed_training_keeps_unknown_rare_success_risk_instead_of_zero_error():
    evidence = tuple(
        replace(
            block,
            training_failure_reason='training_failed',
            test_groups=tuple(replace(test, sample_losses=None) for test in block.test_groups),
        )
        for block in blocks(20)
    )
    result = bound_independent_training_risk(evidence, plan=plan(20))
    assert result.status == 'computed'
    assert result.training_failure_count == 20
    assert result.risk_mass_on_success_interval is not None
    assert result.risk_mass_on_success_interval.lower == 0
    assert result.risk_mass_on_success_interval.upper > 0
    assert result.successful_training_mean_risk_interval is None
    assert result.successful_training_risk_reason == 'success_probability_not_separated_from_zero'
    assert result.unconditional_model_risk_interval is None


def test_finite_large_loss_bound_does_not_overflow_raw_block_sums():
    evidence = tuple(
        IndependentTrainingBlock(
            f'b{index}',
            (group(f'b{index}_train', 3),),
            tuple(
                TrainingRiskTestGroup(group(f'b{index}_test{test}', 3), (1e308,) * 3)
                for test in range(2)
            ),
        )
        for index in range(2)
    )
    registered = replace(plan(2, total=True), maximum_sample_loss=1e308, minimum_group_size=3)
    result = bound_independent_training_risk(evidence, plan=registered)
    assert result.status == 'computed'
    assert result.unconditional_model_risk_interval is not None
    assert result.unconditional_model_risk_interval.lower == 0
    assert result.unconditional_model_risk_interval.upper == 1e308


@pytest.mark.parametrize('defect', ['partial_test', 'loss_bound', 'size_bound', 'totality'])
def test_unavailable_or_contradictory_evidence_cannot_change_the_registered_population(defect: str):
    evidence = blocks(4)
    registered = plan(4)
    changed = evidence[1]
    if defect == 'totality':
        registered = replace(registered, total_learner=True)
    elif defect == 'partial_test':
        changed = replace(
            changed,
            test_groups=(
                replace(changed.test_groups[0], sample_losses=None),
                *changed.test_groups[1:],
            ),
        )
    elif defect == 'loss_bound':
        changed = replace(
            changed,
            test_groups=(
                replace(changed.test_groups[0], sample_losses=(1.1,)),
                *changed.test_groups[1:],
            ),
        )
    else:
        registered = replace(registered, maximum_group_size=2)
    evidence = (evidence[0], changed, *evidence[2:])
    result = bound_independent_training_risk(evidence, plan=registered)
    expected = {
        'partial_test': 'incomplete_successful_block_test_losses',
        'loss_bound': 'observed_sample_loss_bound_violation',
        'size_bound': 'observed_group_size_bound_violation',
        'totality': 'total_learner_assertion_violated',
    }[defect]
    assert result.reason == expected
    assert result.moments is None
    assert result.risk_mass_on_success_interval is None


@pytest.mark.parametrize(
    'defect', ['dropped_block', 'shared_group', 'role_count', 'failed_zero_loss']
)
def test_dependent_or_selectively_retained_blocks_are_rejected(defect: str):
    evidence = blocks(4)
    if defect == 'dropped_block':
        evidence = evidence[:-1]
    elif defect == 'shared_group':
        evidence = (
            evidence[0],
            replace(evidence[1], training_groups=evidence[0].training_groups),
            *evidence[2:],
        )
    elif defect == 'role_count':
        evidence = (replace(evidence[0], training_groups=()), *evidence[1:])
    else:
        original = evidence[0]
        evidence = (
            replace(
                original,
                test_groups=tuple(
                    replace(test, sample_losses=(0.0,) * len(test.group.samples))
                    for test in original.test_groups
                ),
            ),
            *evidence[1:],
        )
    with pytest.raises(EvaluationDocumentError):
        bound_independent_training_risk(evidence, plan=plan(4))
