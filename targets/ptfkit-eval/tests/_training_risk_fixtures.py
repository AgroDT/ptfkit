import json
from pathlib import Path

from ptfkit_eval import load_retention_run_plan
from ptfkit_eval.documents import canonical_json


EXAMPLE = (
    Path(__file__).resolve().parents[3] / 'evaluation/examples/synthetic_conditional_risk/run.json'
)


def training_risk_document() -> dict:
    source = load_retention_run_plan(EXAMPLE)
    result = json.loads(canonical_json(source.document))
    result['bootstrap']['n_resamples'] = 16
    result.pop('conditional_outer_risk', None)
    result['independent_training_risk'] = [
        {
            'strategy': strategy,
            'seed': 71,
            'population_id': 'iid_binary_group_fixed_predictors_two_samples_v1',
            'learner_id': f'native_nested_selector_{strategy}_four_groups_v1',
            'grouping': 'source',
            'maximum_sample_loss': 1,
            'minimum_group_size': 2,
            'maximum_group_size': 2,
            'training_groups_per_block': 4,
            'test_groups_per_block': 2,
            'n_blocks': 2,
            'total_learner': False,
            'confidence_level': 0.95,
            'assumptions': 'iid_groups_disjoint_blocks_training_only_failure_population_bounds',
            'method': 'independent_blocks_group_hoeffding_training_law_v1',
        }
        for strategy in ('atomic', 'ensemble')
    ]
    return result
