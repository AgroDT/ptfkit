import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest
from _training_risk_fixtures import EXAMPLE
from _training_risk_fixtures import training_risk_document as document

from ptfkit_eval import (
    EvaluationDocumentError,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)


def test_native_registration_runs_whole_selector_and_replays_complete_portable_evidence(
    tmp_path: Path,
):
    result = execute_retention_run(
        load_retention_run_plan(document(), base_directory=EXAMPLE.parent)
    )
    assert len(result.independent_training_risk) == 2
    for item in result.independent_training_risk:
        assert item.bound.status == 'computed'
        assert item.bound.training_failure_count == 0
        assert item.bound.test_sample_count == 8
        assert item.bound.unconditional_model_risk_interval is None
        assert item.bound.moments is not None
        # Three two-sided events for q=2, alpha=.05 and n=2: sqrt(ln(240)/4).
        radius = float((Decimal(240).ln() / 4).sqrt())
        assert item.bound.moments.normalized_successful_loss_radius == pytest.approx(radius)
        assert item.bound.plan.simultaneous_policy_count == 2
        assert item.bound.moments.normalized_group_size_radius == 0
        assert len(item.blocks) == 2
    directory = write_retention_run(result, tmp_path / 'run')
    report = read_retention_run_report(directory)
    assert 'Independent training-law risk bounds' in report
    assert 'training groups/block=4' in report
    assert 'family size=2' in report
    assert 'unconditional model risk=unavailable' in report
    data = json.loads((directory / 'independent-training-risk.json').read_text(encoding='utf-8'))
    assert len(data) == 2
    first = data[0]
    assert len(first['samples']) == 24
    assert len(first['blocks'][0]['roles']['training_groups']) == 4
    assert len(first['blocks'][0]['selection']['folds']) == 1
    assert len(first['blocks'][0]['selection']['folds'][0]['atomic']['inner_scores']) == 2
    replay = execute_retention_run(load_retention_run_plan(directory / 'run-plan.json'))
    assert replay.independent_training_risk == result.independent_training_risk


def test_failed_native_ensemble_keeps_registered_budget_and_full_block_records(tmp_path: Path):
    config = document()
    config['learned_selection']['fixed_selection']['candidate_ids'] = ['clapp', 'vereecken']
    config['learned_selection']['ensembles'][0]['minimum_mean_squared_contrast'] = 100
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    atomic, ensemble = result.independent_training_risk
    assert atomic.bound.training_failure_count == 0
    assert ensemble.bound.status == 'computed'  # The failure probability is itself a target.
    assert ensemble.bound.training_failure_count == 2
    assert ensemble.bound.plan.simultaneous_policy_count == 2
    assert ensemble.bound.test_sample_count == 8
    assert ensemble.bound.unconditional_model_risk_interval is None
    assert ensemble.bound.moments is not None
    radius = float((Decimal(240).ln() / 4).sqrt())
    assert ensemble.bound.moments.training_success_radius == pytest.approx(radius)
    assert all(
        b.evidence.training_failure_reason == 'insufficient_inner_evidence' for b in ensemble.blocks
    )
    destination = write_retention_run(result, tmp_path / 'failed')
    report = read_retention_run_report(destination)
    assert 'failed training=2' in report
    assert report.count('insufficient_inner_evidence') >= 2
    data = json.loads((destination / 'independent-training-risk.json').read_text(encoding='utf-8'))
    assert all(
        g['sample_losses'] is None for b in data[1]['blocks'] for g in b['evidence']['test_groups']
    )


def test_missing_profile_fallback_is_resolved_once_before_native_block_allocation(tmp_path: Path):
    config = document()
    dataset = json.loads((EXAMPLE.parent / 'dataset.json').read_text(encoding='utf-8'))
    dataset['samples'][0]['profile_id'] = None
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps(dataset), encoding='utf-8')
    config['dataset'] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    folds = config['learned_selection']['fixed_selection']['folds']
    folds['grouping'], folds['missing_profiles'] = 'profile', 'source'
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    for item in result.independent_training_risk:
        assert item.allocation.plan.grouping == 'source'
        assert item.bound.status == 'computed'
        assert item.selection_plan.fixed.folds.grouping == 'source'
        assert item.selection_plan.fixed.folds.missing_profiles == 'reject'
        for block in item.blocks:
            assert block.selection.splits.effective_grouping == 'source'
            assert all(
                g.group_id[1] == ''
                for g in (*block.roles.training_groups, *block.roles.test_groups)
            )


@pytest.mark.parametrize(
    'change',
    [
        'duplicate',
        'confidence',
        'grouping',
        'count',
        'missing_selector',
        'assumptions',
        'method',
        'loss_override',
        'totality_type',
        'missing_learner',
        'seed_type',
    ],
)
def test_invalid_training_law_registration_is_rejected(change: str):
    config = document()
    policy = config['independent_training_risk'][1]
    replacements = {
        'duplicate': ('strategy', 'atomic'),
        'confidence': ('confidence_level', 0.9),
        'grouping': ('grouping', 'profile'),
        'count': ('training_groups_per_block', 5),
        'assumptions': ('assumptions', 'ordinary_cv_folds'),
        'method': ('method', 'bootstrap'),
        'loss_override': ('loss', {'lower_suction_kpa': 1, 'upper_suction_kpa': 100}),
        'totality_type': ('total_learner', 1),
        'seed_type': ('seed', True),
    }
    if change == 'missing_selector':
        config.pop('learned_selection')
    elif change == 'missing_learner':
        policy.pop('learner_id')
    else:
        key, value = replacements[change]
        policy[key] = value
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(config, base_directory=EXAMPLE.parent)
