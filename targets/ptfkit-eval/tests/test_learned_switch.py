import json
from dataclasses import replace
from pathlib import Path

import pytest
from _run_fixtures import dataset_document, write_run_fixture

from ptfkit_eval import (
    ConvexPairPlan,
    EvaluationDocumentError,
    FixedSelectionPlan,
    HardSwitchGridFit,
    HardSwitchGridPlan,
    LearnedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RetentionRunResult,
    execute_retention_run,
    load_retention_run_plan,
    select_learned_retention_candidates,
)


SWITCH = HardSwitchGridPlan(
    id='trained_switch',
    left_candidate_id='sand_a',
    right_candidate_id='sand_b',
    boundary_grid_kpa=(5, 10),
    boundary_member='left',
    minimum_training_groups=2,
    minimum_loss_gap=1e-6,
)
PLAN = LearnedSelectionPlan(
    fixed=FixedSelectionPlan(
        candidate_ids=('sand_a', 'sand_b'),
        folds=NestedGroupPlan(seed=27, outer_folds=3, inner_folds=2),
        loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
    ),
    ensembles=(SWITCH,),
    method='nested_two_curve_selection_v1',
)


def _result(directory: Path) -> RetentionRunResult:
    dataset = json.loads(json.dumps(dataset_document()))
    template, observation = dataset['samples'][0], dataset['observations'][0]
    dataset['samples'] = [{**template, 'source_id': f'source_{index}'} for index in range(6)]
    dataset['observations'] = [
        {
            **observation,
            'id': f'{index}_{pressure}',
            'source_id': f'source_{index}',
            'suction_kpa': pressure,
            'value': value,
        }
        for index in range(6)
        for pressure, value in ((1, 0.75), (10, 0.75), (100, 0.25))
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


def test_boundary_search_uses_training_only_and_recovers_exact_registered_switch(tmp_path: Path):
    selected = select_learned_retention_candidates(_result(tmp_path), plan=PLAN)
    assert selected.method == 'nested_two_curve_selection_v1'
    assert selected.status == 'computed'
    for fold in selected.folds:
        outer = selected.splits.folds[fold.fold_id]
        assert fold.atomic.candidate_id == 'sand_a'
        assert fold.atomic.assessment is not None
        assert fold.atomic.assessment.mean_loss == pytest.approx(1 / 16)
        assert fold.ensemble.candidate_id == 'trained_switch'
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, HardSwitchGridFit)
        assert fit.training_groups == outer.training_groups
        assert fit.training_sample_count == fit.usable_group_count == 4
        assert fit.switch_suction_kpa == 10
        assert fit.training_loss == 0
        assert fit.loss_gap == pytest.approx(1 / 8)
        assert [(score.suction_kpa, score.mean_training_loss) for score in fit.scores] == [
            (5, 1 / 8),
            (10, 0),
        ]
        for evidence, inner in zip(fold.ensemble.inner_scores[0].folds, outer.inner, strict=True):
            assert isinstance(evidence.fit, HardSwitchGridFit)
            assert evidence.fit.training_groups == inner.training_groups
            assert set(evidence.fit.training_groups).isdisjoint(inner.validation_groups)
            assert evidence.fit.switch_suction_kpa == 10
        assert [point.predicted for point in fold.ensemble.predictions] == [0.75, 0.75, 0.25] * 2


def test_untouched_outer_targets_cannot_choose_or_refit_the_boundary(tmp_path: Path):
    result = _result(tmp_path)
    before = select_learned_retention_candidates(result, plan=PLAN)
    held_out = {source for source, _ in before.splits.folds[0].test_groups}
    points = tuple(
        replace(point, comparison=replace(point.comparison, observed=1 - point.observed))
        if point.source_id in held_out and point.comparison is not None
        else point
        for point in result.points
    )
    after = select_learned_retention_candidates(replace(result, points=points), plan=PLAN)
    first, changed = before.folds[0].ensemble, after.folds[0].ensemble
    assert changed.inner_scores == first.inner_scores
    assert changed.candidate_id == first.candidate_id
    assert changed.outer_fit == first.outer_fit
    assert isinstance(changed.outer_fit, HardSwitchGridFit)
    assert changed.outer_fit.switch_suction_kpa == 10
    assert changed.assessment is not None
    # Held-out targets would favor boundary 5 (loss 1/8), but the locked 10 loses 1/4.
    assert changed.assessment.mean_loss == pytest.approx(1 / 4)


def test_boundary_owner_changes_the_exact_switch_point_prediction(tmp_path: Path):
    policy = replace(
        PLAN, ensembles=(replace(SWITCH, boundary_grid_kpa=(10, 20), boundary_member='right'),)
    )
    selected = select_learned_retention_candidates(_result(tmp_path), plan=policy)
    for fold in selected.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, HardSwitchGridFit)
        assert fit.switch_suction_kpa == 20
        assert [(score.suction_kpa, score.mean_training_loss) for score in fit.scores] == [
            (10, 1 / 8),
            (20, 0),
        ]


