import json
from dataclasses import replace
from pathlib import Path

import pytest
from _run_fixtures import dataset_document, evaluation_document, write_run_fixture

from ptfkit_eval import (
    FixedSelectionError,
    FixedSelectionPlan,
    LogPressureLossPlan,
    NestedGroupPlan,
    RangeGatedCurveCandidate,
    RetentionRunResult,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    select_fixed_retention_candidates,
    write_retention_run,
)


PLAN = FixedSelectionPlan(
    candidate_ids=('sand_b', 'ensemble', 'sand_a'),
    folds=NestedGroupPlan(seed=27, outer_folds=3, inner_folds=2),
    loss=LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100),
)


def _fixture(directory: Path) -> Path:
    dataset = json.loads(json.dumps(dataset_document()))
    sample = dataset['samples'][0]
    observation = dataset['observations'][0]
    dataset['samples'] = [{**sample, 'source_id': f'source_{index}'} for index in range(6)]
    dataset['observations'] = [
        {
            **observation,
            'id': f'{index}_{pressure}',
            'source_id': f'source_{index}',
            'suction_kpa': pressure,
            'value': value,
        }
        for index in range(6)
        for pressure, value in ((1, 0.5), (100, 0.4))
    ]
    evaluation = json.loads(json.dumps(evaluation_document()))
    atom = evaluation['candidates'][0]
    evaluation['candidates'].append(
        {
            'id': 'ensemble',
            'kind': 'range_gated_curve',
            'axis': atom['axis'],
            'target': atom['target'],
            'members': [
                {
                    'id': name,
                    'function': atom['function'],
                    'prediction': atom['prediction'],
                    'interval': {
                        'lower': {'value': lower, 'inclusive': inclusive},
                        'upper': {'value': upper, 'inclusive': True},
                    },
                }
                for name, lower, upper, inclusive in (('wet', 1, 10, True), ('dry', 10, 100, False))
            ],
            'routing': {'gap': 'reject', 'extrapolation': 'reject', 'transitions': []},
            'provenance': {'kind': 'fixed', 'source': 'Synthetic predeclared candidate.'},
        }
    )
    return write_run_fixture(directory, dataset=dataset, evaluation=evaluation)


def _controlled_result(directory: Path) -> RetentionRunResult:
    result = execute_retention_run(load_retention_run_plan(_fixture(directory)))
    points = []
    for point in result.points:
        assert point.comparison is not None
        assert point.prediction is not None
        delta = {'sand_a': 0.1, 'sand_b': 0.2, 'ensemble': 0.15}[point.candidate_id]
        predicted = point.observed + delta
        points.append(
            replace(
                point,
                comparison=replace(point.comparison, predicted=predicted),
                prediction=replace(
                    point.prediction,
                    value=predicted,
                    contributions=tuple(
                        replace(item, value=predicted) for item in point.prediction.contributions
                    ),
                ),
            )
        )
    return replace(result, points=tuple(points))


def test_held_out_winner_cannot_change_the_candidate_locked_by_inner_validation(tmp_path: Path):
    result = _controlled_result(tmp_path)
    baseline = select_fixed_retention_candidates(result, plan=PLAN)
    assert baseline.status == 'computed'
    assert baseline.folds[0].atomic.choice.candidate_id == 'sand_a'
    held_out_sources = {group[0] for group in baseline.splits.folds[0].test_groups}
    points = []
    for point in result.points:
        assert point.comparison is not None
        points.append(
            replace(point, observed=1.0, comparison=replace(point.comparison, observed=1.0))
            if point.source_id in held_out_sources
            else point
        )
    changed = select_fixed_retention_candidates(replace(result, points=tuple(points)), plan=PLAN)
    locked = changed.folds[0].atomic

    assert locked.choice.candidate_id == 'sand_a'
    assert locked.choice.inner_scores == baseline.folds[0].atomic.choice.inner_scores
    assert locked.assessment is not None
    # The held-out targets favor B (MSE .125), while locked A has MSE .205.
    assert locked.assessment.mean_loss == pytest.approx(0.205)
    assert locked.assessment.mean_loss is not None
    assert locked.assessment.mean_loss > 0.125


