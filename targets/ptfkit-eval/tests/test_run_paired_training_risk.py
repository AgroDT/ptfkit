import json
from decimal import Decimal
from pathlib import Path

import pytest
from _training_risk_fixtures import EXAMPLE, training_risk_document

from ptfkit_eval import (
    EvaluationDocumentError,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)


def document():
    config = training_risk_document()
    paired = dict(config.pop('independent_training_risk')[0])
    paired.pop('strategy')
    paired.update(
        learner_id='joint_atomic_ensemble_training_v1',
        left_learner_id='inner_selected_atomic_v1',
        right_learner_id='inner_selected_ensemble_v1',
        left_strategy='atomic',
        right_strategy='ensemble',
        method='independent_blocks_affine_paired_training_law_v1',
    )
    config['paired_training_risk'] = paired
    return config


def test_native_paired_registration_retains_both_rules_on_identical_roles_and_replays(
    tmp_path: Path,
):
    result = execute_retention_run(
        load_retention_run_plan(document(), base_directory=EXAMPLE.parent)
    )
    paired = result.paired_training_risk
    assert paired is not None
    assert paired.bound.status == 'computed'
    transformed = paired.bound.transformed_bound
    assert transformed is not None
    assert transformed.training_failure_count == 0
    assert transformed.test_sample_count == 8
    assert transformed.plan.maximum_sample_loss == 1
    assert transformed.plan.simultaneous_policy_count == 1
    assert paired.bound.joint_success_risk_reason == 'success_probability_not_separated_from_zero'
    assert paired.bound.unconditional_mean_risk_difference_interval is None
    for block in paired.blocks:
        assert block.left.training_groups == block.right.training_groups
        assert [g.group for g in block.left.test_groups] == [
            g.group for g in block.right.test_groups
        ]
        assert block.left.training_failure_reason is None
        assert block.right.training_failure_reason is None
        assert block.selection.folds[0].atomic.inner_scores
        assert block.selection.folds[0].ensemble.inner_scores
    directory = write_retention_run(result, tmp_path / 'paired')
    report = read_retention_run_report(directory)
    assert 'Paired training-law risk difference' in report
    assert 'Orientation: atomic minus ensemble' in report
    assert 'both training procedures succeeding' in report
    assert 'unconditional model-risk difference=unavailable' in report
    artifact = json.loads((directory / 'paired-training-risk.json').read_text(encoding='utf-8'))
    assert len(artifact['blocks']) == 2
    assert len(artifact['samples']) == 24
    replay = execute_retention_run(load_retention_run_plan(directory / 'run-plan.json'))
    assert replay.paired_training_risk == paired


@pytest.mark.parametrize('total', [False, True])
def test_failed_one_sided_training_retains_successful_rule_and_joint_failure_law(
    tmp_path: Path,
    *,
    total: bool,
):
    config = document()
    config['paired_training_risk']['total_learner'] = total
    config['learned_selection']['fixed_selection']['candidate_ids'] = ['clapp', 'vereecken']
    config['learned_selection']['ensembles'][0]['minimum_mean_squared_contrast'] = 100
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    paired = result.paired_training_risk
    assert paired is not None
    transformed = paired.bound.transformed_bound
    assert transformed is not None
    assert transformed.training_failure_count == 2
    assert transformed.test_sample_count == 8
    assert paired.bound.reason == ('total_learner_assertion_violated' if total else None)
    for block in paired.blocks:
        assert block.left.training_failure_reason is None
        assert all(g.sample_losses is not None for g in block.left.test_groups)
        assert block.right.training_failure_reason == 'insufficient_inner_evidence'
        assert all(g.sample_losses is None for g in block.right.test_groups)
    directory = write_retention_run(result, tmp_path / 'failed')
    report = read_retention_run_report(directory)
    assert 'right=insufficient_inner_evidence' in report
    assert 'unconditional model-risk difference=unavailable' in report
    if total:
        assert 'total_learner_assertion_violated' in report
        assert paired.bound.joint_success_probability_interval is None


@pytest.mark.parametrize(
    'change', ['same_strategy', 'same_learner', 'method', 'missing_id', 'array', 'budget']
)
def test_ambiguous_or_unsupported_native_paired_registrations_are_rejected(change: str):
    config = document()
    policy = config['paired_training_risk']
    if change == 'same_strategy':
        policy['right_strategy'] = 'atomic'
    elif change == 'same_learner':
        policy['right_learner_id'] = policy['left_learner_id']
    elif change == 'method':
        policy['method'] = 'independent_blocks_group_hoeffding_training_law_v1'
    elif change == 'missing_id':
        policy.pop('left_learner_id')
    elif change == 'array':
        config['paired_training_risk'] = [policy]
    else:
        policy['simultaneous_policy_count'] = 3
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(config, base_directory=EXAMPLE.parent)


def test_paired_comparison_has_its_own_budget_without_reallocating_marginal_families():
    config = training_risk_document()
    config['paired_training_risk'] = document()['paired_training_risk']
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    paired = result.paired_training_risk
    assert paired is not None
    transformed = paired.bound.transformed_bound
    assert transformed is not None
    assert transformed.moments is not None
    radius = float((Decimal(120).ln() / 4).sqrt())
    assert transformed.moments.normalized_successful_loss_radius == pytest.approx(radius)
    for item in result.independent_training_risk:
        assert item.bound.moments is not None
        radius = float((Decimal(240).ln() / 4).sqrt())
        assert item.bound.moments.normalized_successful_loss_radius == pytest.approx(radius)
        assert item.bound.plan.simultaneous_policy_count == 2
