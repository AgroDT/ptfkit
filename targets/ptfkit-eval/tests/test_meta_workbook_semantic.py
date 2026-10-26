"""Protect E5 physical quantities, exact identity, units and measured support."""

import importlib
import json
import math
from datetime import datetime
from pathlib import Path
from types import ModuleType

import pytest
from openpyxl import Workbook


@pytest.fixture
def semantic(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3]))
    return importlib.import_module('evaluation.experiments.meta_v3_3.workbook_semantic')


def workbook() -> Workbook:
    book = Workbook()
    for i in range(1, 7):
        book.create_sheet(str(i))
    return book


def test_ksat_typo_and_velocity_conversions_are_e5_only(semantic: ModuleType):
    book = workbook()
    thesis = book.worksheets[6]
    for row, value in ((33, 0.864), (42, 0.06), (87, 86.4)):
        thesis[f'A{row}'], thesis[f'C{row}'], thesis[f'AB{row}'] = f'core{row}', 'paper', value
    rows = semantic.workbook_rows(book)
    by_row = {r['row']: r['properties']['ksat'] for r in rows}
    # Independent SI arithmetic: 0.864 m/day and 86.4 cm/day both equal 1e-5 m/s.
    assert by_row[33].value == pytest.approx(0.00001)
    assert by_row[87].value == pytest.approx(0.00001)
    assert by_row[42].value == pytest.approx(0.00001)
    details = dict(by_row[42].details)
    assert details['original_unit_label'] == 'cm/smin'
    assert details['interpreted_unit'] == 'cm/min'
    assert details['original_value'] == 0.06
    assert semantic.conductivity_factor('cm/smin') is None


def test_workbook_scales_density_and_datetime_rejection(semantic: ModuleType):
    book = workbook()
    sheet = book.worksheets[0]
    for row in (2, 3):
        sheet[f'A{row}'], sheet[f'C{row}'] = f'core{row}', 'paper'
    sheet['U2'], sheet['U3'] = 0.45, 45
    sheet['V2'], sheet['V3'] = 2.7, datetime(1900, 1, 2)  # noqa: DTZ001 - Excel stores naive dates.
    sheet['T2'] = 6.5
    rows = semantic.workbook_rows(book)
    assert [r['properties']['porosity'].value for r in rows] == [0.45, 0.45]
    assert rows[0]['properties']['particle_density'].value == 2.7
    assert 'particle_density' not in rows[1]['properties']
    assert dict(rows[0]['properties']['ph'].details)['method_contract_approximate'] is True


@pytest.mark.parametrize(
    ('theta', 'expected'), [(0.4, 10), (0.3, 100), (0.2, 1000), (0.5, None), (0.1, None)]
)
def test_inverse_uses_log_pressure_and_never_extrapolates(
    semantic: ModuleType, theta: float, expected: float | None
):
    result = semantic.inverse_wrc([(10, 0.4), (1000, 0.2)], theta)
    if expected is None:
        assert result is None
    else:
        assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    'curve',
    [
        [(10, 0.2), (100, 0.4)],
        [(10, 0.4), (10, 0.2)],
        [(10, 0.3), (100, 0.3)],
        [(0, 0.4), (10, 0.2)],
    ],
)
def test_inverse_rejects_ambiguous_or_nonlog_support(semantic: ModuleType, curve: list):
    assert semantic.inverse_wrc(curve, 0.3) is None


def test_same_key_cannot_override_conflicting_horizon(semantic: ModuleType):
    row = {'source_id': 'A', 'sample_id': 'core1', 'values': {'I': 'Ap', 'J': '0-20'}}
    assert semantic.compatible(row, {**row, 'values': {'I': 'Ap', 'J': '0-20 cm'}})
    assert not semantic.compatible(row, {**row, 'sample_id': 'core2'})
    assert not semantic.compatible(row, {**row, 'values': {'I': 'B', 'J': '20-40'}})


def test_public_execution_uses_non_wrc_ksat_and_plasticity_rows(semantic: ModuleType):
    book = workbook()
    thesis = book.worksheets[6]
    for row in (5, 42):
        thesis[f'A{row}'], thesis[f'C{row}'] = f'core{row}', 'paper'
    thesis['AF5'], thesis['AG5'] = 20, 35
    thesis['CW5'] = 25  # Explicit <1 micrometre clay, approximated to the requested <2.
    thesis['AB42'], thesis['P42'], thesis['T42'], thesis['U42'] = 0.06, 30, 1.5, 2
    root = Path(__file__).resolve().parents[3]
    catalog = semantic.contracts.load_catalog(root)
    ids = {
        'calc_ptf_ferrerjulia2004_general_sand',
        'calc_ptf_lal1979_group_i_lower_plastic_limit_from_clay',
        'calc_ptf_lal1979_group_i_plasticity_index_from_clay',
    }
    functions = [f for f in catalog if f['id'] in ids]
    assert len(functions) == 3
    context = {
        'catalog': functions,
        'datasets': [],
        'support': {},
        'manifest': {},
        'old_registration': json.loads(
            (root / 'evaluation/experiments/meta_v3_3/exploratory-policies.json').read_bytes()
        ),
    }
    records, points = semantic.evaluate(context, semantic.workbook_rows(book))
    assert {p['function'] for p in points} == ids
    ksat = next(p for p in points if p['target']['kind'] == 'ksat')
    assert ksat['observed'] == pytest.approx(0.00001)
    # Ferrer Julia's documented sand regression, with 70% derived >10 um sand proxy.
    assert ksat['predicted'] == pytest.approx(0.920 * math.exp(0.0491 * 70) / 3600000)
    assert ksat['predictor_evidence']['sand']['sources'] == ['6!P42']
    index = next(p for p in points if p['target']['field'] == 'plasticity_index')
    assert index['observed'] == 15
    assert index['predicted'] == pytest.approx(5.23)  # Lal Table IX: 0.11 * 25 + 2.48.
    assert index['predictor_evidence']['clay']['sources'] == ['6!CW5']
    assert all(r['status'] == 'executed' or r['reasons'] for r in records)


