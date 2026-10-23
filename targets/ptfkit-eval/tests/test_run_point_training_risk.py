import json
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from _training_risk_fixtures import EXAMPLE, training_risk_document

import ptfkit_eval.training_selection as training_module
from ptfkit_eval import (
    EvaluationDocumentError,
    LearnedNestedSelection,
    PairedPointSelectionTrainingBlock,
    PointErrorLossPlan,
    PointSelectionBlock,
    PointSelectionTrainingRisk,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)


if TYPE_CHECKING:
    from collections.abc import Callable


def document():
    config = training_risk_document()
    config['point_training_risk'] = [
        dict(policy, point_metric=metric, learner_id=f'{policy["learner_id"]}_{metric}')
        for policy in config['independent_training_risk']
        for metric in ('mae', 'mse')
    ]
    return config


def test_point_family_preserves_log_selector_and_scores_full_grids_with_equal_weights(
    tmp_path: Path,
):
    result = execute_retention_run(
        load_retention_run_plan(document(), base_directory=EXAMPLE.parent)
    )
    assert len(result.point_training_risk) == 4
    for item in result.point_training_risk:
        assert isinstance(item, PointSelectionTrainingRisk)
        assert item.bound.plan.simultaneous_policy_count == 4
        baseline = next(p for p in result.independent_training_risk if p.strategy == item.strategy)
        assert item.selector_sha256 == baseline.selector_sha256
        assert [b.selection for b in item.blocks] == [b.selection for b in baseline.blocks]
        assert item.bound.training_failure_count == 0
        assert item.bound.test_sample_count == 8
        metric = item.assessment_loss.metric
        for block in item.blocks:
            assert isinstance(block, PointSelectionBlock)
            selected = getattr(block.selection.folds[0], item.strategy)
            for sample in block.point_losses:
                rows = [
                    p
                    for p in selected.predictions
                    if (p.source_id, p.sample_id) == (sample.source_id, sample.sample_id)
                ]
                errors = [abs(p.predicted - p.observed) for p in rows]
                expected = sum(e if metric == 'mae' else e * e for e in errors) / len(errors)
                assert sample.loss == pytest.approx(expected)
                assert sample.reason is None
                assert sample.point_count == sample.expected_point_count == len(errors)
        moments = item.bound.moments
        assert moments is not None
        # Three bounded moments per registered policy: ln(6*q/alpha)/(2*n).
        radius = float((Decimal(480).ln() / 4).sqrt())
        assert moments.normalized_successful_loss_radius == pytest.approx(radius)
        assert item.bound.unconditional_model_risk_interval is None
        assert item.unconditional_pooled_rmse_interval is None
        if metric == 'mae':
            assert item.successful_training_pooled_rmse_interval is None
    directory = write_retention_run(result, tmp_path / 'points')
    artifact = json.loads((directory / 'point-training-risk.json').read_text(encoding='utf-8'))
    assert len(artifact) == 4
    assert len(artifact[0]['blocks'][0]['point_losses']) == 4
    report = read_retention_run_report(directory)
    assert 'Sample-balanced point training-law risk' in report
    assert 'equal point weights' in report
    assert 'not mean per-training RMSE' in report
    replay = execute_retention_run(load_retention_run_plan(directory / 'run-plan.json'))
    assert replay.point_training_risk == result.point_training_risk


def test_failed_point_policies_remain_in_family_and_keep_every_sample(tmp_path: Path):
    config = document()
    config['learned_selection']['fixed_selection']['candidate_ids'] = ['clapp', 'vereecken']
    config['learned_selection']['ensembles'][0]['minimum_mean_squared_contrast'] = 100
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    for item in result.point_training_risk:
        assert item.bound.plan.simultaneous_policy_count == 4
        assert item.bound.test_sample_count == 8
        if item.strategy == 'atomic':
            assert item.bound.training_failure_count == 0
        else:
            assert item.bound.training_failure_count == 2
            for block in item.blocks:
                assert isinstance(block, PointSelectionBlock)
                assert len(block.point_losses) == 4
                assert all(
                    s.loss is None and s.reason == 'training_failed' for s in block.point_losses
                )
    write_retention_run(result, tmp_path / 'failed')


