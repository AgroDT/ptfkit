import json
from dataclasses import replace
from pathlib import Path

import pytest
from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    ConvexPairFit,
    ConvexPairPlan,
    EvaluationDocumentError,
    FixedSelectionPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionRunResult,
    execute_retention_run,
    load_retention_run_plan,
    select_learned_retention_candidates,
)


ENSEMBLE = ConvexPairPlan(
    id='trained_pair',
    left_candidate_id='sand_a',
    right_candidate_id='sand_b',
    minimum_training_groups=2,
    minimum_mean_squared_contrast=1e-12,
)
PLAN = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('sand_a', 'sand_b'),
        folds=NestedGroupPlan(seed=27, outer_folds=3, inner_folds=2),
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    ),
    ensembles=(ENSEMBLE,),
)


def _result(directory: Path, *, observed: float = 0.375) -> RetentionRunResult:
    dataset = json.loads(json.dumps(dataset_document()))
    template = dataset['samples'][0]
    observation = dataset['observations'][0]
    dataset['samples'] = [{**template, 'source_id': f'source_{index}'} for index in range(6)]
    dataset['observations'] = [
        {
            **observation,
            'id': f'{index}_{pressure}',
            'source_id': f'source_{index}',
            'suction_kpa': pressure,
            'value': observed,
        }
        for index in range(6)
        for pressure in (1, 100)
    ]
    result = execute_retention_run(
        load_retention_run_plan(write_run_fixture(directory, dataset=dataset))
    )
    points = []
    for point in result.points:
        assert point.comparison is not None
        value = 0.75 if point.candidate_id == 'sand_a' else 0.25
        points.append(replace(point, comparison=replace(point.comparison, predicted=value)))
    return replace(result, points=tuple(points))


def test_inner_fits_and_outer_refits_recover_independent_quarter_weight(tmp_path: Path):
    selected = select_learned_retention_candidates(_result(tmp_path), plan=PLAN)
    assert selected.status == 'computed'
    assert len(selected.folds) == 3
    for fold in selected.folds:
        outer = selected.splits.folds[fold.fold_id]
        assert fold.atomic.candidate_id == 'sand_b'
        assert fold.ensemble.candidate_id == 'trained_pair'
        refit = fold.ensemble.outer_fit
        assert isinstance(refit, ConvexPairFit)
        assert refit.training_groups == outer.training_groups
        assert refit.training_sample_count == refit.usable_group_count == 4
        assert refit.mean_squared_contrast == pytest.approx(0.25)
        assert refit.left_weight == pytest.approx(0.25)
        assert refit.training_loss == pytest.approx(0)
        for evidence, inner in zip(fold.ensemble.inner_scores[0].folds, outer.inner, strict=True):
            fit = evidence.fit
            assert isinstance(fit, ConvexPairFit)
            assert fit.training_groups == inner.training_groups
            assert fit.left_weight == pytest.approx(0.25)
            assert set(fit.training_groups).isdisjoint(inner.validation_groups)
            assert {point.source_id for point in evidence.predictions} == {
                group[0] for group in inner.validation_groups
            }
        assert fold.ensemble.assessment is not None
        assert fold.ensemble.assessment.mean_loss == pytest.approx(0)
        assert [point.predicted for point in fold.ensemble.predictions] == pytest.approx(
            [0.375] * 4
        )
    assert selected.protocols[0].mean_outer_loss == pytest.approx(1 / 64)
    assert selected.protocols[1].mean_outer_loss == pytest.approx(0)


def test_outer_targets_cannot_change_inner_fits_choice_or_outer_training_weight(tmp_path: Path):
    result = _result(tmp_path)
    baseline = select_learned_retention_candidates(result, plan=PLAN)
    test_sources = {group[0] for group in baseline.splits.folds[0].test_groups}
    points = tuple(
        replace(point, observed=0.75, comparison=replace(point.comparison, observed=0.75))
        if point.source_id in test_sources and point.comparison is not None
        else point
        for point in result.points
    )
    changed = select_learned_retention_candidates(replace(result, points=points), plan=PLAN)
    before, after = baseline.folds[0].ensemble, changed.folds[0].ensemble
    assert after.candidate_id == before.candidate_id == 'trained_pair'
    assert after.inner_scores == before.inner_scores
    assert after.outer_fit == before.outer_fit
    assert isinstance(after.outer_fit, ConvexPairFit)
    assert after.outer_fit.left_weight == pytest.approx(0.25)
    assert after.assessment is not None
    # The untouched test data would prefer weight 1; the locked weight remains 1/4.
    assert after.assessment.mean_loss == pytest.approx(9 / 64)


