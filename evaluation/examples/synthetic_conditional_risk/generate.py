"""Generate a fixed-size IID binary-group population example without real data."""

# ruff: noqa: INP001 - Standalone example generator.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from random import Random


ROOT = Path(__file__).resolve().parent
SEED = 20261023
PRESSURES = (0.1, 1, 10, 100, 1000)
LOW_TARGETS = (0.4, 0.36, 0.28, 0.2, 0.15)


def generate() -> None:
    """Draw twelve independent fair group states and retain all twenty-four samples."""
    template = json.loads(
        (ROOT / '../synthetic_retraining/dataset.json').read_text(encoding='utf-8')
    )
    reference = template['samples'][0]
    old_source = reference['source_id']
    observation = template['observations'][0]
    dataset = {
        **template,
        'dataset_id': 'synthetic_iid_conditional_risk',
        'samples': [],
        'observations': [],
    }
    random = Random(SEED)  # noqa: S311 - Reproducible statistical draws.
    for group in range(12):
        state = random.randrange(2)
        source = f'conditional_group_{group:02d}'
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
    payload = (json.dumps(dataset, indent=2) + '\n').encode('utf-8')
    (ROOT / 'dataset.json').write_bytes(payload)
    plan = json.loads((ROOT / '../synthetic_retraining/run.json').read_text(encoding='utf-8'))
    plan.pop('selection_resampling')
    plan['dataset'] = {'path': 'dataset.json', 'sha256': hashlib.sha256(payload).hexdigest()}
    plan['conditional_outer_risk'] = [
        {
            'protocol': 'learned',
            'strategy': strategy,
            'population_id': 'iid_binary_group_fixed_predictors_two_samples_v1',
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
    (ROOT / 'run.json').write_text(json.dumps(plan, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    generate()
