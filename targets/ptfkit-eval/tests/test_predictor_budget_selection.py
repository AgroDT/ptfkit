"""Independent contracts for predictor masking and common-cohort model choice."""

import copy
import math

import pytest
from evaluation.experiments.meta_v3_3.expanded_predictors import water_convert
from evaluation.experiments.meta_v3_3.select_predictor_budgets import (
    analyze_budget,
    leave_source_out,
    mask_context,
    mask_row,
    validate_forecasts,
)


def point(source: str, sample: str, pressure: float, model: str, error: float) -> dict:
    return {
        'basis': 'volumetric_water_content',
        'source_id': source,
        'sample_id': sample,
        'pressure_kpa': pressure,
        'observed': 0.0,
        'predicted': error,
        'function': model,
    }


def test_budget_masks_hidden_cells_properties_and_formula_caches_without_mutating_inputs():
    row = {
        'values': {
            'M': 30,
            'N': 20,
            'O': 30,
            'P': 50,
            'J': '10-20',
            'Q': 1.4,
            'R': 2,
            'S': 3.448,
            'I': 'B',
        },
        'value_cells': {c: [f'master!{c}2'] for c in 'MNOPJQRSI'},
        'formulas': {'R': '=S2/1.724'},
        'properties': {'particle_density': 2.65, 'porosity': 0.5},
        'psd_bins': {
            'cells': ['master!AA2', 'master!AB2'],
            'values': [10, 20],
            'original_values': [10, 20],
        },
    }
    original = copy.deepcopy(row)
    masked = mask_row(row, ('organic_carbon',), {'master!AB2'})
    assert masked['values'] == {
        'M': 30,
        'N': 20,
        'O': 30,
        'P': 50,
        'J': None,
        'Q': None,
        'R': None,
        'S': None,
        'I': None,
    }
    assert masked['properties'] == {}
    assert masked['psd_bins']['values'] == [10, None]
    assert masked['psd_bins']['original_values'] == [10, None]
    assert row == original
    row['formulas'] = {}
    assert mask_row(row, ('organic_carbon', 'bulk_density', 'depth'), set())['values']['R'] == 2
    context = {'datasets': [{'samples': [{'features': [{'id': 'texture', 'value': 'clay'}]}]}]}
    masked_context = mask_context(context)
    assert masked_context['datasets'][0]['samples'][0]['features'] == []
    assert context['datasets'][0]['samples'][0]['features']


def test_full_pool_comparison_cannot_be_won_by_zero_error_on_a_smaller_subset():
    ledger = [point('A', 'a', 1, '', 0), point('B', 'b', 1, '', 0)]
    forecasts = [
        point('A', 'a', 1, 'partial', 0),
        point('A', 'a', 1, 'complete', 1),
        point('B', 'b', 1, 'complete', 1),
    ]
    analysis = analyze_budget(forecasts, ledger)
    assert analysis['descriptive_choice']['model'] == 'complete'
    assert analysis['descriptive_choice']['sample_balanced_rmse'] == 1
    assert analysis['choice_scope'] == 'full_predictor_pool'
    assert analysis['own_support_ranking_diagnostic'][0]['model'] == 'partial'
    assert analysis['common_ranking'][0]['model'] == 'partial'


def test_water_basis_conversion_requires_density_inside_the_budget():
    row = {
        'values': {'Q': 1.4},
        'value_cells': {'Q': ['master!Q2']},
        'formulas': {},
        'properties': {},
    }
    hidden = mask_row(row, (), set())
    with pytest.raises(ValueError, match='requires observed same-record bulk density'):
        water_convert(0.28, 'volumetric_water_content', 'gravimetric_water_content', hidden)
    available = mask_row(row, ('bulk_density',), set())
    value, evidence = water_convert(
        0.28, 'volumetric_water_content', 'gravimetric_water_content', available
    )
    assert value == pytest.approx(0.2)
    assert evidence['sources'] == ['master!Q2']