def test_outer_refit_recomputes_the_grid_objective_on_all_training_samples(tmp_path: Path):
    result = _result(tmp_path)
    middle_targets = (0.25, 0.26, 0.27, 0.6, 0.65, 0.7)
    points = tuple(
        replace(
            point,
            comparison=replace(point.comparison, observed=middle_targets[int(point.source_id[-1])]),
        )
        if point.suction_kpa == 10 and point.comparison is not None
        else point
        for point in result.points
    )
    selected = select_learned_retention_candidates(replace(result, points=points), plan=PLAN)
    different_inner_seen = False
    for fold in selected.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, HardSwitchGridFit)
        mean_target = sum(
            middle_targets[int(source[-1])] for source, _ in fit.usable_samples
        ) / len(fit.usable_samples)
        assert fit.switch_suction_kpa == (10 if mean_target > 0.5 else 5)
        for evidence in fold.ensemble.inner_scores[0].folds:
            assert isinstance(evidence.fit, HardSwitchGridFit)
            different_inner_seen |= evidence.fit.switch_suction_kpa != fit.switch_suction_kpa
    assert different_inner_seen


@pytest.mark.parametrize(
    ('gap', 'expected_status'), [(0.125, 'insufficient_evidence'), (0.124, 'computed')]
)
def test_loss_separation_gate_is_strict(tmp_path: Path, gap: float, expected_status: str):
    policy = replace(PLAN, ensembles=(replace(SWITCH, minimum_loss_gap=gap),))
    selected = select_learned_retention_candidates(_result(tmp_path), plan=policy)
    assert selected.protocols[1].status == expected_status


def test_indistinguishable_boundaries_remain_unidentified_instead_of_defaulting(tmp_path: Path):
    policy = replace(PLAN, ensembles=(replace(SWITCH, boundary_grid_kpa=(5, 6)),))
    selected = select_learned_retention_candidates(_result(tmp_path), plan=policy)
    assert selected.protocols[1].status == 'insufficient_evidence'
    for fold in selected.folds:
        assert fold.ensemble.candidate_id is None
        for evidence in fold.ensemble.inner_scores[0].folds:
            fit = evidence.fit
            assert isinstance(fit, HardSwitchGridFit)
            assert fit.reason == 'unidentifiable_boundary'
            assert fit.loss_gap == 0
            assert fit.switch_suction_kpa is None
            assert len(fit.scores) == 2


@pytest.mark.parametrize(
    'changes',
    [
        {'boundary_grid_kpa': ()},
        {'boundary_grid_kpa': (10,)},
        {'boundary_grid_kpa': (5, 5)},
        {'boundary_grid_kpa': (0, 5)},
        {'boundary_grid_kpa': (5, float('inf'))},
        {'boundary_member': 'nearest'},
        {'minimum_loss_gap': 0},
        {'minimum_training_groups': True},
    ],
)
def test_invalid_switch_registrations_fail(changes: dict[str, object]):
    with pytest.raises(EvaluationDocumentError):
        replace(SWITCH, **changes)


@pytest.mark.parametrize('grid', [(1, 10), (10, 100), (0.5, 10), (10, 1000)])
def test_boundaries_must_be_strictly_inside_the_registered_loss_domain(grid: tuple[float, ...]):
    with pytest.raises(EvaluationDocumentError, match='strictly inside'):
        replace(PLAN, ensembles=(replace(SWITCH, boundary_grid_kpa=grid),))


def test_switch_cannot_silently_use_the_older_convex_only_protocol():
    with pytest.raises(EvaluationDocumentError):
        replace(PLAN, method='nested_convex_pair_selection_v1')


def test_switches_compete_with_convex_pairs_using_inner_evidence(tmp_path: Path):
    convex = ConvexPairPlan(
        id='convex',
        left_candidate_id='sand_a',
        right_candidate_id='sand_b',
        minimum_training_groups=2,
        minimum_mean_squared_contrast=1e-12,
    )
    selected = select_learned_retention_candidates(
        _result(tmp_path), plan=replace(PLAN, ensembles=(convex, SWITCH))
    )
    assert all(fold.ensemble.candidate_id == 'trained_switch' for fold in selected.folds)
    for fold in selected.folds:
        assert [(score.candidate_id, score.mean_loss) for score in fold.ensemble.inner_scores] == [
            ('convex', 3 / 64),
            ('trained_switch', 0),
        ]


def test_switch_grid_and_input_row_order_do_not_change_fitted_results(tmp_path: Path):
    result = _result(tmp_path)
    baseline = select_learned_retention_candidates(result, plan=PLAN)
    reordered = replace(PLAN, ensembles=(replace(SWITCH, boundary_grid_kpa=(10, 5)),))
    assert (
        select_learned_retention_candidates(
            replace(result, points=result.points[::-1]), plan=reordered
        )
        == baseline
    )


def test_training_group_gate_preserves_failures_without_default_boundary(tmp_path: Path):
    selected = select_learned_retention_candidates(
        _result(tmp_path),
        plan=replace(PLAN, ensembles=(replace(SWITCH, minimum_training_groups=99),)),
    )
    assert selected.protocols[1].status == 'insufficient_evidence'
    for fold in selected.folds:
        assert fold.ensemble.candidate_id is None
        for evidence in fold.ensemble.inner_scores[0].folds:
            fit = evidence.fit
            assert isinstance(fit, HardSwitchGridFit)
            assert fit.reason == 'too_few_training_groups'
            assert fit.switch_suction_kpa is None
            assert fit.scores == ()
