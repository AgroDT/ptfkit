import math
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Literal

import pytest
from _resampling_fixtures import resampling_result
from _selection_diagnostic_fixtures import FIXED, diagnostic_result

from ptfkit_eval import (
    ConditionalOuterRiskPlan,
    EvaluationDocumentError,
    SelectionRiskPlan,
    assess_selection_conditional_risks,
    evaluate_log_pressure_loss,
)


def policy(
    *,
    protocol: Literal['fixed', 'learned'] = 'learned',
    strategy: Literal['atomic', 'ensemble'] = 'atomic',
):
    return SelectionRiskPlan(
        protocol=protocol,
        strategy=strategy,
        bounds=ConditionalOuterRiskPlan(
            population_id='controlled_test_population',
            grouping='source',
            loss=FIXED.loss,
            maximum_sample_loss=1,
            minimum_group_size=1,
            maximum_group_size=1,
        ),
    )


def test_all_registered_strategies_share_family_budget_with_independent_radius_oracle(
    tmp_path: Path,
):
    result = diagnostic_result(tmp_path)
    policies = tuple(
        policy(protocol=protocol, strategy=strategy)
        for protocol in ('fixed', 'learned')
        for strategy in ('atomic', 'ensemble')
    )
    assessed = assess_selection_conditional_risks(result, policies=policies)
    assert len(assessed) == 4
    # Four policies, three numerator events plus a denominator per policy,
    # two-sided tails and alpha=.05 give ln(640); two test groups per fold.
    radius = float((Decimal(640).ln() / 4).sqrt())
    for item in assessed:
        assert item.status == 'computed'
        assert item.family_size == 4
        assert item.allocated_error_probability == pytest.approx(0.0125)
        assert item.bound is not None
        assert item.bound.group_count == item.bound.sample_count == 6
        assert all(
            fold.normalized_numerator_radius == pytest.approx(radius) for fold in item.bound.folds
        )
        assert item.bound.plan.simultaneous_policy_count == 4


def test_partial_target_coverage_keeps_original_population_and_produces_no_band(tmp_path: Path):
    result = diagnostic_result(tmp_path, missing_target=True)
    assert result.learned_selection is not None
    assert result.learned_selection.status == 'computed'
    assessed = assess_selection_conditional_risks(result, policies=(policy(),))
    assert assessed[0].bound is None
    assert assessed[0].reason == 'incomplete_outer_strategy'
    assert any(
        item.reason == 'incomplete_outer_sample_losses' for item in assessed[0].fold_failures
    )