@pytest.mark.parametrize(('observed', 'expected_weight'), [(0, 0), (1, 1)])
def test_boundary_weights_are_valid_constrained_optima(
    tmp_path: Path, observed: float, expected_weight: float
):
    result = select_learned_retention_candidates(_result(tmp_path, observed=observed), plan=PLAN)
    for fold in result.folds:
        assert isinstance(fold.ensemble.outer_fit, ConvexPairFit)
        assert fold.ensemble.outer_fit.left_weight == expected_weight
        assert fold.ensemble.outer_fit.reason is None


def test_identical_members_do_not_produce_an_arbitrary_default_weight(tmp_path: Path):
    result = _result(tmp_path)
    points = tuple(
        replace(point, comparison=replace(point.comparison, predicted=0.25))
        if point.comparison is not None
        else point
        for point in result.points
    )
    selected = select_learned_retention_candidates(replace(result, points=points), plan=PLAN)
    assert selected.protocols[1].status == 'insufficient_evidence'
    for fold in selected.folds:
        assert fold.ensemble.candidate_id is None
        assert fold.ensemble.assessment is None
        for evidence in fold.ensemble.inner_scores[0].folds:
            assert isinstance(evidence.fit, ConvexPairFit)
            assert evidence.fit.reason == 'unidentifiable_weight'
            assert evidence.fit.left_weight is None
            assert evidence.fit.mean_squared_contrast == 0


def test_weight_fits_are_sample_balanced_over_log_pressure_not_point_weighted(tmp_path: Path):
    result = _result(tmp_path)
    points = []
    for point in result.points:
        assert point.comparison is not None
        # Dense and sparse samples differ in target; the independent optimum is
        # the mean group target mapped onto [1/4, 3/4], regardless of extra points.
        target = 0.5 if int(point.source_id[-1]) % 2 else 0.25
        points.append(
            replace(point, observed=target, comparison=replace(point.comparison, observed=target))
        )
        if target == 0.5 and point.suction_kpa == 1:
            points.append(
                replace(
                    points[-1],
                    observation_id=f'{point.observation_id}_middle',
                    suction_kpa=10,
                    comparison=replace(points[-1].comparison, suction_kpa=10),
                )
            )
    selected = select_learned_retention_candidates(replace(result, points=tuple(points)), plan=PLAN)
    for fold in selected.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, ConvexPairFit)
        odd_count = sum(int(source[-1]) % 2 for source, _ in fit.usable_samples)
        expected_weight = 0.5 * odd_count / len(fit.usable_samples)
        assert fit.left_weight == pytest.approx(expected_weight)


def test_training_group_gate_blocks_fits_without_falling_back(tmp_path: Path):
    policy = replace(PLAN, ensembles=(replace(ENSEMBLE, minimum_training_groups=99),))
    result = select_learned_retention_candidates(_result(tmp_path), plan=policy)
    assert result.protocols[0].status == 'computed'
    assert result.protocols[1].status == 'insufficient_evidence'
    for fold in result.folds:
        assert fold.ensemble.candidate_id is None
        assert all(
            evidence.fit.reason == 'too_few_training_groups'
            for evidence in fold.ensemble.inner_scores[0].folds
            if evidence.fit
        )