def test_physical_non_equivalents_have_no_e5_targets(semantic: ModuleType):
    context = {'support': {}}
    base = {'id': 'test', 'inputs': [], 'scalar_output': True, 'fields': []}
    for name, quantity in (
        ('infiltration_rate', 'infiltration_rate'),
        ('moisture_equivalent', 'gravimetric_water_content'),
        ('osmotic_potential', 'osmotic_potential'),
    ):
        function = {
            **base,
            'fields': [{'name': name, 'quantity': quantity, 'unit': 'mass_fraction'}],
        }
        assert semantic.target_list(function, context) == []


def test_semantic_predictors_use_density_ratio_but_never_default_density(semantic: ModuleType):
    book = workbook()
    sheet = book.worksheets[0]
    sheet['A2'], sheet['C2'], sheet['Q2'], sheet['V2'], sheet['T2'] = 'core', 'paper', 1.3, 2.6, 6.5
    row = semantic.workbook_rows(book)[0]
    root = Path(__file__).resolve().parents[3]
    context = {
        'old_registration': json.loads(
            (root / 'evaluation/experiments/meta_v3_3/exploratory-policies.json').read_bytes()
        )
    }
    function = {
        'id': 'test',
        'inputs': [
            {'name': 'total_porosity', 'unit': 'cm^3/cm^3'},
            {'name': 'particle_density', 'unit': 'g/cm^3'},
            {'name': 'ph', 'unit': 'dimensionless'},
            {'name': 'effective_porosity', 'unit': 'cm^3/cm^3'},
        ],
    }
    values, proofs, reasons = semantic.semantic_inputs(
        function, {'features': []}, row, context, {}, set()
    )
    assert values == {'total_porosity': 0.5, 'particle_density': 2.6, 'ph': 6.5}
    assert reasons == ['missing_predictor:effective_porosity']
    assert proofs['total_porosity']['sources'] == ['Sheet!Q2', 'Sheet!V2']
    row['properties'].pop('particle_density')
    values, _, reasons = semantic.semantic_inputs(
        function, {'features': []}, row, context, {}, set()
    )
    assert 'total_porosity' not in values
    assert 'missing_predictor:particle_density' in reasons


def test_porosity_target_requires_explicit_output_equivalence(semantic: ModuleType):
    base = {'id': 'test', 'inputs': [], 'scalar_output': True}
    field = {
        'name': 'theta_s',
        'quantity': 'volumetric_water_content',
        'unit': 'volume_fraction',
        'description': 'Saturated volumetric water content.',
    }
    context = {'support': {}}
    assert not any(
        t['kind'] == 'porosity_parameter'
        for t in semantic.target_list({**base, 'fields': [field]}, context)
    )
    field['description'] = 'Saturated volumetric soil water content represented by soil porosity.'
    assert any(
        t['kind'] == 'porosity_parameter'
        for t in semantic.target_list({**base, 'fields': [field]}, context)
    )


def test_errors_balance_samples_and_keep_porosity_pool_separate(semantic: ModuleType):
    target = {'kind': 'fixed_pressure', 'field': 'theta_s', 'quantity': 'volumetric_water_content'}
    base = {
        'function': 'test',
        'scenario': 'master',
        'source_id': 'paper',
        'observed': 0,
        'target': target,
    }
    points = [
        {**base, 'sample_id': 'a', 'predicted': 1},
        {**base, 'sample_id': 'a', 'predicted': 3},
        {**base, 'sample_id': 'b', 'predicted': 0},
        {
            **base,
            'sample_id': 'a',
            'predicted': 20,
            'target': {**target, 'kind': 'porosity_parameter'},
        },
    ]
    result = semantic.pool_metrics(points)
    assert len(result) == 2
    curve = next(r for r in result if r['target_kind'] == 'fixed_pressure')
    assert curve['rmse'] == pytest.approx(math.sqrt(2.5))
    assert curve['mae'] == 1
    assert curve['bias'] == 1
    assert curve['samples'] == 2


