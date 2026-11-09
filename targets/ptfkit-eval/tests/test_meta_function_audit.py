"""Separate missing metadata, predictor discovery and conditional source gains."""

import runpy
from pathlib import Path


def test_missing_adapter_does_not_prove_impossibility_or_authorize_candidate_columns():
    audit = runpy.run_path(
        str(
            Path(__file__).resolve().parents[3]
            / 'evaluation/experiments/meta_v3_3/function_audit.py'
        )
    )['audit']
    functions = [
        {
            'id': 'water',
            'source': 'paper',
            'prediction_target': 'water',
            'manifest_eligible': False,
            'inputs': [
                {
                    'name': 'sand',
                    'measurement': None,
                    'unit': '%',
                    'description': 'Measured dry-mass sand fraction.',
                }
            ],
            'outputs': [{'quantity': 'volumetric_water_content'}],
        },
        {
            'id': 'conductivity',
            'source': 'paper',
            'prediction_target': 'conductivity',
            'manifest_eligible': False,
            'inputs': [{'name': 'sand', 'measurement': None, 'unit': '%'}],
            'outputs': [{'quantity': 'saturated_hydraulic_conductivity'}],
        },
        {
            'id': 'climate',
            'source': 'paper',
            'prediction_target': 'water',
            'manifest_eligible': False,
            'inputs': [{'name': 'precipitation', 'measurement': None, 'unit': 'mm'}],
            'outputs': [{'quantity': 'volumetric_water_content'}],
        },
    ]
    rows = [
        {
            'function': f['id'],
            'master_key': 'master!2',
            'source_id': source,
            'status': 'blocked',
            'scientific_status': 'unresolved',
            'target': 'volumetric_water_content',
            'observation_count': 3,
            'reasons': ['unresolved_measurement_contract'],
        }
        for source in ('populated', 'missing_value')
        for f in functions
    ]
    rows = [
        {**r, 'master_key': 'master!3'} if r['source_id'] == 'missing_value' else r for r in rows
    ]
    result = audit(
        {'functions': functions},
        rows,
        {
            'worksheets': [
                {'id': 'samples_master', 'columns': [{'role': 'sand_fraction', 'column': 'P'}]}
            ]
        },
        {},
        {'master!2': {'P': 20}, 'master!3': {'P': None}},
    )
    assert result['counts']['real_data_scored'] == 0
    assert result['counts']['proven_impossible_on_meta'] == 0
    assert result['counts']['with_not_inventoried_predictors'] == 1
    water, conductivity, climate = result['functions']
    assert water['predictor_definitions'][0]['binding_authorized'] is False
    assert water['predictor_definitions'][0]['description'] == 'Measured dry-mass sand fraction.'
    assert water['implementation_blockers'] == [
        'public_measurement_contract',
        'target_adapter_or_binding',
    ]
    assert water['scientific_blockers'] == ['source_specific_input_and_target_evidence']
    assert climate['meta_impossibility'] == 'not_established'
    assert conductivity['not_inventoried_predictors'] == []
    # A water observation cannot support conductivity; missing raw cells cannot
    # support any candidate. An absent adapter alone must not remove water.
    gains = {r['source_id']: r for r in result['source_impacts']}
    assert gains['populated']['new_functions'] == ['water']
    assert gains['populated']['new_scoring_combinations_upper_bound'] == 1
    assert gains['missing_value']['new_functions_upper_bound'] == 0
    # A scientifically eligible unexecuted function must be classified as an
    # implementation gap, rather than counted as either scored or scientific.
    ready = [
        {**r, 'scientific_status': 'eligible', 'reasons': ['missing_input_binding']}
        if r['function'] == 'water'
        else r
        for r in rows
    ]
    after = audit(
        {'functions': functions},
        ready,
        {
            'worksheets': [
                {'id': 'samples_master', 'columns': [{'role': 'sand_fraction', 'column': 'P'}]}
            ]
        },
        {},
    )
    assert after['counts']['implementation_only_blocked'] == 1
    assert after['counts']['scientifically_blocked'] == 2
    assert after['counts']['real_data_scored'] == 0
    assert after['functions'][0]['current_eligible_samples'] == 2
    assert after['functions'][0]['real_data_scored_samples'] == 0
