"""Protect exact cohorts, target sensitivity and descriptive ensemble interpretation."""

import importlib
from pathlib import Path
from types import ModuleType

import pytest
import yaml


@pytest.fixture
def analysis(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[3]))
    return importlib.import_module('evaluation.experiments.meta_v3_3.comparative')


def point(
    function: str,
    sample: str,
    predicted: float,
    *,
    observed: float = 0,
    scenario: str = 'left',
    route: str = 'measured',
    tier: str = 'E2',
):
    return {
        'function': function,
        'sample_id': sample,
        'source_id': 's',
        'profile_id': None,
        'pressure_kpa': 33,
        'target_pool': 'water:33',
        'predicted': predicted,
        'observed': observed,
        'scenario': scenario,
        'route': route,
        'minimum_tier': tier,
    }


def test_common_cohort_excludes_unmatched_errors_and_scores_ensembles(analysis: ModuleType):
    points = [
        point('a', '1', -1),
        point('a', '2', -2),
        point('a', '3', -3),
        point('b', '1', 1),
        point('b', '2', 2),
        point('b', '3', 3),
        point('a', 'unmatched', 1000),
    ]
    result = analysis.analyze(points)[0]
    assert result['points'] == result['samples'] == 3
    assert result['profiles'] == 0
    assert result['samples_without_profile'] == 3
    rows = {r['function']: r for r in result['ranking']}
    assert rows['a']['metrics'] == pytest.approx(
        {
            'rmse': (14 / 3) ** 0.5,
            'mae': 2,
            'bias': -2,
            'median_absolute_error': 2,
        }
    )
    assert rows['a']['coverage'] == 1
    assert rows['b']['coverage'] == 0.75
    assert result['residual_correlations'][0]['correlation'] == pytest.approx(-1)
    best = result['best_atomic_vs_ensemble']
    assert best['ensemble']['metrics']['rmse'] == 0
    assert best['delta_rmse_ensemble_minus_atomic'] == pytest.approx(-((14 / 3) ** 0.5))


def test_empty_global_intersection_preserves_only_separate_pair_comparisons(analysis: ModuleType):
    result = analysis.analyze(
        [
            point('a', '1', 1),
            point('b', '1', 2),
            point('b', '2', 3),
            point('c', '2', 4),
        ]
    )[0]
    assert result['status'] == 'empty_common_cohort'
    assert 'ranking' not in result
    assert 'best_atomic_vs_ensemble' not in result
    pairs = {tuple(p['members']): p['comparison'] for p in result['pairwise_cohorts']}
    assert pairs['a', 'b']['cohort'] == [['s', '1', 33]]
    assert pairs['b', 'c']['cohort'] == [['s', '2', 33]]
    assert pairs['a', 'c']['status'] == 'empty_common_cohort'


def test_target_route_rank_reversal_allows_intentional_observation_differences(
    analysis: ModuleType,
):
    points = [
        point('a', '1', 0),
        point('b', '1', 2),
        point('a', '1', 0, observed=2, route='fit'),
        point('b', '1', 2, observed=2, route='fit'),
        point('a', 'unmatched', 1000),
    ]
    result = analysis.robustness(points, dimension='route')[0]
    assert result['common_points'] == 1
    assert result['rankings'] == {'fit': ['b', 'a'], 'measured': ['a', 'b']}
    assert result['rank_changes'] == {'a': -1, 'b': 1}
    assert result['changed_pair_orderings'] == [['a', 'b']]
    points[-2]['observed'] = 3
    with pytest.raises(ValueError, match='identical observed'):
        analysis.robustness(points, dimension='route')


def test_pareto_prefers_lower_tier_when_errors_are_practically_equal(analysis: ModuleType):
    result = analysis.analyze(
        [
            point('low', '1', 1, tier='E2'),
            point('high', '1', 0.995, tier='E4'),
        ]
    )[0]
    assert result['pareto'] == ['low']
    assert result['ranking'][0]['function'] == 'high'


