"""Independent synthetic records for the public run contract."""

import hashlib
import json
from pathlib import Path


HALF_WETNESS_KPA = 3.5 * 2**4.05 * 0.0980665


def dataset_document() -> dict[str, object]:
    return {
        'schema_version': 1,
        'dataset_id': 'synthetic_sand',
        'kind': 'synthetic',
        'target': {
            'quantity': 'volumetric_water_content',
            'unit': 'volume_fraction',
            'material_basis': 'mineral_soil',
            'denominator_basis': 'bulk_volume',
        },
        'method': 'synthetic_pressure_control',
        'samples': [
            {
                'source_id': source,
                'sample_id': 'one',
                'profile_id': 'profile_one',
                'features': [
                    {
                        'id': 'texture',
                        'kind': 'categorical',
                        'value': 'sand',
                        'review_status': 'confirmed',
                        'origin': 'synthetic',
                        'category_system': 'clapp1978.UsdaTextureClass',
                        'source_cells': [f'{source}!A1'],
                    }
                ],
            }
            for source in ('a', 'b', 'without_target')
        ],
        'observations': [
            {
                'id': f'{source}_{index}',
                'source_id': source,
                'sample_id': 'one',
                'suction_kpa': pressure,
                'value': value,
                'origin': 'synthetic',
                'review_status': 'confirmed',
                'quality_flags': [],
                'source_cells': [f'{source}!B{index + 1}', f'{source}!C{index + 1}'],
            }
            for source in ('a', 'b')
            for index, (pressure, value) in enumerate(((0, 0.3), (HALF_WETNESS_KPA, 0.2)))
        ],
    }


def evaluation_document() -> dict[str, object]:
    return {
        'schema_version': 1,
        'ptfkit_manifest_schema_version': 1,
        'candidates': [
            {
                'id': name,
                'kind': 'function_curve',
                'axis': {
                    'quantity': 'matric_potential',
                    'unit': 'kilopascal',
                    'convention': 'magnitude',
                    'transform': 'linear',
                },
                'target': {
                    'quantity': 'volumetric_water_content',
                    'unit': 'volume_fraction',
                    'material_basis': 'mineral_soil',
                    'denominator_basis': 'bulk_volume',
                },
                'function': 'calc_ptf_clapp1978',
                'prediction': {'kind': 'model_adapter', 'id': 'clapp1978_h_theta'},
            }
            for name in ('sand_a', 'sand_b')
        ],
    }


def write_run_fixture(
    directory: Path,
    *,
    dataset: dict[str, object] | None = None,
    evaluation: dict[str, object] | None = None,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    references = {}
    for name, document in (
        ('dataset', dataset_document() if dataset is None else dataset),
        ('evaluation_plan', evaluation_document() if evaluation is None else evaluation),
    ):
        contents = (json.dumps(document, sort_keys=True, indent=2) + '\n').encode('utf-8')
        filename = f'{name}.json'
        (directory / filename).write_bytes(contents)
        references[name] = {'path': filename, 'sha256': hashlib.sha256(contents).hexdigest()}
    run = {
        'schema_version': 1,
        **references,
        'protocol': {
            'id': 'synthetic_retention_v1',
            'observation_method': 'synthetic_pressure_control',
            'allowed_target_origins': ['synthetic'],
            'cohorts': ['maximal', 'common'],
            'bindings': {'calc_ptf_clapp1978': {'soil_texture': 'texture'}},
        },
        'bootstrap': {
            'method': 'cluster_percentile_linear_v1',
            'seed': 7123,
            'minimum_groups': 2,
            'grouping': 'source',
            'missing_profiles': 'reject',
            'confidence_level': 0.95,
            'n_resamples': 16,
        },
    }
    path = directory / 'run.json'
    path.write_text(json.dumps(run, indent=2) + '\n', encoding='utf-8')
    return path
