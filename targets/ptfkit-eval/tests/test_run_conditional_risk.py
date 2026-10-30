import json
from pathlib import Path

import pytest

from ptfkit_eval import (
    EvaluationDocumentError,
    execute_retention_run,
    load_retention_run_plan,
    read_retention_run_report,
    write_retention_run,
)
from ptfkit_eval.documents import canonical_json


EXAMPLE = (
    Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_conditional_risk/run.json'
)


def document():
    source = load_retention_run_plan(EXAMPLE)
    result = json.loads(canonical_json(source.document))
    result.pop('selection_resampling', None)
    result['bootstrap']['n_resamples'] = 16
    result['conditional_outer_risk'] = [
        {
            'protocol': 'learned',
            'strategy': strategy,
            'population_id': 'synthetic_population',
            'grouping': 'source',
            'maximum_sample_loss': 1,
            'minimum_group_size': 2,
            'maximum_group_size': 2,
            'confidence_level': 0.95,
            'assumptions': 'iid_groups_value_independent_partition_population_bounds',
            'method': 'simultaneous_group_hoeffding_conditional_outer_risk_v1',
        }
        for strategy in ('atomic', 'ensemble')
    ]
    return result


def test_native_run_retains_simultaneous_bands_in_verified_portable_artifacts(tmp_path: Path):
    result = execute_retention_run(
        load_retention_run_plan(document(), base_directory=EXAMPLE.parent)
    )
    assert len(result.conditional_outer_risk) == 2
    assert all(item.status == 'computed' for item in result.conditional_outer_risk)
    assert all(item.family_size == 2 for item in result.conditional_outer_risk)
    destination = write_retention_run(result, tmp_path / 'run')
    report = read_retention_run_report(destination)
    assert 'Conditional outer-rule risk bounds' in report
    assert 'family size=2' in report
    assert 'equal-fold mean conditional sample risk' in report
    artifact = json.loads((destination / 'conditional-outer-risk.json').read_text(encoding='utf-8'))
    assert [item['bound']['group_count'] for item in artifact] == [12, 12]
    assert [item['bound']['sample_count'] for item in artifact] == [24, 24]
    replay = execute_retention_run(load_retention_run_plan(destination / 'run-plan.json'))
    assert replay.conditional_outer_risk == result.conditional_outer_risk


def test_native_failed_fit_keeps_its_family_allocation_and_failure_artifact(tmp_path: Path):
    config = document()
    config['learned_selection']['ensembles'][0]['minimum_mean_squared_contrast'] = 100
    config['learned_selection']['fixed_selection']['candidate_ids'] = ['clapp', 'vereecken']
    result = execute_retention_run(load_retention_run_plan(config, base_directory=EXAMPLE.parent))
    assert result.conditional_outer_risk[0].status == 'computed'
    failed = result.conditional_outer_risk[1]
    assert failed.bound is None
    assert failed.reason == 'incomplete_outer_strategy'
    assert failed.family_size == 2
    assert len(failed.fold_failures) == 3
    destination = write_retention_run(result, tmp_path / 'failed')
    artifact = json.loads((destination / 'conditional-outer-risk.json').read_text(encoding='utf-8'))
    assert artifact[1]['bound'] is None
    assert artifact[1]['status'] == 'insufficient_evidence'


@pytest.mark.parametrize(
    'change',
    [
        'duplicate',
        'different_confidence',
        'missing_protocol',
        'assumptions',
        'loss',
        'maximum_group_size',
        'grouping',
    ],
)
def test_invalid_native_inference_registration_is_rejected(change: str):
    config = document()
    item = config['conditional_outer_risk'][1]
    if change == 'duplicate':
        item['strategy'] = 'atomic'
    elif change == 'different_confidence':
        item['confidence_level'] = 0.9
    elif change == 'missing_protocol':
        item['protocol'] = 'fixed'
    elif change == 'assumptions':
        item['assumptions'] = 'infer_independence_from_ids'
    elif change == 'grouping':
        item['grouping'] = 'profile'
    elif change == 'loss':
        item['loss'] = {'method': 'other'}
    else:
        item['maximum_group_size'] = 0
    with pytest.raises(EvaluationDocumentError):
        load_retention_run_plan(config, base_directory=EXAMPLE.parent)
