import json
import math
from dataclasses import replace
from pathlib import Path

import pytest
from _training_risk_fixtures import EXAMPLE, training_risk_document

from ptfkit_eval import (
    BlendGridFit,
    EvaluationDocumentError,
    RetentionRunResult,
    diagnose_learned_blend_endpoints,
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


def document():
    config = training_risk_document()
    config['learned_selection']['method'] = 'nested_two_curve_selection_v1'
    config['learned_selection']['fixed_selection']['candidate_ids'] = ['clapp', 'vereecken']
    config['learned_selection']['ensembles'] = [
        {
            'method': 'training_grid_blend_interval_v1',
            'id': 'trained_blend',
            'left_candidate_id': 'clapp',
            'right_candidate_id': 'vereecken',
            'interval_grid_kpa': [[1, 100], [10, 100]],
            'transform': 'log10',
            'weighting': 'linear',
            'minimum_training_groups': 2,
            'minimum_loss_gap': 1e-12,
        }
    ]
    paired = dict(config['independent_training_risk'][0])
    paired.pop('strategy')
    paired.update(
        learner_id='joint_atomic_grid_blend_training',
        left_learner_id='atomic_training',
        right_learner_id='grid_blend_training',
        left_strategy='atomic',
        right_strategy='ensemble',
        method='independent_blocks_affine_paired_training_law_v1',
    )
    config['paired_training_risk'] = paired
    return config


@pytest.fixture(scope='module')
def native_blend_result() -> RetentionRunResult:
    return execute_retention_run(load_retention_run_plan(document(), base_directory=EXAMPLE.parent))


def test_native_blend_search_matches_independent_grid_objectives_and_portable_risk_evidence(
    tmp_path: Path,
    native_blend_result: RetentionRunResult,
):
    result = native_blend_result
    selection = result.learned_selection
    assert selection is not None
    points = {
        item.cohort.candidate_id: item.cohort.comparisons
        for item in result.cohorts
        if item.cohort.kind == 'common'
    }
    assert len(points['clapp']) == len(points['vereecken']) == 120
    low = {(p.source_id, p.sample_id, p.suction_kpa): p for p in points['vereecken']}
    for fold in selection.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, BlendGridFit)
        training_groups = selection.splits.folds[fold.fold_id].training_groups
        assert fit.training_groups == training_groups
        training_sample_count = 2 * len(training_groups)
        assert fit.training_sample_count == training_sample_count
        scores = []
        for interval in ((1, 100), (10, 100)):
            errors = []
            for p in points['clapp']:
                if (p.source_id, '') not in fit.training_groups:
                    continue
                other = low[p.source_id, p.sample_id, p.suction_kpa]
                # Only 10 kPa is an interior blend point for these two grids.
                weight = (
                    1
                    if p.suction_kpa <= interval[0]
                    else 0
                    if p.suction_kpa >= interval[1]
                    else 0.5
                )
                predicted = weight * p.predicted + (1 - weight) * other.predicted
                integration_weight = 1 / 8 if p.suction_kpa in (0.1, 1000) else 1 / 4
                errors.append(integration_weight * (predicted - p.observed) ** 2)
            objective = math.fsum(errors) / training_sample_count
            scores.append((objective, interval))
        scores.sort()
        assert fit.interval_kpa == scores[0][1]
        assert fit.training_loss == pytest.approx(scores[0][0])
        assert fit.loss_gap == pytest.approx(scores[1][0] - scores[0][0])
    assert all(item.bound.status == 'computed' for item in result.independent_training_risk)
    assert result.paired_training_risk is not None
    assert result.paired_training_risk.bound.status == 'computed'
    assert result.learned_applicability is not None
    directory = write_retention_run(result, tmp_path / 'blend')
    assert 'blend interval kPa=' in read_retention_run_report(directory)
    artifact = json.loads((directory / 'learned-selection.json').read_text(encoding='utf-8'))
    assert artifact['folds'][0]['ensemble']['outer_fit']['plan']['transform'] == 'log10'
    endpoints = json.loads((directory / 'learned-blend-endpoints.json').read_text(encoding='utf-8'))
    assert len(endpoints) == 48
    assert 'Fitted blend endpoint diagnostics' in read_retention_run_report(directory)
    replay = execute_retention_run(load_retention_run_plan(directory / 'run-plan.json'))
    assert replay.learned_selection == selection
    assert replay.independent_training_risk == result.independent_training_risk
    assert replay.paired_training_risk == result.paired_training_risk
    assert replay.learned_blend_endpoints == result.learned_blend_endpoints


