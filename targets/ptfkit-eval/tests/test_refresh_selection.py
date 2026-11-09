"""Independent scientific and selection contracts for the post-rebase refresh."""

import math

import pytest
from evaluation.experiments.meta_v3_3.campaign_contracts import canonical_input_unit
from evaluation.experiments.meta_v3_3.refresh_selection import (
    analyze,
    depth_interval,
    score,
    specialized,
    structurally_allowed,
)
from evaluation.experiments.meta_v3_3.rudiyanto_routes import DRY_HEAD_CM, KPA_PER_CM, fxw_water


def point(name: str, sample: str, error: float) -> dict:
    return {
        'basis': 'volumetric_water_content',
        'source_id': 'source',
        'sample_id': sample,
        'pressure_kpa': 10,
        'observed': 0.1,
        'predicted': 0.1 + error,
        'function': name,
    }


def test_coverage_precedes_own_support_error_and_a_single_candidate_is_not_validated():
    ledger = [point('', s, 0) for s in ('a', 'b')]
    predictions = [point('partial', 'a', 0.01), point('broad', 'a', 0.2), point('broad', 'b', 0.2)]
    result = analyze(predictions, ledger)
    comparison = result['coverage_comparison']
    assert comparison['coverage_candidate']['model'] == 'broad'
    assert comparison['maximum_points'] == 2
    assert comparison['coverage_candidate']['sample_balanced_rmse'] == pytest.approx(0.2)
    assert comparison['leader'] is None
    assert comparison['qualification'] == 'single_maximum_coverage_candidate'
    assert result['own_support_accuracy_diagnostic'][0]['model'] == 'partial'
    assert result['common_ranking_general_routes'][0]['model'] == 'partial'


def test_conductivity_errors_use_log10_and_report_factors():
    points = [
        {
            'basis': 'ksat',
            'id': str(i),
            'source_id': 'source',
            'sample_id': str(i),
            'pressure_kpa': None,
            'observed': observed,
            'predicted': predicted,
        }
        for i, (observed, predicted) in enumerate(((1e-6, 1e-5), (1e-7, 1e-7)))
    ]
    result = score(points, points, conductivity=True)
    assert result['sample_balanced_rmse'] == pytest.approx(math.sqrt(0.5))
    assert result['sample_balanced_bias'] == pytest.approx(0.5)
    assert result['within_factor_2'] == 0.5
    assert result['within_factor_10'] == 1
    assert result['median_predicted_observed_ratio'] == pytest.approx(5.5)


def test_soil_specific_ferrer_routes_are_not_general_recommendations():
    assert specialized('calc_ptf_ferrerjulia2004_gleyic_cambisol_sand')
    assert not specialized('calc_ptf_ferrerjulia2004_dane_puckett')
    assert not specialized('calc_ptf_ferrerjulia2004_general_sand')
    assert not structurally_allowed({'inputs': [{'name': 'sand'}, {'name': 'clay'}]}, ('clay',))
    assert structurally_allowed({'inputs': [{'name': 'clay'}]}, ('clay',))


def test_duplicate_depth_comparison_normalizes_dash_and_unit_spelling():
    assert depth_interval('60\u201480') == depth_interval('60-80 cm') == (60.0, 80.0)
    assert depth_interval('0\u201420') != depth_interval('0-5 cm')
    assert depth_interval(None) is None


def test_fxw_exact_saturation_and_oven_dry_endpoints_and_no_extrapolation():
    parameters = {'theta_s': 0.4, 'alpha': 0.01, 'n': 1.5, 'm': 0.3}
    assert fxw_water(parameters, 0) == 0.4
    assert fxw_water(parameters, DRY_HEAD_CM * KPA_PER_CM) == pytest.approx(0, abs=1e-15)
    with pytest.raises(ValueError, match='outside saturation-to-dryness support'):
        fxw_water(parameters, (DRY_HEAD_CM + 1) * KPA_PER_CM)


def test_fxw_retention_uses_correction_factor_not_conductivity_scaling():
    # Published FXW Eq. 17: at h=1500 cm choose alpha so Gamma=1/2.
    # The correction factor is 1-ln(2)/ln(4201), not scaled Gamma(h)-Gamma(h0).
    parameters = {'theta_s': 0.4, 'alpha': (math.exp(2) - math.e) / 1500, 'n': 1, 'm': 1}
    expected = 0.2 * (1 - math.log(2) / math.log(4201))
    assert fxw_water(parameters, 147.09975) == pytest.approx(expected, rel=1e-14)
    assert canonical_input_unit({'unit': 'kg/kg'}) == 'mass_fraction'
