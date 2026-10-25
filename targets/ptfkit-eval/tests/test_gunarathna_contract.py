"""Keep undisturbed retention specimens distinct from prepared texture aliquots."""

import pytest
from ptfkit import get_manifest

from ptfkit_eval import PlanValidationError, load_evaluation_plan
from ptfkit_eval.documents import object_mapping, object_records


def test_all_gunarathna_contracts_preserve_source_specimens_and_pressure_conditions():
    functions = [
        f for f in object_records(get_manifest()['functions']) if f['source'] == 'gunarathna2019'
    ]
    assert len(functions) == 11
    for function in functions:
        pressure = int(str(function['id']).split('_vwc')[1].split('_')[0])
        output = object_mapping(object_records(function['outputs'])[0]['measurement'])
        assert output['basis'] == {'material': 'soil', 'denominator': 'bulk_volume'}
        assert output['conditions'] == (
            {
                'quantity': 'matric_potential',
                'value': pressure,
                'unit': 'kilopascal',
                'convention': 'magnitude',
            },
        )
        assert output['method'] == 'pressure_plate'
        for parameter in object_records(function['inputs']):
            descriptor = object_mapping(parameter['measurement'])
            if parameter['name'] == 'bulk_density':
                assert descriptor['basis'] == {'material': 'soil', 'denominator': 'bulk_volume'}
                assert descriptor['method'] == 'undisturbed_core_54_mm_diameter_60_mm_height'
            else:
                assert descriptor['basis'] == {'material': 'fine_earth', 'denominator': 'dry_mass'}


def test_fine_earth_target_cannot_be_substituted_for_undisturbed_bulk_retention():
    candidate = {
        'id': 'point',
        'kind': 'function_point',
        'axis': {
            'quantity': 'matric_potential',
            'unit': 'kilopascal',
            'convention': 'magnitude',
            'transform': 'linear',
        },
        'target': {
            'quantity': 'volumetric_water_content',
            'unit': 'volume_fraction',
            'material_basis': 'fine_earth',
            'denominator_basis': 'bulk_volume',
        },
        'function': 'calc_ptf_gunarathna2019_vwc33_set1',
        'prediction': {'kind': 'fixed_output', 'name': 'theta_33'},
    }
    with pytest.raises(PlanValidationError):
        load_evaluation_plan(
            {
                'schema_version': 1,
                'ptfkit_manifest_schema_version': 1,
                'candidates': [candidate],
            }
        )