def test_locked_blend_endpoints_preserve_full_test_roster_and_member_orientation(
    native_blend_result: RetentionRunResult,
):
    result = native_blend_result
    endpoints = result.learned_blend_endpoints
    assert len(endpoints) == 48
    assert (
        len({(e.outer_fold_id, e.left.source_id, e.left.sample_id, e.side) for e in endpoints})
        == 48
    )
    assert result.learned_selection is not None
    for endpoint in endpoints:
        fit = result.learned_selection.folds[endpoint.outer_fold_id].ensemble.outer_fit
        assert isinstance(fit, BlendGridFit)
        assert fit.interval_kpa is not None
        assert endpoint.suction_kpa == fit.interval_kpa[0 if endpoint.side == 'lower' else 1]
        assert endpoint.active_member == ('left' if endpoint.side == 'lower' else 'right')
        assert endpoint.left.candidate_id == 'clapp'
        assert endpoint.right.candidate_id == 'vereecken'
        assert endpoint.status == 'computed'
        assert endpoint.left.predicted is not None
        assert endpoint.right.predicted is not None
        assert endpoint.right_minus_left == pytest.approx(
            endpoint.right.predicted - endpoint.left.predicted
        )


def test_blend_endpoint_diagnostics_need_only_locked_fit_and_predictors_without_observations(
    native_blend_result: RetentionRunResult,
):
    result = native_blend_result
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    dataset['observations'] = []
    selection = result.learned_selection
    assert selection is not None
    selection = replace(
        selection,
        protocols=(),
        folds=tuple(
            replace(
                fold,
                atomic=replace(fold.atomic, predictions=(), assessment=None, inner_scores=()),
                ensemble=replace(fold.ensemble, predictions=(), assessment=None, inner_scores=()),
            )
            for fold in selection.folds
        ),
    )
    changed = replace(
        result,
        plan=replace(result.plan, dataset=load_retention_dataset(dataset)),
        points=(),
        cohorts=(),
        learned_selection=selection,
    )
    assert diagnose_learned_blend_endpoints(changed) == result.learned_blend_endpoints


def test_missing_member_inputs_remain_explicit_at_both_locked_blend_endpoints(
    native_blend_result: RetentionRunResult,
):
    result = native_blend_result
    first = result.learned_blend_endpoints[0]
    key = (first.left.source_id, first.left.sample_id)
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    for sample in dataset['samples']:
        if (sample['source_id'], sample['sample_id']) == key:
            for feature in sample['features']:
                if feature['id'] == 'carbon':
                    feature['value'] = None
    changed = replace(result, plan=replace(result.plan, dataset=load_retention_dataset(dataset)))
    endpoints = diagnose_learned_blend_endpoints(changed)
    assert len(endpoints) == 48
    unavailable = [e for e in endpoints if (e.left.source_id, e.left.sample_id) == key]
    assert len(unavailable) == 2
    for endpoint in unavailable:
        assert endpoint.status == 'unavailable'
        assert endpoint.left.predicted is not None
        assert endpoint.right.predicted is None
        assert endpoint.right.reasons == ('missing_input',)
        assert endpoint.right_minus_left is None


def test_native_unidentified_blend_grid_remains_a_training_failure_in_both_risk_policies():
    config = document()
    config['learned_selection']['ensembles'][0]['minimum_loss_gap'] = 100
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    assert result.independent_training_risk[0].bound.training_failure_count == 0
    assert result.independent_training_risk[1].bound.training_failure_count == 2
    assert result.paired_training_risk is not None
    transformed = result.paired_training_risk.bound.transformed_bound
    assert transformed is not None
    assert transformed.training_failure_count == 2
    assert all(b.left.training_failure_reason is None for b in result.paired_training_risk.blocks)


@pytest.mark.parametrize('change', ['unordered', 'duplicate', 'axis', 'weighting', 'domain'])
def test_native_blend_schema_and_selection_domain_reject_invalid_grids(change: str):
    config = document()
    grid = config['learned_selection']['ensembles'][0]
    changes = {
        'unordered': ('interval_grid_kpa', [[100, 1], [10, 100]]),
        'duplicate': ('interval_grid_kpa', [[1, 100], [1, 100]]),
        'axis': ('transform', 'automatic'),
        'weighting': ('weighting', 'target_fitted'),
        'domain': ('interval_grid_kpa', [[0.1, 100], [10, 100]]),
    }
    key, value = changes[change]
    grid[key] = value
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(config, base_directory=EXAMPLE.parent)