def test_sample_weighting_differs_from_pointwise_median(analysis: ModuleType):
    points = [point('a', 'one', 4), point('a', 'many', 0), point('a', 'many', 0)]
    points[-1]['pressure_kpa'] = 1500
    assert analysis.describe(points) == pytest.approx(
        {
            'rmse': 8**0.5,
            'mae': 2,
            'bias': 2,
            'median_absolute_error': 0,
        }
    )


def test_catalog_delta_uses_previous_ids_and_ladder(analysis: ModuleType):
    rolling = importlib.import_module(analysis.__name__.rsplit('.', 1)[0] + '.rolling')
    previous = {
        'functions': [{'function': 'old'}, {'function': 'removed'}],
        'assumption_ladder': [{'evidence_ceiling': 'E4', 'functions_executable': 1}],
    }
    assert rolling.catalog_refresh([{'id': 'old'}, {'id': 'new'}], previous) == {
        'previous_count': 2,
        'current_count': 2,
        'newly_discovered_functions': ['new'],
        'removed_functions': ['removed'],
    }
    assert (
        rolling.ladder_delta([{'evidence_ceiling': 'E4', 'functions_executable': 3}], previous)[0][
            'delta_from_previous'
        ]
        == 2
    )


def test_public_wrapper_is_discovered_even_before_status_is_implemented(
    analysis: ModuleType, tmp_path: Path
):
    contracts = importlib.import_module(analysis.__name__.rsplit('.', 1)[0] + '.campaign_contracts')
    specs = tmp_path / 'specs/functions'
    wrappers = tmp_path / 'targets/ptfkit-py/src/ptfkit'
    specs.mkdir(parents=True)
    wrappers.mkdir(parents=True)
    functions = [
        {
            'name': name,
            'status': status,
            'inputs': [],
            'outputs': {'name': 'value', 'type': 'number', 'quantity': 'dry_bulk_density'},
        }
        for name, status in [
            ('calc_ptf_old', 'implemented'),
            ('calc_ptf_new', 'ready-for-implementation'),
            ('calc_ptf_unreleased', 'blocked'),
        ]
    ]
    (specs / 'sample.yaml').write_text(yaml.safe_dump({'functions': functions}), encoding='utf-8')
    (wrappers / 'sample.py').write_text(
        'def calc_ptf_old(): pass\ndef calc_ptf_new(): pass\n', encoding='utf-8'
    )
    catalog = contracts.load_catalog(tmp_path)
    assert {f['id'] for f in catalog} == {'calc_ptf_old', 'calc_ptf_new'}
    assert (
        next(f for f in catalog if f['id'] == 'calc_ptf_new')['status']
        == 'ready-for-implementation'
    )


def test_strict_roster_is_refreshed_and_reconstruction_never_becomes_strict(
    analysis: ModuleType, monkeypatch: pytest.MonkeyPatch
):
    rolling = importlib.import_module(analysis.__name__.rsplit('.', 1)[0] + '.rolling')
    predictions = [
        {
            'function': f,
            'source_id': 's',
            'sample_id': '1',
            'target_pool': 'curve:water',
            'suction_kpa': 33,
            'water_quantity': 'volumetric_water_content',
            'target_evidence': {'tier': target},
            'predictor_evidence': {'x': {'tier': predictor}},
        }
        for f, target, predictor in [
            ('new', 'strict', 'derived'),
            ('interpolated', 'reconstructed', 'strict'),
            ('imputed', 'strict', 'approximate'),
        ]
    ]
    matrix = [dict(p) for p in predictions]
    monkeypatch.setattr(rolling, 'public_api_audit', lambda _: {})
    monkeypatch.setattr(rolling, 'audit', lambda _: {'functions': []})
    monkeypatch.setattr(rolling, 'evaluate_catalog', lambda *_: (matrix, predictions))
    context: dict = {
        'root': Path(),
        'catalog': [{'id': p['function'], 'fields': []} for p in predictions],
        'support': {},
        'datasets': [],
        'manifest': {},
        'strict_ids': {'historical'},
    }
    rolling.refresh_strict(context)
    assert context['strict_ids'] == {'new'}
    assert [p['function'] for p in context['strict_points']] == ['new']
    assert [r['strict_eligible'] for r in matrix] == [True, False, False]