@pytest.mark.parametrize('change', ['duplicate', 'confidence', 'unknown', 'missing', 'domain'])
def test_invalid_point_registration_is_rejected_before_training(change: str):
    config = document()
    policies = config['point_training_risk']
    if change == 'duplicate':
        policies[1] = deepcopy(policies[0])
    elif change == 'confidence':
        policies[1]['confidence_level'] = 0.9
    elif change == 'unknown':
        policies[0]['point_metric'] = 'rmse'
    elif change == 'missing':
        policies[0].pop('point_metric')
    else:
        policies[0]['loss'] = {'lower_suction_kpa': 10}
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(config, base_directory=EXAMPLE.parent)


@pytest.mark.parametrize('metric', ['mae', 'mse'])
def test_paired_point_assessment_retains_each_raw_error_and_uses_joint_success(metric: str):
    config = document()
    paired = dict(config['point_training_risk'][0], point_metric=metric)
    paired.pop('strategy')
    paired.update(
        left_strategy='atomic',
        right_strategy='ensemble',
        left_learner_id='atomic',
        right_learner_id='ensemble',
        learner_id='joint',
        method='independent_blocks_affine_paired_training_law_v1',
    )
    config['paired_training_risk'] = paired
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    assessment = result.paired_training_risk
    assert assessment is not None
    assert isinstance(assessment.bound.plan.bounds.loss, PointErrorLossPlan)
    assert assessment.bound.plan.bounds.loss.metric == metric
    assert assessment.bound.transformed_bound is not None
    assert assessment.bound.transformed_bound.plan.simultaneous_policy_count == 1
    for block in assessment.blocks:
        assert isinstance(block, PairedPointSelectionTrainingBlock)
        for strategy in ('atomic', 'ensemble'):
            records = block.left_point_losses if strategy == 'atomic' else block.right_point_losses
            evidence = block.left if strategy == 'atomic' else block.right
            predictions = getattr(block.selection.folds[0], strategy).predictions
            by_sample = {}
            for point in predictions:
                error = abs(point.predicted - point.observed)
                by_sample.setdefault((point.source_id, point.sample_id), []).append(
                    error if metric == 'mae' else error * error
                )
            assert len(records) == 4
            for sample in records:
                values = by_sample[(sample.source_id, sample.sample_id)]
                assert sample.loss == pytest.approx(sum(values) / len(values))
            raw = {}
            for group in evidence.test_groups:
                assert group.sample_losses is not None
                raw.update(zip(group.group.samples, group.sample_losses, strict=True))
            assert raw == pytest.approx({(p.source_id, p.sample_id): p.loss for p in records})


def test_missing_selected_test_forecast_suppresses_bound_without_reclassifying_training(
    monkeypatch: pytest.MonkeyPatch,
):
    actual = training_module.select_grouped_forecast_holdout

    def missing_interior(*args: object, **kwargs: object) -> LearnedNestedSelection:
        selection = cast('Callable[..., LearnedNestedSelection]', actual)(*args, **kwargs)
        fold = selection.folds[0]
        assert fold.ensemble.candidate_id is not None
        assert any(p.suction_kpa == 10 for p in fold.ensemble.predictions)
        changed = replace(
            fold.ensemble,
            predictions=tuple(p for p in fold.ensemble.predictions if p.suction_kpa != 10),
        )
        return replace(selection, folds=(replace(fold, ensemble=changed),))

    monkeypatch.setattr(training_module, 'select_grouped_forecast_holdout', missing_interior)
    config = document()
    config.pop('independent_training_risk')
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    for item in result.point_training_risk:
        assert item.bound.training_failure_count == 0
        assert item.bound.test_sample_count == 8
        if item.strategy == 'atomic':
            assert item.bound.reason is None
        else:
            assert item.bound.reason == 'incomplete_successful_block_test_losses'
            assert item.bound.risk_mass_on_success_interval is None
            for block in item.blocks:
                assert isinstance(block, PointSelectionBlock)
                assert block.evidence.training_failure_reason is None
                assert len(block.point_losses) == 4
                assert all(p.loss is None for p in block.point_losses)
                assert {p.reason for p in block.point_losses} == {'incomplete_forecast_grid'}
                assert {p.point_count for p in block.point_losses} == {4}
                assert {p.expected_point_count for p in block.point_losses} == {5}