def test_forecast_audit_rejects_hidden_inputs_even_if_masking_were_bypassed():
    forecast = point('A', 'a', 1, 'a', 0.3)
    forecast['predictor_evidence'] = {'bulk_density': {'value': 1.4}}
    with pytest.raises(ValueError, match='outside its predictor budget'):
        validate_forecasts([forecast], ())
    validate_forecasts([forecast], ('bulk_density',))
    forecast['predictor_evidence'] = {}
    forecast['water_basis_conversion'] = {'bulk_density_g_cm3': 1.4}
    with pytest.raises(ValueError, match='hidden bulk density'):
        validate_forecasts([forecast], ())


def test_specialized_horizon_and_fixed_pressure_candidates_are_diagnostics_only():
    ledger = [point('A', 'a', 1, '', 0), point('B', 'b', 1, '', 0)]
    forecasts = [
        {**p, 'function': name, 'predicted': error}
        for p in ledger
        for name, error in [
            ('calc_ptf_varallyai1982_chernozem_b', 0),
            ('family_lal1979_group_i_from_sand_WRC_mass', 0),
            ('general', 2),
        ]
    ]
    forecasts.extend(
        {**p, 'function': 'fixed', 'predicted': 0, 'adapter': 'native_spec_fixed_pressure_v1'}
        for p in ledger
    )
    analysis = analyze_budget(forecasts, ledger)
    assert analysis['descriptive_choice']['model'] == 'general'
    assert analysis['specialized_domain_diagnostic'][0]['sample_balanced_rmse'] == 0
    assert len(analysis['specialized_domain_diagnostic']) == 2
    assert analysis['fixed_pressure_diagnostic'][0]['sample_balanced_rmse'] == 0


def test_empty_common_intersection_has_no_invented_winner():
    ledger = [point('A', 'a', p, '', 0) for p in (1, 10, 100)]
    analysis = analyze_budget(
        [point('A', 'a', 1, 'left', 0), point('A', 'a', 10, 'right', 0)], ledger
    )
    assert analysis['status'] == 'no_all_candidate_common_points'
    assert analysis['descriptive_choice'] is None
    assert analysis['common_ranking'] == []


def test_common_comparison_excludes_different_points_from_the_error():
    ledger = [point('A', 'a', p, '', 0) for p in (1, 10, 100)]
    analysis = analyze_budget(
        [
            point('A', 'a', 1, 'a', 99),
            point('A', 'a', 10, 'a', 2),
            point('A', 'a', 10, 'b', 3),
            point('A', 'a', 100, 'b', 0),
        ],
        ledger,
    )
    assert analysis['status'] == 'common_points_only'
    assert analysis['descriptive_choice']['model'] == 'a'
    assert analysis['descriptive_choice']['sample_balanced_rmse'] == 2
    assert analysis['descriptive_choice']['n_predicted_points'] == 1
    assert analysis['descriptive_choice']['n_total_points'] == 1


def test_held_out_source_cannot_choose_its_own_best_model():
    # Model a wins on source A; model b wins on source B. Training selection
    # therefore deliberately incurs errors 3 and 2 on the opposite sources.
    ledger = [point('A', 'a', 1, '', 0), point('B', 'b', 1, '', 0)]
    indices = {
        name: {
            (p['basis'], p['source_id'], p['sample_id'], p['pressure_kpa']): {
                **p,
                'function': name,
                'predicted': error,
            }
            for p, error in zip(ledger, errors, strict=True)
        }
        for name, errors in [('a', (0, 3)), ('b', (2, 0))]
    }
    result = leave_source_out(indices, list(indices['a']), ledger)
    assert result['scores']['sample_balanced_rmse'] == pytest.approx(math.sqrt(6.5))
    assert result['selected_counts'] == {'a': 1, 'b': 1}
    assert {f['held_out_source']: f['selected'] for f in result['folds']} == {'A': 'b', 'B': 'a'}
