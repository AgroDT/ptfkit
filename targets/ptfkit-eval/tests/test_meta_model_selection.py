"""Independent oracles for observed-coordinate selection and grouped evaluation."""

import importlib
import math
from pathlib import Path
from types import ModuleType

import pytest
from openpyxl import Workbook
from ptfkit import get_manifest


@pytest.fixture
def selection(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3]))
    return importlib.import_module('evaluation.experiments.meta_v3_3.model_selection')


def point(fid: str, sample: str, pressure: float, prediction: float, observed: float = 0):
    return {
        'id': f'{sample}:{pressure}',
        'source_id': 'source',
        'sample_id': sample,
        'profile_id': None,
        'horizon': None,
        'function': fid,
        'pressure_kpa': pressure,
        'predicted': prediction,
        'observed': observed,
        'basis': 'volumetric_water_content',
    }


def test_equal_sample_weighting_differs_from_point_weighting(selection: ModuleType):
    # One sample has error 2; another has three zero errors. MSE=(4+0)/2.
    result = selection.metrics(
        [point('a', 'one', 1, 2), *[point('a', 'two', p, 0) for p in (1, 2, 3)]]
    )
    assert result['rmse'] == pytest.approx(math.sqrt(2))
    assert result['mae'] == result['bias'] == 1
    assert result['median_absolute_error'] == 0
    assert result['samples'] == 2
    assert result['observations'] == 4


def test_log_scoring_factor_boundaries_and_nonpositive_rejection(selection: ModuleType):
    result = selection.metrics(
        [point('a', 'one', 1, 2, 1), point('a', 'two', 1, 0.1, 1)], ksat=True
    )
    assert result['rmse'] == pytest.approx(math.sqrt((math.log10(2) ** 2 + 1) / 2))
    assert result['bias'] == pytest.approx((math.log10(2) - 1) / 2)
    assert result['median_ratio'] == pytest.approx(1.05)
    assert result['factor_2'] == result['factor_5'] == 0.5
    assert result['factor_10'] == 1
    with pytest.raises(ValueError, match='positive'):
        selection.metrics([point('a', 'one', 1, 0, 1)], ksat=True)


def test_common_cohort_requires_multiple_shared_pressures_per_sample(selection: ModuleType):
    a = [point('a', 'shared', p, 0.1) for p in (1, 3, 7)]
    b = [point('b', 'shared', p, 0.2) for p in (1, 3)]
    # Each has two pressures for lonely, but just one pressure in common.
    a.extend(point('a', 'lonely', p, 100) for p in (1, 2))
    b.extend(point('b', 'lonely', p, 0) for p in (2, 3))
    cohorts = selection.common_cohorts({'a': {p['id']: p for p in a}, 'b': {p['id']: p for p in b}})
    assert len(cohorts) == 1
    assert cohorts[0]['keys'] == ['shared:1', 'shared:3']
    assert cohorts[0]['samples'] == 1
    assert cohorts[0]['observations'] == 2
    replicates = [point('a', 'replicate', 10, 0.1), point('a', 'replicate', 10, 0.2)]
    for number, record in enumerate(replicates):
        record['id'] = str(number)
    index = {p['id']: p for p in replicates}
    assert not selection.eligible_keys(set(index), index, ksat=False)


def test_conflicting_observations_fail_common_comparison(selection: ModuleType):
    a = [point('a', 'one', p, 0) for p in (1, 2)]
    b = [point('b', 'one', p, 0, 0.1) for p in (1, 2)]
    with pytest.raises(ValueError, match='observations disagree'):
        selection.common_cohorts({'a': {p['id']: p for p in a}, 'b': {p['id']: p for p in b}})


def test_ranking_and_ensemble_ignore_unmatched_large_errors(selection: ModuleType):
    records = [
        point(fid, sample, pressure, prediction)
        for fid, prediction in [('a', 1), ('b', 2)]
        for sample in ('one', 'two')
        for pressure in (10, 100)
    ]
    records.extend(point('a', 'unmatched', pressure, 1000) for pressure in (10, 100))
    result = selection.analyze(records)
    assert result['primary']['samples'] == 2
    assert result['primary']['observations'] == 4
    assert [(r['function'], r['rmse']) for r in result['primary']['ranking']] == [
        ('a', 1),
        ('b', 2),
    ]
    assert result['ensembles']['mean']['rmse'] == 1.5
    assert result['ensembles']['mean']['samples'] == 2
    assert not result['ensemble_conclusion']['mean']['meaningful_and_robust']


