import json
import math
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest
from _training_risk_fixtures import EXAMPLE, training_risk_document

from ptfkit_eval import (
    EvaluationDocumentError,
    RetentionRunResult,
    SigmoidGridFit,
    diagnose_learned_sigmoid_centers,
    execute_retention_run,
    load_retention_dataset,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


def document():
    config = training_risk_document()
    selection = config['learned_selection']
    selection['method'] = 'nested_two_curve_selection_v1'
    selection['fixed_selection']['candidate_ids'] = ['clapp', 'vereecken']
    selection['ensembles'] = [
        {
            'method': 'training_grid_log_pressure_sigmoid_v1',
            'id': 'pressure_gate',
            'left_candidate_id': 'clapp',
            'right_candidate_id': 'vereecken',
            'parameter_grid': [[1, math.log(3)], [10, math.log(3)], [10, 2 * math.log(3)]],
            'minimum_training_groups': 2,
            'minimum_loss_gap': 1e-12,
        }
    ]
    paired = dict(config['independent_training_risk'][0])
    paired.pop('strategy')
    paired.update(
        left_strategy='atomic',
        right_strategy='ensemble',
        left_learner_id='atomic',
        right_learner_id='sigmoid',
        learner_id='joint',
        method='independent_blocks_affine_paired_training_law_v1',
    )
    config['paired_training_risk'] = paired
    config['point_training_risk'] = [
        dict(p, point_metric='mse') for p in config['independent_training_risk']
    ]
    config['selection_resampling'] = [
        {
            'method': 'whole_group_bootstrap_retraining_sensitivity_v1',
            'protocol': 'learned',
            'seed': 20261023,
            'n_resamples': 2,
            'minimum_groups': 8,
        }
    ]
    return config


@pytest.fixture(scope='module')
def native_sigmoid_result() -> RetentionRunResult:
    return execute_retention_run(load_retention_run_plan(document(), base_directory=EXAMPLE.parent))


def test_native_sigmoid_objectives_use_preregistered_pressure_weights_on_outer_training_only(
    native_sigmoid_result: RetentionRunResult,
):
    result = native_sigmoid_result
    selection = result.learned_selection
    assert selection is not None
    points = {
        c.cohort.candidate_id: c.cohort.comparisons
        for c in result.cohorts
        if c.cohort.kind == 'common'
    }
    right = {(p.source_id, p.sample_id, p.suction_kpa): p for p in points['vereecken']}
    for fold in selection.folds:
        fit = fold.ensemble.outer_fit
        assert isinstance(fit, SigmoidGridFit)
        assert fit.parameters is not None
        training = set(selection.splits.folds[fold.fold_id].training_groups)
        assert set(fit.training_groups) == training
        assert fit.training_sample_count == 16
        expected = {}
        for center, slope in fit.plan.parameter_grid:
            by_sample = {}
            for left in points['clapp']:
                if (left.source_id, '') not in training:
                    continue
                key = (left.source_id, left.sample_id)
                other = right[(*key, left.suction_kpa)]
                exponent = round(math.log10(left.suction_kpa) - math.log10(center))
                exponent *= 2 if slope == 2 * math.log(3) else 1
                weight = float(1 / (1 + Fraction(3) ** exponent))
                predicted = weight * left.predicted + (1 - weight) * other.predicted
                log_weight = 1 / 8 if left.suction_kpa in (0.1, 1000) else 1 / 4
                by_sample[key] = (
                    by_sample.get(key, 0) + log_weight * (predicted - left.observed) ** 2
                )
            assert len(by_sample) == 16
            expected[(center, slope)] = sum(by_sample.values()) / 16
        assert {s.parameters: s.mean_training_loss for s in fit.scores} == pytest.approx(
            expected, rel=1e-13
        )
        best = min(expected, key=lambda key: expected[key])
        assert fit.parameters == best
        assert fit.training_loss == pytest.approx(expected[best], rel=1e-13)


def test_native_sigmoid_risk_retraining_and_portable_center_artifacts(
    tmp_path: Path,
    native_sigmoid_result: RetentionRunResult,
):
    result = native_sigmoid_result
    assert len(result.learned_sigmoid_centers) == 24
    assert all(p.status == 'computed' for p in result.learned_sigmoid_centers)
    for point in result.learned_sigmoid_centers:
        assert point.left.predicted is not None
        assert point.right.predicted is not None
        assert point.predicted == pytest.approx((point.left.predicted + point.right.predicted) / 2)
        assert point.left.input_traces
        assert point.right.input_traces
    for item in (*result.independent_training_risk, *result.point_training_risk):
        assert item.bound.training_failure_count == 0
        assert item.bound.test_sample_count == 8
        for block in item.blocks:
            assert isinstance(block.selection.folds[0].ensemble.outer_fit, SigmoidGridFit)
    assert result.paired_training_risk is not None
    assert result.paired_training_risk.bound.transformed_bound is not None
    assert result.paired_training_risk.bound.transformed_bound.training_failure_count == 0
    assert len(result.selection_resampling) == 1
    assert result.selection_resampling[0].complete_replicate_count == 2
    destination = write_retention_run(result, tmp_path / 'sigmoid')
    report = read_retention_run_report(destination)
    assert 'sigmoid (center kPa, steepness)' in report
    assert 'Locked sigmoid centers' in report
    assert 'Available centers: 24/24.' in report
    saved = json.loads((destination / 'learned-sigmoid-centers.json').read_text(encoding='utf-8'))
    assert len(saved) == 24
    replay = execute_retention_run(load_retention_run_plan(destination / 'run-plan.json'))
    assert replay.learned_selection == result.learned_selection
    assert replay.learned_sigmoid_centers == result.learned_sigmoid_centers
    assert replay.independent_training_risk == result.independent_training_risk
    assert replay.point_training_risk == result.point_training_risk
    assert replay.paired_training_risk == result.paired_training_risk
    assert replay.selection_resampling == result.selection_resampling


def test_locked_sigmoid_center_forecasts_do_not_read_observations_or_refit(
    native_sigmoid_result: RetentionRunResult,
):
    result = native_sigmoid_result
    assert result.learned_selection is not None
    document_without_targets = dict(result.plan.dataset.document)
    document_without_targets['observations'] = ()
    dataset = replace(result.plan.dataset, document=document_without_targets)
    selection = replace(
        result.learned_selection,
        folds=tuple(
            replace(
                fold,
                ensemble=replace(fold.ensemble, inner_scores=(), predictions=(), assessment=None),
                atomic=replace(fold.atomic, inner_scores=(), predictions=(), assessment=None),
            )
            for fold in result.learned_selection.folds
        ),
    )
    diagnostic_only = replace(
        result,
        plan=replace(result.plan, dataset=dataset),
        points=(),
        cohorts=(),
        learned_selection=selection,
    )
    assert diagnose_learned_sigmoid_centers(diagnostic_only) == result.learned_sigmoid_centers


@pytest.mark.parametrize(
    'change', ['empty', 'duplicate', 'missing_slope', 'center', 'method', 'extra']
)
def test_native_sigmoid_registration_rejects_unregistered_choices(change: str):
    config = document()
    gate = config['learned_selection']['ensembles'][0]
    if change == 'empty':
        gate['parameter_grid'] = []
    elif change == 'duplicate':
        gate['parameter_grid'][1] = gate['parameter_grid'][0]
    elif change == 'missing_slope':
        gate['parameter_grid'][0] = [10]
    elif change == 'center':
        gate['parameter_grid'][0][0] = 0.1
    elif change == 'method':
        config['learned_selection']['method'] = 'nested_convex_pair_selection_v1'
    else:
        gate['test_adaptive_slope'] = True
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(config, base_directory=EXAMPLE.parent)


def test_missing_member_input_keeps_original_sigmoid_center_and_unavailable_forecast(
    native_sigmoid_result: RetentionRunResult,
):
    result = native_sigmoid_result
    first = result.learned_sigmoid_centers[0]
    key = (first.left.source_id, first.left.sample_id)
    dataset = json.loads(canonical_json(result.plan.dataset.document))
    for sample in dataset['samples']:
        if (sample['source_id'], sample['sample_id']) == key:
            for feature in sample['features']:
                if feature['id'] == 'carbon':
                    feature['value'] = None
    changed = replace(result, plan=replace(result.plan, dataset=load_retention_dataset(dataset)))
    centers = diagnose_learned_sigmoid_centers(changed)
    assert len(centers) == 24
    affected = [c for c in centers if (c.left.source_id, c.left.sample_id) == key]
    assert len(affected) == 1
    point = affected[0]
    assert point.suction_kpa == first.suction_kpa
    assert point.steepness == first.steepness
    assert point.status == 'unavailable'
    assert point.predicted is None
    assert point.left.predicted is not None
    assert point.right.predicted is None
    assert point.right.reasons == ('missing_input',)


def test_unidentified_native_sigmoid_retains_failed_policies_in_every_registered_family():
    config = document()
    config['learned_selection']['ensembles'][0]['minimum_loss_gap'] = 100
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    for policy in (*result.independent_training_risk, *result.point_training_risk):
        assert policy.bound.plan.simultaneous_policy_count == 2
        assert policy.bound.test_sample_count == 8
        assert policy.bound.training_failure_count == (0 if policy.strategy == 'atomic' else 2)
    paired = result.paired_training_risk
    assert paired is not None
    assert paired.bound.transformed_bound is not None
    assert paired.bound.transformed_bound.training_failure_count == 2
    for block in paired.blocks:
        assert block.left.training_failure_reason is None
        assert block.right.training_failure_reason == 'insufficient_inner_evidence'
        assert all(g.sample_losses is None for g in block.right.test_groups)
