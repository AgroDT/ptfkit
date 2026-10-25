"""Build the single-pressure restriction of the independent two-pressure fixture."""

# ruff: noqa: INP001 - Standalone reproducible example builder.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ptfkit_eval.documents import canonical_json


PRESSURE_KPA = 33


def build(output: Path) -> Path:
    """Keep published-coefficient synthetic targets; do not generate them with candidates."""
    source = Path(__file__).resolve().parent.parent / 'synthetic_discrete_retention'
    dataset = json.loads((source / 'dataset.json').read_bytes())
    evaluation = json.loads((source / 'evaluation_plan.json').read_bytes())
    run = json.loads((source / 'run.json').read_bytes())
    dataset['dataset_id'] = 'synthetic_single_pressure_retention'
    dataset['observations'] = [
        o for o in dataset['observations'] if o['suction_kpa'] == PRESSURE_KPA
    ]
    for candidate in evaluation['candidates']:
        candidate['kind'] = 'function_point'
        candidate['prediction'] = {'kind': 'fixed_output', 'name': 'water_field_capacity'}
    loss = {'method': 'single_pressure_mse_v1', 'suction_kpa': PRESSURE_KPA}
    run['selection']['loss'] = loss
    run['learned_selection']['fixed_selection']['loss'] = loss
    run['learned_selection']['ensembles'][0]['method'] = 'constant_convex_pair_single_pressure_v1'
    run['protocol']['id'] = 'synthetic_single_pressure_retention_v1'
    output.mkdir(parents=True, exist_ok=False)
    for name, value in (('dataset', dataset), ('evaluation_plan', evaluation)):
        raw = canonical_json(value)
        (output / f'{name}.json').write_bytes(raw)
        run[name] = {'path': f'{name}.json', 'sha256': hashlib.sha256(raw).hexdigest()}
    path = output / 'run.json'
    path.write_bytes(canonical_json(run))
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    print(build(parser.parse_args().output))  # noqa: T201 - CLI reports the generated plan path.
