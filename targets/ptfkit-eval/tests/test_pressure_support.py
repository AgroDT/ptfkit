import json
import math
import runpy
from pathlib import Path

from _run_fixtures import dataset_document
from ptfkit import get_manifest

from ptfkit_eval import load_retention_dataset


def test_pressure_audit_preserves_exact_support_and_unreported_saturation_conditions():
    root = Path(__file__).resolve().parents[3]
    count = runpy.run_path(
        str(root / 'evaluation/experiments/catalog_coverage/pressure_support.py')
    )['count_pressure_support']
    document = json.loads(json.dumps(dataset_document()))
    document.update(
        schema_version=2,
        target={
            'quantity': 'gravimetric_water_content',
            'unit': 'mass_fraction',
            'material_basis': 'unspecified',
            'denominator_basis': 'dry_soil_mass',
        },
    )
    for point, pressure in zip(
        document['observations'], [33, math.nextafter(33, 0), 0, 1500], strict=True
    ):
        point['suction_kpa'] = pressure
    report = count(load_retention_dataset(document), get_manifest())
    outputs = {
        item['output']: item
        for item in report['outputs']
        if item['function'] == 'calc_ptf_beniaich2023_slr1'
    }
    assert outputs['water_field_capacity']['matching_observation_count'] == 1
    assert outputs['water_wilting_point']['matching_observation_count'] == 1
    assert outputs['water_saturation']['suction_kpa'] is None
    assert outputs['water_saturation']['matching_observation_count'] is None
    assert outputs['water_saturation']['status'] == 'no_supported_fixed_pressure_condition'