def test_reduced_membership_uses_training_groups_only(selection: ModuleType):
    # Training chooses a,b. c is perfect on the held-out source but poor on training.
    indices = {}
    for fid, errors in {'a': [0.1, 0.2, 3, 3], 'b': [0.2, 0.1, -3, -3], 'c': [4, 4, 0, 0]}.items():
        records = [point(fid, 'train' if j < 2 else 'test', j, e) for j, e in enumerate(errors)]
        for record in records:
            record['source_id'] = record['sample_id']
        indices[fid] = {p['id']: p for p in records}
    result = selection.robustness(indices, ['a', 'b', 'c'], list(indices['a']))
    held = next(f for f in result['folds'] if f['omitted_group'] == 'test')
    assert held['reduced_members'] == ['a', 'b']
    assert held['held_out_ensembles']['reduced']['rmse'] == 0
    assert held['training_best_atomic'] == 'a'
    assert held['held_out_training_best_atomic']['rmse'] == 3


def test_scalar_theta33_is_not_full_curve_candidate(selection: ModuleType):
    function = {
        'id': 'scalar',
        'fields': [
            {
                'name': 'theta33',
                'quantity': 'volumetric_water_content',
                'unit': 'volume_fraction',
                'description': 'Water content at 33 kPa.',
            }
        ],
        'inputs': [],
        'scalar_output': True,
    }
    water, conductivity = selection.candidate_targets(function, {'support': {}})
    assert water == conductivity == []


def test_discrete_curve_interpolates_predictions_without_extrapolation(
    selection: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
):
    targets = [{'pressure_kpa': p, 'value': v} for p, v in [(10, 0.6), (100, 0.4), (1000, 0.2)]]
    monkeypatch.setattr(
        selection.semantic, 'prediction', lambda _f, target, _v, _c: target['value']
    )
    assert selection.discrete_prediction({}, targets, math.sqrt(1000), {}, {}) == pytest.approx(0.5)
    with pytest.raises(ValueError, match='outside'):
        selection.discrete_prediction({}, targets, 5, {}, {})


def test_logistic_curve_evaluates_physical_zero_suction_limit(
    selection: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
):
    function = {
        'fields': [
            {'name': 's', 'quantity': 'volumetric_water_content', 'unit': 'volume_fraction'},
            {'name': 'm', 'quantity': 'varallyai_m'},
            {'name': 'pf', 'quantity': 'varallyai_pf_star'},
        ]
    }
    monkeypatch.setattr(
        selection.contracts, 'native_outputs', lambda *_: {'s': 0.45, 'm': 0.3, 'pf': 2}
    )
    result = selection.contracts.predicted(
        function,
        {
            'adapter': 'logistic_pressure_scale_v1',
            'pressure_kpa': 0,
        },
        {},
        get_manifest(),
    )
    assert result == 0.45


@pytest.mark.usefixtures('selection')
def test_explicit_thesis_axes_keep_basis_and_reject_unproven_replicates():
    audit = importlib.import_module('evaluation.experiments.meta_v3_3.selection_audit')
    book = Workbook()
    for number in range(6):
        book.create_sheet(str(number))
    sheet = book.worksheets[6]
    sheet['C5'], sheet['A5'] = 'source', 'sample'
    sheet['AJ4'], sheet['AK4'], sheet['AL4'] = 0.1, 0.1, 1
    sheet['AJ5'], sheet['AK5'], sheet['AL5'] = 0.4, 0.35, 0.3
    sheet['C3'], sheet['A3'] = 'other', 'mass'
    sheet['AJ2'], sheet['AJ3'] = 2, 25
    context = {'datasets': []}
    points, decisions = audit.thesis_wrc(context, book)
    assert len(points) == 2
    volume = next(p for p in points if p['sample_id'] == 'sample')
    mass = next(p for p in points if p['sample_id'] == 'mass')
    assert volume['pressure_kpa'] == pytest.approx(9.80665)
    assert volume['observed'] == 0.3
    assert volume['basis'] == 'volumetric_water_content'
    assert mass['pressure_kpa'] == pytest.approx(9.80665)
    assert mass['observed'] == 0.25
    assert mass['basis'] == 'gravimetric_water_content'
    assert (
        sum(
            d['status'] == 'repeated_head_without_independent_measurement_evidence'
            for d in decisions
        )
        == 2
    )
