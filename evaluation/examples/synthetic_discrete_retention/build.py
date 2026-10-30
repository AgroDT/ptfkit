"""Build a synthetic, finite-pressure benchmark for native multi-output PTFs."""

# ruff: noqa: INP001 - Standalone reproducible example builder.

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from ptfkit_eval.documents import canonical_json


def build(directory: Path) -> Path:
    """Use hand-derived Table 5 numbers; no ptfkit callable generates the targets."""
    target = {
        'quantity': 'gravimetric_water_content',
        'unit': 'mass_fraction',
        'material_basis': 'fine_earth',
        'denominator_basis': 'dry_soil_mass',
    }
    method = 'klute1986_disturbed_ring_retention'
    samples, observations = [], []
    for index in range(6):
        sample = f'soil_{index}'
        features = []
        for name, value, lower, upper in [('clay', 20, None, 2), ('sand', 50, 50, 2000)]:
            features.append(
                {
                    'id': name,
                    'kind': 'numeric',
                    'value': value,
                    'review_status': 'confirmed',
                    'origin': 'synthetic',
                    'source_cells': [f'generator:{sample}:{name}'],
                    'measurement': {
                        'quantity': 'particle_mass_fraction',
                        'unit': 'mass_percent',
                        'basis': {'material': 'fine_earth', 'denominator': 'dry_mass'},
                        'method': 'bouyoucos1962_hydrometer_hexametaphosphate_5_percent',
                        'conditions': [],
                        'particle_size': {
                            'unit': 'micrometer',
                            'lower': None if lower is None else {'value': lower, 'inclusive': True},
                            'upper': {'value': upper, 'inclusive': False},
                        },
                    },
                }
            )
        samples.append(
            {
                'source_id': 'synthetic',
                'sample_id': sample,
                'profile_id': sample,
                'features': features,
            }
        )
        for pressure, water in [(33, 0.1825425), (1500, 0.10713)]:
            observations.append(
                {
                    'id': f'{sample}_{pressure}',
                    'source_id': 'synthetic',
                    'sample_id': sample,
                    'suction_kpa': pressure,
                    'value': water,
                    'origin': 'synthetic',
                    'review_status': 'confirmed',
                    'quality_flags': [],
                    'source_cells': [f'generator:{sample}:{pressure}'],
                }
            )
    dataset = {
        'schema_version': 2,
        'dataset_id': 'synthetic_discrete_retention',
        'kind': 'synthetic',
        'target': target,
        'method': method,
        'samples': samples,
        'observations': observations,
    }
    evaluation = {
        'schema_version': 2,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': name,
                'kind': 'function_points',
                'function': f'calc_ptf_beniaich2023_{name}',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'log10',
                },
                'target': target,
                'prediction': {
                    'kind': 'fixed_outputs',
                    'names': ['water_field_capacity', 'water_wilting_point'],
                },
            }
            for name in ('slr1', 'slr3')
        ],
    }
    selection = {
        'method': 'fixed_candidate_nested_selection_v1',
        'candidate_ids': ['slr1', 'slr3'],
        'minimum_coverage': 1.0,
        'tie_breaker': 'candidate_id',
        'failure_policy': 'require_common_cohort',
        'folds': {
            'seed': 20261025,
            'outer_folds': 3,
            'inner_folds': 2,
            'grouping': 'profile',
            'missing_profiles': 'reject',
            'minimum_training_groups': 2,
            'minimum_validation_groups': 1,
        },
        'loss': {
            'method': 'log10_trapezoid_mse_v1',
            'lower_suction_kpa': 33,
            'upper_suction_kpa': 1500,
            'minimum_points': 2,
        },
    }
    directory.mkdir(parents=True, exist_ok=True)
    if any(
        (directory / name).exists() for name in ('dataset.json', 'evaluation_plan.json', 'run.json')
    ):
        message = 'Example inputs already exist; choose a fresh output directory.'
        raise FileExistsError(message)
    references = {}
    for name, document in [('dataset', dataset), ('evaluation_plan', evaluation)]:
        raw = canonical_json(document)
        with (directory / f'{name}.json').open('xb') as stream:
            stream.write(raw)
        references[name] = {'path': f'{name}.json', 'sha256': hashlib.sha256(raw).hexdigest()}
    run = {
        'schema_version': 1,
        **references,
        'protocol': {
            'id': 'synthetic_discrete_retention_v1',
            'observation_method': method,
            'allowed_target_origins': ['synthetic'],
            'cohorts': ['maximal', 'common'],
            'bindings': {
                'calc_ptf_beniaich2023_slr1': {'clay': 'clay'},
                'calc_ptf_beniaich2023_slr3': {'sand': 'sand'},
            },
        },
        'bootstrap': {
            'method': 'cluster_percentile_linear_v1',
            'seed': 20261025,
            'minimum_groups': 2,
            'grouping': 'profile',
            'missing_profiles': 'reject',
            'confidence_level': 0.95,
            'n_resamples': 16,
        },
        'selection': selection,
        'learned_selection': {
            'method': 'nested_convex_pair_selection_v1',
            'fixed_selection': selection,
            'ensembles': [
                {
                    'method': 'constant_convex_pair_log_pressure_v1',
                    'id': 'pair',
                    'left_candidate_id': 'slr1',
                    'right_candidate_id': 'slr3',
                    'minimum_training_groups': 2,
                    'minimum_mean_squared_contrast': 1e-10,
                }
            ],
        },
    }
    path = directory / 'run.json'
    with path.open('xb') as stream:
        stream.write(canonical_json(run))
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    build(parser.parse_args().output)
