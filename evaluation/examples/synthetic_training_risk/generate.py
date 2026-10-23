"""Generate a larger independent-block run from the declared binary population."""

# ruff: noqa: INP001 - Standalone reproducible example generator.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from random import Random


ROOT = Path(__file__).resolve().parent
PRESSURES = (0.1, 1, 10, 100, 1000)
LOW_TARGETS = (0.4, 0.36, 0.28, 0.2, 0.15)
MINIMUM_BLOCKS = 2


def generate(
    destination: Path,
    *,
    n_blocks: int,
    population_seed: int = 20261023,
    allocation_seed: int = 71,
    metric_resamples: int = 256,
    paired: bool = False,
    point_metrics: bool = False,
) -> Path:
    """Draw every original group once and write a self-contained input directory.

    The independent-block learner always uses four training and two test groups.
    The destination must be new so generation cannot overwrite existing evidence.
    Population and allocation seeds are fixed before observing any run results.
    """
    if (
        isinstance(n_blocks, bool)
        or not isinstance(n_blocks, int)
        or n_blocks < MINIMUM_BLOCKS
        or isinstance(metric_resamples, bool)
        or not isinstance(metric_resamples, int)
        or metric_resamples < MINIMUM_BLOCKS
        or not isinstance(paired, bool)
        or not isinstance(point_metrics, bool)
        or any(
            isinstance(s, bool) or not isinstance(s, int)
            for s in (population_seed, allocation_seed)
        )
    ):
        message = 'Generation needs integer seeds, at least two blocks and two metric resamples.'
        raise ValueError(message)
    template = json.loads(
        (ROOT / '../synthetic_conditional_risk/dataset.json').read_text(encoding='utf-8')
    )
    reference = template['samples'][0]
    old_source = reference['source_id']
    observation = template['observations'][0]
    dataset = {
        **template,
        'dataset_id': f'synthetic_training_risk_{n_blocks}_blocks_seed_{population_seed}',
        'samples': [],
        'observations': [],
    }
    random = Random(population_seed)  # noqa: S311 - Registered reproducible statistical draws.
    for group in range(6 * n_blocks):
        state = random.randrange(2)
        source = f'training_group_{group:04d}'
        for sample_index in range(2):
            sample = json.loads(json.dumps(reference).replace(old_source, source))
            sample_id = f'sample_{sample_index + 1}'
            sample.update(source_id=source, sample_id=sample_id)
            dataset['samples'].append(sample)
            for pressure_index, (pressure, low) in enumerate(
                zip(PRESSURES, LOW_TARGETS, strict=True)
            ):
                row = sample_index * len(PRESSURES) + pressure_index + 1
                dataset['observations'].append(
                    {
                        **observation,
                        'id': f'{source}_{sample_id}_{pressure}',
                        'source_id': source,
                        'sample_id': sample_id,
                        'suction_kpa': pressure,
                        'value': low + state * 0.1 + sample_index * 0.02,
                        'source_cells': [f'{source}_retention!B{row}'],
                    }
                )
    plan = json.loads((ROOT / 'run.json').read_text(encoding='utf-8'))
    evaluation = (ROOT / '../synthetic_retention/evaluation_plan.json').read_bytes()
    payload = (json.dumps(dataset, indent=2) + '\n').encode('utf-8')
    plan['dataset'] = {'path': 'dataset.json', 'sha256': hashlib.sha256(payload).hexdigest()}
    plan['evaluation_plan'] = {
        'path': 'evaluation_plan.json',
        'sha256': hashlib.sha256(evaluation).hexdigest(),
    }
    plan['bootstrap']['n_resamples'] = metric_resamples
    for policy in plan['independent_training_risk']:
        policy.update(seed=allocation_seed, n_blocks=n_blocks)
    if point_metrics:
        plan['point_training_risk'] = [
            dict(policy, point_metric=metric, learner_id=f'{policy["learner_id"]}_{metric}')
            for policy in plan['independent_training_risk']
            for metric in ('mae', 'mse')
        ]
    if paired:
        policy = dict(plan.pop('independent_training_risk')[0])
        policy.pop('strategy')
        policy.update(
            learner_id='joint_atomic_ensemble_four_group_training_v1',
            left_learner_id='inner_selected_atomic_v1',
            right_learner_id='inner_selected_ensemble_v1',
            left_strategy='atomic',
            right_strategy='ensemble',
            method='independent_blocks_affine_paired_training_law_v1',
        )
        if point_metrics:
            policy['point_metric'] = 'mse'
        plan['paired_training_risk'] = policy
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'dataset.json').write_bytes(payload)
    (destination / 'evaluation_plan.json').write_bytes(evaluation)
    (destination / 'run.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')
    (destination / 'generation.json').write_text(
        json.dumps(
            {
                'population_id': 'iid_binary_group_fixed_predictors_two_samples_v1',
                'population_seed': population_seed,
                'dataset_sha256': hashlib.sha256(payload).hexdigest(),
                'allocation_seed': allocation_seed,
                'n_blocks': n_blocks,
                'original_group_count': 6 * n_blocks,
                'training_groups_per_block': 4,
                'test_groups_per_block': 2,
                'metric_resamples': metric_resamples,
                'paired': paired,
                'point_metrics': point_metrics,
            },
            indent=2,
        )
        + '\n',
        encoding='utf-8',
    )
    return destination / 'run.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--blocks', type=int, default=20)
    parser.add_argument('--population-seed', type=int, default=20261023)
    parser.add_argument('--allocation-seed', type=int, default=71)
    parser.add_argument('--metric-resamples', type=int, default=256)
    parser.add_argument('--paired', action='store_true')
    parser.add_argument('--point-metrics', action='store_true')
    arguments = parser.parse_args()
    print(  # noqa: T201 - CLI reports the generated plan path.
        generate(
            arguments.output,
            n_blocks=arguments.blocks,
            population_seed=arguments.population_seed,
            allocation_seed=arguments.allocation_seed,
            metric_resamples=arguments.metric_resamples,
            paired=arguments.paired,
            point_metrics=arguments.point_metrics,
        )
    )