def test_outer_refit_recomputes_weight_from_all_outer_training_samples(tmp_path: Path):
    result = _result(tmp_path)
    points = tuple(
        replace(
            point,
            comparison=replace(point.comparison, observed=0.25 + int(point.source_id[-1]) / 16),
        )
        if point.comparison is not None
        else point
        for point in result.points
    )
    selected = select_learned_retention_candidates(replace(result, points=points), plan=PLAN)
    distinct_refit_seen = False
    for fold in selected.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, ConvexPairFit)
        expected = sum(int(source[-1]) / 8 for source, _ in fit.usable_samples) / len(
            fit.usable_samples
        )
        assert fit.left_weight == pytest.approx(expected)
        inner_weights = [
            item.fit.left_weight
            for item in fold.ensemble.inner_scores[0].folds
            if isinstance(item.fit, ConvexPairFit)
        ]
        distinct_refit_seen |= any(weight != pytest.approx(expected) for weight in inner_weights)
    assert distinct_refit_seen


def test_training_objective_uses_log_pressure_trapezoids_with_unequal_intervals(tmp_path: Path):
    result = _result(tmp_path)
    points = []
    for point in result.points:
        assert point.comparison is not None
        pressure = 1000 if point.suction_kpa == 100 else 1
        updated = replace(
            point,
            suction_kpa=pressure,
            observed=0.25,
            comparison=replace(point.comparison, suction_kpa=pressure, observed=0.25),
        )
        points.append(updated)
        if pressure == 1:
            points.append(
                replace(
                    updated,
                    observation_id=f'{point.observation_id}_mid',
                    suction_kpa=10,
                    observed=0.75,
                    comparison=replace(point.comparison, suction_kpa=10, observed=0.75),
                )
            )
    policy = replace(
        PLAN, fixed=replace(PLAN.fixed, loss=replace(PLAN.fixed.loss, upper_suction_kpa=1000))
    )
    selected = select_learned_retention_candidates(
        replace(result, points=tuple(points)), plan=policy
    )
    # The log trapezoids give a mean target of 1/2; an equal-point mean is 5/12.
    for fold in selected.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, ConvexPairFit)
        assert fit.left_weight == pytest.approx(0.5)
        assert fit.training_loss == pytest.approx(1 / 16)
        assert fold.ensemble.assessment is not None
        assert fold.ensemble.assessment.mean_loss == pytest.approx(1 / 16)


def test_missing_training_targets_retain_coverage_failure_and_sample_roster(tmp_path: Path):
    result = _result(tmp_path)
    points = tuple(point for point in result.points if point.source_id != 'source_5')
    selected = select_learned_retention_candidates(replace(result, points=points), plan=PLAN)
    failures = [
        evidence.fit
        for fold in selected.folds
        for score in fold.ensemble.inner_scores
        for evidence in score.folds
        if evidence.fit and ('source_5', '') in evidence.fit.training_groups
    ]
    assert failures
    assert all(fit.status == 'insufficient_evidence' for fit in failures)
    assert all(fit.coverage < 1 for fit in failures)
    assert all(fit.training_sample_count > len(fit.usable_samples) for fit in failures)


def test_nonfinite_training_contrast_remains_an_explicit_fit_failure(tmp_path: Path):
    result = _result(tmp_path)
    points = tuple(
        replace(
            point,
            comparison=replace(
                point.comparison, predicted=1e154 if point.candidate_id == 'sand_a' else -1e154
            ),
        )
        if point.comparison is not None
        else point
        for point in result.points
    )
    selected = select_learned_retention_candidates(replace(result, points=points), plan=PLAN)
    assert selected.protocols[0].status == 'computed'
    assert selected.protocols[1].status == 'insufficient_evidence'
    fits = [
        evidence.fit
        for fold in selected.folds
        for score in fold.ensemble.inner_scores
        for evidence in score.folds
        if evidence.fit is not None
    ]
    assert len(fits) == 6
    assert all(fit.reason == 'nonfinite_training_objective' for fit in fits)
    assert all(
        isinstance(fit, ConvexPairFit)
        and fit.mean_squared_contrast is None
        and fit.left_weight is None
        for fit in fits
    )


@pytest.mark.parametrize(
    'changes',
    [
        {'id': 'sand_a'},
        {'right_candidate_id': 'sand_a'},
        {'minimum_training_groups': 0},
        {'minimum_mean_squared_contrast': 0},
        {'minimum_mean_squared_contrast': float('nan')},
    ],
)
def test_invalid_convex_registrations_are_rejected(changes: dict[str, object]):
    with pytest.raises(EvaluationDocumentError):
        replace(ENSEMBLE, **changes)