def test_failed_ensemble_never_reallocates_its_family_budget(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    assert result.learned_selection is not None
    first = result.learned_selection.folds[0]
    failed = replace(
        first.ensemble, candidate_id=None, assessment=None, reason='unidentifiable_boundary'
    )
    modified = replace(
        result,
        learned_selection=replace(
            result.learned_selection,
            folds=(replace(first, ensemble=failed), *result.learned_selection.folds[1:]),
        ),
    )
    assessed = assess_selection_conditional_risks(
        modified, policies=(policy(), policy(strategy='ensemble'))
    )
    assert assessed[0].status == 'computed'
    assert assessed[1].reason == 'incomplete_outer_strategy'
    assert assessed[1].fold_failures[0].reason == 'unidentifiable_boundary'
    assert all(item.family_size == 2 for item in assessed)
    assert all(item.allocated_error_probability == pytest.approx(0.025) for item in assessed)


@pytest.mark.parametrize('change', ['loss', 'grouping', 'stored_loss', 'stored_mean'])
def test_incompatible_or_corrupt_retained_evidence_is_rejected(tmp_path: Path, change: str):
    result = diagnostic_result(tmp_path)
    selected = policy()
    assert result.learned_selection is not None
    first = result.learned_selection.folds[0]
    assessment = first.atomic.assessment
    assert assessment is not None
    if change == 'loss':
        selected = replace(
            selected,
            bounds=replace(selected.bounds, loss=replace(FIXED.loss, upper_suction_kpa=10)),
        )
    elif change == 'grouping':
        selected = replace(selected, bounds=replace(selected.bounds, grouping='profile'))
    else:
        assessment = (
            replace(assessment, mean_loss=0.123)
            if change == 'stored_mean'
            else replace(
                assessment,
                samples=(replace(assessment.samples[0], loss=0.123), *assessment.samples[1:]),
            )
        )
        result = replace(
            result,
            learned_selection=replace(
                result.learned_selection,
                folds=(
                    replace(first, atomic=replace(first.atomic, assessment=assessment)),
                    *result.learned_selection.folds[1:],
                ),
            ),
        )
    with pytest.raises(EvaluationDocumentError):
        assess_selection_conditional_risks(result, policies=(selected,))


def test_observed_population_bound_violation_is_a_retained_failure(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    selected = policy()
    selected = replace(selected, bounds=replace(selected.bounds, maximum_sample_loss=1e-9))
    assessed = assess_selection_conditional_risks(result, policies=(selected,))[0]
    assert assessed.bound is None
    assert assessed.reason == 'incomplete_outer_strategy'
    assert {failure.reason for failure in assessed.fold_failures} == {
        'observed_sample_loss_bound_violation'
    }


@pytest.mark.parametrize(
    ('grouping', 'effective', 'fallback'),
    [('source', 'source', False), ('profile', 'profile', False), ('profile', 'source', True)],
)
def test_unequal_source_local_groups_keep_full_sample_counts(
    *,
    tmp_path: Path,
    grouping: Literal['source', 'profile'],
    effective: Literal['source', 'profile'],
    fallback: bool,
):
    result = resampling_result(tmp_path, grouping=grouping, source_fallback=fallback)
    selected = policy()
    selected = replace(
        selected, bounds=replace(selected.bounds, grouping=effective, maximum_group_size=2)
    )
    assessed = assess_selection_conditional_risks(result, policies=(selected,))[0]
    assert assessed.bound is not None
    assert assessed.bound.group_count == 8
    assert assessed.bound.sample_count == 9
    violated = replace(selected, bounds=replace(selected.bounds, maximum_group_size=1))
    rejected = assess_selection_conditional_risks(result, policies=(violated,))[0]
    assert rejected.bound is None
    assert rejected.reason == 'observed_group_size_bound_violation'


def test_near_one_family_confidence_does_not_round_allocated_plan_to_one(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    policies = tuple(
        replace(
            policy(strategy=strategy),
            bounds=replace(policy().bounds, confidence_level=math.nextafter(1, 0)),
        )
        for strategy in ('atomic', 'ensemble')
    )
    assessed = assess_selection_conditional_risks(result, policies=policies)
    assert all(item.bound is not None for item in assessed)
    assert all(item.allocated_error_probability > 0 for item in assessed)


def test_consistently_rewritten_targets_cannot_replace_original_eligible_observations(
    tmp_path: Path,
):
    result = diagnostic_result(tmp_path)
    assert result.learned_selection is not None
    first = result.learned_selection.folds[0]
    original = first.atomic
    assert original.assessment is not None
    predictions = tuple(
        replace(point, observed=point.observed + 0.125) for point in original.predictions
    )
    losses = evaluate_log_pressure_loss(predictions, plan=FIXED.loss)
    valid = [sample.loss for sample in losses if sample.loss is not None]
    assert len(valid) == original.assessment.total_sample_count
    changed = replace(
        original,
        predictions=predictions,
        assessment=replace(
            original.assessment,
            samples=losses,
            mean_loss=sum(valid) / len(valid),
        ),
    )
    rewritten = replace(
        result,
        learned_selection=replace(
            result.learned_selection,
            folds=(replace(first, atomic=changed), *result.learned_selection.folds[1:]),
        ),
    )
    with pytest.raises(EvaluationDocumentError, match='common observation grid'):
        assess_selection_conditional_risks(rewritten, policies=(policy(),))


def test_interior_pressure_omission_is_rejected_even_when_losses_are_consistently_recomputed(
    tmp_path: Path,
):
    result = diagnostic_result(tmp_path)
    assert result.learned_selection is not None
    first = result.learned_selection.folds[0]
    original = first.atomic
    assert original.assessment is not None
    assert any(point.suction_kpa == 10 for point in original.predictions)
    predictions = tuple(point for point in original.predictions if point.suction_kpa != 10)
    losses = evaluate_log_pressure_loss(predictions, plan=FIXED.loss)
    valid = [sample.loss for sample in losses if sample.loss is not None]
    assert len(valid) == original.assessment.total_sample_count
    changed = replace(
        original,
        predictions=predictions,
        assessment=replace(
            original.assessment,
            samples=losses,
            mean_loss=sum(valid) / len(valid),
        ),
    )
    rewritten = replace(
        result,
        learned_selection=replace(
            result.learned_selection,
            folds=(replace(first, atomic=changed), *result.learned_selection.folds[1:]),
        ),
    )
    with pytest.raises(EvaluationDocumentError, match='complete retained common pressure grid'):
        assess_selection_conditional_risks(rewritten, policies=(policy(),))


def test_retained_outside_domain_pressure_diagnostics_do_not_change_the_risk_estimand(
    tmp_path: Path,
):
    result = diagnostic_result(tmp_path, outside_pressure=True)
    assert result.learned_selection is not None
    assert {fold.atomic.candidate_id for fold in result.learned_selection.folds} == {'sand_a'}
    assessed = assess_selection_conditional_risks(result, policies=(policy(),))[0]
    assert assessed.bound is not None
    assert assessed.bound.sample_count == 6
    assert all(
        fold.normalized_mean_group_loss_sum == pytest.approx(1 / 64)
        for fold in assessed.bound.folds
    )


def test_coordinated_inner_training_role_and_fit_provenance_tampering_is_rejected(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    selection = result.learned_selection
    assert selection is not None
    outer = selection.splits.folds[0]
    inner = outer.inner[0]
    leaked_training = (outer.test_groups[0], *inner.training_groups[1:])
    changed_inner = replace(inner, training_groups=leaked_training)
    changed_outer = replace(outer, inner=(changed_inner, *outer.inner[1:]))
    fold = selection.folds[0]
    scores = tuple(
        replace(
            score,
            folds=tuple(
                replace(evidence, fit=replace(evidence.fit, training_groups=leaked_training))
                if evidence.fold_id == inner.fold_id and evidence.fit is not None
                else evidence
                for evidence in score.folds
            ),
        )
        for score in fold.ensemble.inner_scores
    )
    changed_fold = replace(fold, ensemble=replace(fold.ensemble, inner_scores=scores))
    rewritten = replace(
        result,
        learned_selection=replace(
            selection,
            splits=replace(selection.splits, folds=(changed_outer, *selection.splits.folds[1:])),
            folds=(changed_fold, *selection.folds[1:]),
        ),
    )
    with pytest.raises(EvaluationDocumentError, match='original identity-only split'):
        assess_selection_conditional_risks(rewritten, policies=(policy(),))
