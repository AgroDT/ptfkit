"""Protect target-first atomic review without synthetic measured targets."""

import runpy
from pathlib import Path


def _campaign() -> dict:
    return runpy.run_path(
        str(
            Path(__file__).resolve().parents[3]
            / 'evaluation/experiments/meta_v3_3/atomic_campaign.py'
        )
    )


def test_target_coordinates_require_exact_pressure_and_matching_water_denominator():
    match = _campaign()['matching_observations']
    rows = [{'suction_kpa': p} for p in (31.01135021609024, 33, 33.000000001, 1520)]
    target = {'quantity': 'volumetric_water_content', 'kind': 'fixed_pressure', 'pressure_kpa': 33}
    assert match(target, rows, 'volumetric_water_content') == [{'suction_kpa': 33}]
    assert match(target, rows, 'gravimetric_water_content') == []
    assert match({**target, 'pressure_kpa': 1500}, rows, 'volumetric_water_content') == []
    # Operational field capacity cannot be fabricated from a theta33 point.
    assert (
        match(
            {'quantity': 'volumetric_water_content', 'kind': 'operational'},
            rows,
            'volumetric_water_content',
        )
        == []
    )


def test_available_target_and_populated_predictors_remain_independent_of_execution_permission():
    assess = _campaign()['assess']
    function = {
        'id': 'point',
        'source': 'test',
        'outputs': [{'name': 'theta', 'quantity': 'volumetric_water_content'}],
    }
    support = {
        'point': {
            'fixed_outputs': [
                {'measurement': {'quantity': 'volumetric_water_content'}, 'suction_kpa': 33}
            ]
        }
    }
    audit = {
        'functions': [
            {
                'function': 'point',
                'real_data_scored_samples': 0,
                'predictor_definitions': [{'name': 'sand', 'candidate_column': 'P'}],
            }
        ]
    }
    dataset = {
        'target': {'quantity': 'volumetric_water_content'},
        'observations': [
            {'source_id': 'measured', 'sample_id': 'same_local_id', 'suction_kpa': 33}
        ],
    }
    raw = {('different_source', 'same_local_id'): {'P': 40}}
    result = assess({'functions': [function]}, support, [dataset], audit, raw)
    decision = result['functions'][0]
    assert decision['target_status'] == 'measured_coordinates_available_protocol_review_required'
    assert decision['predictor_status'] == 'missing_predictors_for_available_targets'
    assert decision['source_opportunities'][0]['complete_candidate_predictor_rows'] == 0
    assert decision['execution_authorized'] is False
    # Even a correct source/sample match does not establish measurement method.
    raw['measured', 'same_local_id'] = {'P': 40}
    after = assess({'functions': [function]}, support, [dataset], audit, raw)
    assert after['functions'][0]['predictor_status'] == 'reviewed_unresolved'
    assert (
        after['functions'][0]['source_opportunities'][0]['complete_candidate_predictor_rows'] == 1
    )
    assert after['functions'][0]['execution_authorized'] is False
    assert after['counts']['scored_atomic'] == 0


def test_pidgeon_fc_and_oosterveld_continuous_retention_keep_distinct_target_contracts():
    targets = _campaign()['targets']
    pidgeon = {
        'id': 'calc_ptf_pidgeon1972_fc_sand',
        'source': 'pidgeon1972',
        'outputs': [{'quantity': 'gravimetric_water_content'}],
    }
    assert targets(pidgeon, {}) == [
        {'quantity': 'gravimetric_field_capacity', 'kind': 'operational'}
    ]
    oosterveld = {
        'id': 'calc_ptf_oosterveld1980_retention',
        'source': 'oosterveld1980',
        'outputs': [{'quantity': 'gravimetric_water_content'}],
    }
    assert targets(oosterveld, {}) == [
        {'quantity': 'gravimetric_water_content', 'kind': 'curve', 'pressure_range_kpa': [10, 1500]}
    ]