def test_psd_closure_cites_observed_parents_and_original_cutoffs(semantic: ModuleType):
    book = workbook()
    sheet = book.worksheets[6]
    sheet['A5'], sheet['C5'] = 'core', 'paper'
    # Five observed bins total 99%; the missing <1 um fraction is the 1% remainder.
    for column in ('CR', 'CS', 'CT', 'CU', 'CV'):
        sheet[f'{column}5'] = 19.8
    row = semantic.workbook_rows(book)[0]
    assert row['values']['N'] == pytest.approx(1)
    assert row['value_cells']['N'] == ('6!CR5', '6!CS5', '6!CT5', '6!CU5', '6!CV5')
    assert row['psd_bins']['original_values'][-1] is None
    assert row['clay_upper_um'] == 1


def test_specific_water_volume_uses_explicit_water_density(semantic: ModuleType):
    root = Path(__file__).resolve().parents[3]
    function = next(
        f
        for f in semantic.contracts.load_catalog(root)
        if f['id'] == 'calc_ptf_bruand1994_bulk_volume_water_retention'
    )
    target = {
        'field': 'water_content_30_kpa',
        'unit': 'cubic_centimeter_per_gram',
        'quantity': 'gravimetric_water_content',
        'kind': 'fixed_pressure',
    }
    context = {'old_registration': {'water_density_g_cm3': 0.998}}
    # Independent decimal reference in the source specification at bulk volume 0.695.
    assert semantic.prediction(function, target, {'bulk_volume': 0.695}, context) == pytest.approx(
        0.26079237
    )


def test_consumption_counts_original_observations_once_across_predictions(semantic: ModuleType):
    point = {
        'function': 'a',
        'source_id': 'paper',
        'sample_id': 'core',
        'target_evidence': {'parents': [{'details': {'observation_id': 'wrc-1'}}]},
        'predictor_evidence': {
            'water': {
                'details': {
                    'parents': [
                        {'details': {'observation_id': 'wrc-1'}},
                        {'details': {'observation_id': 'wrc-2'}},
                    ]
                }
            }
        },
    }
    result = semantic.consumption([point, point, {**point, 'function': 'b'}])
    assert result == {
        'wrc_target_observations': 1,
        'wrc_predictor_observations': 2,
        'wrc_observations_union': 2,
        'samples': 1,
        'function_sample_pairs': 2,
    }


def test_inverse_route_records_a_blocker_for_nonmonotone_measured_curve(semantic: ModuleType):
    book = workbook()
    book.worksheets[0]['A2'], book.worksheets[0]['C2'] = 'core', 'paper'
    function = {
        'id': 'test',
        'inputs': [{'name': 'theta', 'unit': 'm^3/m^3'}],
        'fields': [{'name': 'tension', 'quantity': 'matric_potential', 'unit': 'kilopascal'}],
    }
    sample = {'source_id': 'paper', 'sample_id': 'core', 'features': []}
    dataset = {
        'target': {'quantity': 'volumetric_water_content'},
        'samples': [sample],
        'observations': [
            {
                'source_id': 'paper',
                'sample_id': 'core',
                'suction_kpa': p,
                'value': w,
                'id': f'obs-{p}',
                'source_cells': [f'Sheet!A{p}'],
                'origin': 'measured',
                'review_status': 'confirmed',
                'quality_flags': [],
            }
            for p, w in [(10, 0.2), (100, 0.4)]
        ],
    }
    root = Path(__file__).resolve().parents[3]
    context = {
        'catalog': [function],
        'datasets': [dataset],
        'support': {},
        'old_registration': json.loads(
            (root / 'evaluation/experiments/meta_v3_3/exploratory-policies.json').read_bytes()
        ),
    }
    records, points = semantic.evaluate(context, semantic.workbook_rows(book))
    assert points == []
    assert len(records) == 1
    assert records[0]['status'] == 'blocked'
    assert records[0]['reasons'] == ['invalid_or_ambiguous_inverse_wrc']


def test_continuous_outputs_use_observed_pressures_and_scalar_targets_stay_fixed(
    semantic: ModuleType,
):
    sample = {'source_id': 'paper', 'sample_id': 'core'}
    dataset = {
        'target': {'quantity': 'volumetric_water_content'},
        'observations': [
            {
                **sample,
                'suction_kpa': p,
                'value': 0.3,
                'id': str(p),
                'source_cells': [str(p)],
                'origin': 'measured',
                'review_status': 'confirmed',
                'quality_flags': [],
            }
            for p in (7, 19, 71)
        ],
    }
    scalar = {
        'kind': 'fixed_pressure',
        'field': 'theta_33',
        'pressure_kpa': 33,
        'adapter': 'native_spec_fixed_pressure_v1',
    }
    curve = {'kind': 'fixed_pressure', 'pressure_kpa': 33, 'adapter': 'existing_model_adapter_v1'}
    selected = semantic.measured_targets(
        [scalar, curve, {**curve, 'pressure_kpa': 100}], [(dataset, sample)], ('paper', 'core')
    )
    assert [t['pressure_kpa'] for t, _ in selected if 'field' in t] == [33]
    assert sorted(t['pressure_kpa'] for t, _ in selected if 'field' not in t) == [
        7,
        19,
        33,
        71,
        100,
    ]
