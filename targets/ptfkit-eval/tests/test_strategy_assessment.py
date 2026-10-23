from dataclasses import replace
from pathlib import Path

import pytest
from _selection_diagnostic_fixtures import FIXED, LEARNED, diagnostic_result

from ptfkit_eval import (
    EvaluationDocumentError,
    assess_selection_strategies,
    select_fixed_retention_candidates,
    select_learned_retention_candidates,
)


def test_only_locked_outer_predictions_enter_hand_calculated_strategy_metrics(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    assessments = assess_selection_strategies(result)
    assert [item.protocol for item in assessments] == ['fixed', 'learned']
    for assessment in assessments:
        assert assessment.status == 'computed'
        assert assessment.uncertainty_status == 'not_estimated_crossfit_dependency'
        maximal = {cohort.candidate_id: cohort.summary for cohort in assessment.cohorts.maximal}
        common = {cohort.candidate_id: cohort.summary for cohort in assessment.cohorts.common}
        for strategy in assessment.strategies:
            error = (
                0.25
                if assessment.protocol == 'fixed' and strategy.strategy == 'ensemble'
                else 0.125
            )
            assert strategy.status == 'computed'
            assert strategy.total_sample_count == strategy.eligible_loss_sample_count == 6
            assert strategy.failed_fold_count == 0
            assert len(strategy.folds) == 3
            assert all(frame.inner_fold_id is None for frame in strategy.folds)
            assert len(strategy.comparisons) == 18
            assert strategy.mean_outer_loss == pytest.approx(error**2)
            assert strategy.excluded_pressure_point_count == 0
            summary = common[strategy.strategy]
            assert summary is not None
            assert (summary.sample_count, summary.point_count) == (6, 18)
            assert summary == maximal[strategy.strategy]
            assert summary.metrics.mean_error == pytest.approx(error)
            assert summary.metrics.mean_absolute_error == pytest.approx(error)
            assert summary.metrics.root_mean_squared_error == pytest.approx(error)
            assert summary.metrics.median_absolute_error == pytest.approx(error)
        differences = assessment.atomic_minus_ensemble
        assert differences is not None
        expected = -0.125 if assessment.protocol == 'fixed' else 0
        assert differences.root_mean_squared_error == pytest.approx(expected)
        assert differences.mean_absolute_error == pytest.approx(expected)


def test_points_outside_selection_loss_domain_are_audited_and_excluded_from_metrics(tmp_path: Path):
    result = diagnostic_result(tmp_path, outside_pressure=True)
    assessments = assess_selection_strategies(result)
    for assessment in assessments:
        for strategy in assessment.strategies:
            assert strategy.excluded_pressure_point_count == 6
            assert len(strategy.comparisons) == 18
            assert max(point.suction_kpa for point in strategy.comparisons) == 100
            expected = (
                1 / 16
                if assessment.protocol == 'fixed' and strategy.strategy == 'ensemble'
                else 1 / 64
            )
            assert strategy.mean_outer_loss == pytest.approx(expected)
        for cohort in assessment.cohorts.maximal:
            assert cohort.summary is not None
            expected_rmse = (
                0.25
                if assessment.protocol == 'fixed' and cohort.candidate_id == 'ensemble'
                else 0.125
            )
            assert cohort.summary.metrics.root_mean_squared_error == pytest.approx(expected_rmse)


def test_missing_targets_stay_in_strategy_denominators(tmp_path: Path):
    result = diagnostic_result(tmp_path, missing_target=True)
    for assessment in assess_selection_strategies(result):
        for strategy in assessment.strategies:
            assert strategy.status == 'computed'  # Registered per-fold coverage is 1/2.
            assert strategy.total_sample_count == 6
            assert strategy.eligible_loss_sample_count == 5
            missing = next(
                sample for sample in strategy.loss_samples if sample.source_id == 'source_5'
            )
            assert missing.loss is None
            assert missing.reason == 'insufficient_points'
        assert all(
            cohort.summary and cohort.summary.sample_count == 5
            for cohort in assessment.cohorts.common
        )


def test_incomplete_outer_folds_retain_partial_descriptive_rows_without_complete_loss(
    tmp_path: Path,
):
    result = diagnostic_result(tmp_path)
    assert result.selection is not None
    held_out = {source for source, _ in result.selection.splits.folds[0].test_groups}
    points = tuple(
        point
        for point in result.points
        if not (point.source_id in held_out and point.suction_kpa == 100)
    )
    changed = replace(result, points=points)
    changed = replace(
        changed,
        selection=select_fixed_retention_candidates(changed, plan=FIXED),
        learned_selection=select_learned_retention_candidates(changed, plan=LEARNED),
    )
    for assessment in assess_selection_strategies(changed):
        assert assessment.status == 'insufficient_evidence'
        assert assessment.reason == 'incomplete_outer_strategy_evidence'
        for strategy in assessment.strategies:
            assert strategy.mean_outer_loss is None
            assert strategy.failed_fold_count >= 1
            assert strategy.total_sample_count == 6
        # Fold 0 still has two pressure points per held-out sample, even though
        # exact-endpoint curve loss is unsupported. These are partial diagnostics.
        for cohort in assessment.cohorts.maximal:
            assert cohort.summary is not None
            assert cohort.summary.point_count >= 4


def test_split_failure_is_explicit_and_does_not_invent_outer_assignments(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    fixed = replace(FIXED, folds=replace(FIXED.folds, minimum_training_groups=99))
    learned = replace(LEARNED, fixed=replace(LEARNED.fixed, folds=fixed.folds))
    result = replace(
        result,
        selection=select_fixed_retention_candidates(result, plan=fixed),
        learned_selection=select_learned_retention_candidates(result, plan=learned),
    )
    for assessment in assess_selection_strategies(result):
        assert assessment.status == 'insufficient_evidence'
        assert assessment.reason == 'insufficient_groups_for_requested_folds'
        assert assessment.atomic_minus_ensemble is None
        assert all(
            strategy.total_sample_count == 6 and strategy.folds == ()
            for strategy in assessment.strategies
        )
        assert all(cohort.summary is None for cohort in assessment.cohorts.common)


def test_stored_outer_losses_must_match_the_actual_retained_prediction_rows(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    selection = result.learned_selection
    assert selection is not None
    fold = selection.folds[0]
    assert fold.ensemble.assessment is not None
    assessment = fold.ensemble.assessment
    bad_losses = (replace(assessment.samples[0], loss=0), *assessment.samples[1:])
    changed = replace(
        fold, ensemble=replace(fold.ensemble, assessment=replace(assessment, samples=bad_losses))
    )
    result = replace(
        result, learned_selection=replace(selection, folds=(changed, *selection.folds[1:]))
    )
    with pytest.raises(EvaluationDocumentError, match='reproduce stored per-sample'):
        assess_selection_strategies(result)


def test_duplicate_outer_fold_evidence_cannot_duplicate_samples(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    assert result.selection is not None
    selected = result.selection
    result = replace(
        result, selection=replace(selected, folds=(selected.folds[0], *selected.folds))
    )
    with pytest.raises(EvaluationDocumentError, match='Duplicate selection holdout'):
        assess_selection_strategies(result)


def test_outer_fold_order_does_not_change_strategy_assessment(tmp_path: Path):
    result = diagnostic_result(tmp_path)
    assert result.selection is not None
    assert result.learned_selection is not None
    changed = replace(
        result,
        selection=replace(result.selection, folds=result.selection.folds[::-1]),
        learned_selection=replace(
            result.learned_selection, folds=result.learned_selection.folds[::-1]
        ),
    )
    assert assess_selection_strategies(changed) == assess_selection_strategies(result)