def test_fixed_atomic_and_ensemble_strategies_have_separate_outer_evidence(tmp_path: Path):
    selected = select_fixed_retention_candidates(_controlled_result(tmp_path), plan=PLAN)
    atomic, ensemble = selected.protocols
    assert atomic.kind == 'atomic'
    assert atomic.mean_outer_loss == pytest.approx(0.01)
    assert atomic.selected_counts == (('sand_a', 3),)
    assert atomic.total_sample_count == 6
    assert ensemble.kind == 'ensemble'
    assert ensemble.mean_outer_loss == pytest.approx(0.0225)
    assert ensemble.selected_counts == (('ensemble', 3),)


def test_missing_common_domain_endpoints_report_insufficient_evidence_with_full_denominator(
    tmp_path: Path,
):
    result = _controlled_result(tmp_path)
    points = tuple(point for point in result.points if point.suction_kpa != 100)
    selected = select_fixed_retention_candidates(replace(result, points=points), plan=PLAN)
    assert selected.status == 'insufficient_evidence'
    assert all(item.total_sample_count == 6 for item in selected.protocols)
    assert all(item.mean_outer_loss is None for item in selected.protocols)
    assert selected.folds[0].atomic.choice.reason == 'insufficient_inner_coverage'


def test_learned_candidates_are_rejected_by_the_fixed_selection_api(tmp_path: Path):
    result = _controlled_result(tmp_path)
    candidates = [
        replace(
            candidate,
            provenance=replace(
                candidate.provenance, kind='learned', training_protocol='unsupported'
            ),
        )
        if isinstance(candidate, RangeGatedCurveCandidate)
        else candidate
        for candidate in result.plan.evaluation.candidates
    ]
    evaluation = replace(result.plan.evaluation, candidates=tuple(candidates))
    result = replace(result, plan=replace(result.plan, evaluation=evaluation))
    with pytest.raises(FixedSelectionError, match='Learned'):
        select_fixed_retention_candidates(result, plan=PLAN)


def test_selection_contract_is_executable_and_persisted_with_the_run(tmp_path: Path):
    path = _fixture(tmp_path / 'inputs')
    run = json.loads(path.read_text('utf-8'))
    run['selection'] = {
        'method': 'fixed_candidate_nested_selection_v1',
        'candidate_ids': list(PLAN.candidate_ids),
        'minimum_coverage': 1.0,
        'tie_breaker': 'candidate_id',
        'failure_policy': 'require_common_cohort',
        'folds': {
            'seed': 27,
            'outer_folds': 3,
            'inner_folds': 2,
            'grouping': 'source',
            'missing_profiles': 'reject',
            'minimum_training_groups': 2,
            'minimum_validation_groups': 1,
        },
        'loss': {
            'method': 'log10_trapezoid_mse_v1',
            'lower_suction_kpa': 1,
            'upper_suction_kpa': 100,
            'minimum_points': 2,
        },
    }
    path.write_text(json.dumps(run), encoding='utf-8')
    result = execute_retention_run(load_retention_run_plan(path))
    assert result.selection is not None
    assert result.selection.status == 'computed'
    destination = write_retention_run(result, tmp_path / 'output')
    assert (destination / 'selection.json').is_file()
    assert 'Nested fixed-candidate selection' in read_retention_run_report(destination)
    saved = json.loads((destination / 'selection.json').read_text('utf-8'))
    assert saved['status'] == 'computed'
    assert saved['plan']['folds']['seed'] == 27


def test_lexical_ties_do_not_depend_on_registration_order(tmp_path: Path):
    result = _controlled_result(tmp_path)
    points = tuple(
        replace(point, comparison=replace(point.comparison, predicted=point.observed + 0.1))
        if point.candidate_id == 'sand_b' and point.comparison is not None
        else point
        for point in result.points
    )
    selected = select_fixed_retention_candidates(replace(result, points=points), plan=PLAN)
    assert all(fold.atomic.choice.candidate_id == 'sand_a' for fold in selected.folds)
