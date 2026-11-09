"""Protect predictor membership from formula leakage and cross-record joins."""

from evaluation.experiments.meta_v3_3 import expanded_predictors as predictors
from evaluation.experiments.meta_v3_3 import workbook_semantic as semantic
from evaluation.experiments.meta_v3_3.predictor_subsets import (
    PROBE,
    partition,
    pool_members,
    reported_features,
)
from openpyxl import Workbook


def record(name: str, reported: dict, usable: dict) -> dict:
    return {
        'record_id': name,
        'reported': reported,
        'reported_canonical': reported,
        'e5_usable': usable,
        'row_status': 'unique_predictor_record',
    }


def test_reported_cells_exclude_formulas_and_preserve_clay_cutoff():
    values, formulas = Workbook(), Workbook()
    values.active.title = formulas.active.title = 'master'
    for column, value in {'N': 20, 'O': 30, 'P': 50, 'Q': 1.4, 'R': 0.5, 'S': 0.862}.items():
        values.active[f'{column}2'] = formulas.active[f'{column}2'] = value
    formulas.active['Q2'] = '=AVERAGE(Q3:Q4)'
    formulas.active['S2'] = '=R2*1.724'
    row = {
        'worksheet': 'master',
        'row': 2,
        'columns': {c: c for c in 'MNOPQRSTUV'},
        'clay_upper_um': 1,
    }
    features, canonical = reported_features(row, values, formulas)
    assert set(features) == {'clay_lt_1_um', 'silt_1_50_um', 'sand_50_2000_um', 'organic_carbon'}
    assert set(canonical) == {'clay', 'silt', 'sand', 'organic_carbon'}
    assert features['clay_lt_1_um']['source_cells'] == ['master!N2']
    changed, _ = reported_features({**row, 'clay_upper_um': 2}, values, formulas)
    assert 'clay_lt_2_um' in changed
    assert 'clay_lt_1_um' not in changed


def test_signature_depends_on_availability_and_cutoffs_not_predictor_values():
    a = record('a', {'clay_lt_1_um': 10}, {'clay': 10})
    b = record('b', {'clay_lt_1_um': 90}, {'clay': 90})
    c = record('c', {'clay_lt_2_um': 10}, {'clay': 10})
    groups = partition([a, b, c])
    assert len(groups) == 2
    assert a['subset_id'] == b['subset_id']
    assert a['subset_id'] != c['subset_id']
    assert sorted(len(g) for g in groups.values()) == [1, 2]


def test_pools_do_not_union_records_or_relabel_derived_inputs_as_reported():
    a = record('one', {'clay': 20}, {'clay': 20})
    b = record('two', {'sand': 50, 'silt': 30}, {'sand': 50, 'silt': 30})
    derived = record('derived', {'clay': 20, 'sand': 50}, {'clay': 20, 'sand': 50, 'silt': 30})
    complete = record(
        'complete',
        {'clay': 20, 'sand': 50, 'silt': 30, 'bulk_density': 1.4},
        {'clay': 20, 'sand': 50, 'silt': 30, 'bulk_density': 1.4},
    )
    required = ('sand', 'silt', 'clay')
    assert pool_members([a, b], required, 'e5_usable') == []
    assert [
        r['record_id'] for r in pool_members([a, b, derived, complete], required, 'reported')
    ] == ['complete']
    assert [
        r['record_id'] for r in pool_members([a, b, derived, complete], required, 'e5_usable')
    ] == ['derived', 'complete']


def test_availability_probe_keeps_observed_ph_and_porosity_with_canonical_units():
    row = {
        'worksheet': 'master',
        'row': 2,
        'clay_upper_um': 1,
        'columns': {c: c for c in 'MNOPQRSTUVJI'},
        'values': dict.fromkeys('MNOPQRSTUVJI'),
        'formulas': {},
        'value_cells': {c: (f'master!{c}2',) for c in 'MNOPQRSTUVJI'},
        'properties': {
            'ph': semantic.proof(6.5, 'pH', ('master!T2',)),
            'porosity': semantic.proof(0.4, 'porosity', ('master!U2',)),
        },
    }
    context = {
        'old_registration': {
            'scenarios': ['reported_boundary_proxy'],
            'organic_carbon_to_matter_factor': 1.724,
        }
    }
    values, _, _ = predictors.resolve(PROBE, {'features': []}, row, context)
    assert values['ph'] == 6.5
    assert values['porosity'] == 0.4
