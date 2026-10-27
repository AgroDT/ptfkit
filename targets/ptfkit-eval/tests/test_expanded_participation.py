"""Independent numeric contracts for expanded E5 routes and held-out selection."""

import math

import numpy as np
import pytest
from evaluation.experiments.meta_v3_3.expanded_predictors import (
    psd_fraction,
    recovered_texture,
    water_convert,
)
from evaluation.experiments.meta_v3_3.expanded_routes import (
    family_variant,
    interpolate_native,
    parameter_curve,
)
from evaluation.experiments.meta_v3_3.expanded_selection import (
    choose_members,
    correlation_matrix,
    ensemble_assessment,
)


def test_discrete_family_uses_log_pressure_and_separates_zero() -> None:
    """A geometric pressure third must yield an arithmetic water-content third."""
    native = [(0.0, 0.5), (1.0, 0.4), (1000.0, 0.1)]
    assert interpolate_native(native, 10) == pytest.approx(0.3)
    assert interpolate_native(native, 0) == 0.5
    for pressure in (0.5, 1001):
        with pytest.raises(ValueError, match='outside native'):
            interpolate_native(native, pressure)


def test_pressure_removal_preserves_equation_sets_and_predictors() -> None:
    variants = [
        family_variant(
            {
                'source': 'gunarathna2019',
                'id': f'calc_ptf_gunarathna2019_vwc{pressure}_set{variant}',
            }
        )
        for variant, pressure in ((1, 10), (1, 1500), (3, 10))
    ]
    assert variants[0] == variants[1]
    assert variants[0] != variants[2]
    clay = family_variant(
        {'source': 'lal1979', 'id': 'calc_ptf_lal1979_group_i_water_0bar_from_clay'}
    )
    sand = family_variant(
        {'source': 'lal1979', 'id': 'calc_ptf_lal1979_group_i_water_15bar_from_sand'}
    )
    assert clay != sand


def test_parameter_curve_uses_m1_and_centimeter_pressure_scale() -> None:
    """At alpha*h=1 and n=2, m=1 gives half amplitude; Mualem would not."""
    parameters = {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.01, 'n': 2}
    assert parameter_curve('calc_ptf_vereecken1989_detailed', parameters, 9.80665) == pytest.approx(
        0.3
    )
    assert parameter_curve('calc_ptf_vereecken1989_detailed', parameters, 0) == 0.5


def test_brooks_corey_plateau_and_dry_power_are_distinct() -> None:
    parameters = {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.01, 'conductivity_lambda': 0.5}
    assert parameter_curve('calc_ptf_saxton1986_calcptf_parameters', parameters, 9.80665) == 0.5
    assert parameter_curve(
        'calc_ptf_saxton1986_calcptf_parameters', parameters, 39.2266
    ) == pytest.approx(0.3)


def test_saxton_inverse_segments_keep_predicted_anchors_and_support() -> None:
    dry = {'theta_1500': 0.1, 'theta_33': 0.4}
    assert parameter_curve(
        'calc_ptf_saxton2006_tension_dry', dry, math.sqrt(33 * 1500)
    ) == pytest.approx(0.2)
    with pytest.raises(ValueError, match='33<=p<=1500'):
        parameter_curve('calc_ptf_saxton2006_tension_dry', dry, 10)
    wet = {'theta_33': 0.2, 'theta_s': 0.5, 'air_entry_tension': 3}
    assert parameter_curve('calc_ptf_saxton2006_tension_wet', wet, 18) == pytest.approx(0.35)
    assert parameter_curve('calc_ptf_saxton2006_tension_wet', wet, 0) == 0.5


def test_psd_subdivision_is_logarithmic_and_never_bridges_missing_bins() -> None:
    bins = {
        'intervals_um': [[50, 500], [0, 1]],
        'values': [40, 20],
        'sources': [['PSD!A2'], ['PSD!B2']],
    }
    value, cells = psd_fraction(bins, 50, math.sqrt(50 * 500))
    assert value == pytest.approx(20)
    assert cells == ['PSD!A2']
    with pytest.raises(ValueError, match='unobserved gap'):
        psd_fraction(bins, 0, 500)
    with pytest.raises(ValueError, match='lower tail'):
        psd_fraction(bins, 0, 0.5)


def test_silt_closure_requires_two_independent_reported_fractions() -> None:
    row = {
        'values': {'M': 20, 'P': 50},
        'value_cells': {'M': ['master!M2'], 'P': ['master!P2']},
        'clay_upper_um': 1,
    }
    recovered = recovered_texture(row)
    assert recovered['silt'][0] == 30
    assert recovered['silt'][1] == ['master!M2', 'master!P2']
    assert recovered['clay'][2]['original_interval_um'] == [0, 10]
    del row['values']['P']
    assert 'silt' not in recovered_texture(row)
    assert 'sand' not in recovered_texture(row)


def test_water_basis_conversion_never_supplies_default_density() -> None:
    row = {'values': {'Q': 1.5}, 'value_cells': {'Q': ['master!Q2']}}
    value, proof = water_convert(0.3, 'volumetric_water_content', 'gravimetric_water_content', row)
    assert value == pytest.approx(0.2)
    assert proof is not None
    assert proof['sources'] == ['master!Q2']
    with pytest.raises(ValueError, match='same-record bulk density'):
        water_convert(0.3, 'volumetric_water_content', 'gravimetric_water_content', {'values': {}})


def test_member_selection_cannot_rank_using_held_out_loss() -> None:
    residuals = np.array([[0.1, 0.2, 0.3], [0.2, 0.1, -0.1], [99, 0, 0]])
    squared = np.square(residuals)
    selected = choose_members(
        residuals,
        squared,
        residuals,
        np.array([1, 1, 0]),
        ['a', 'b', 'c'],
        np.array([True, True, False]),
    )
    assert selected['top_2'] == [0, 1]
    squared[2] = [0, 1e9, 1e9]
    residuals[2] = [-1e6, 1e6, 1e6]
    changed = choose_members(
        residuals,
        squared,
        residuals,
        np.array([1, 1, 0]),
        ['a', 'b', 'c'],
        np.array([True, True, False]),
    )
    assert selected == changed


def test_redundant_residuals_do_not_inflate_effective_member_count() -> None:
    matrix, effective = correlation_matrix(np.array([[1, 1], [2, 2], [4, 4]], dtype=float))
    assert matrix == pytest.approx(np.ones((2, 2)))
    assert effective == pytest.approx(1)


def test_ensemble_metrics_balance_samples_instead_of_points() -> None:
    # Sample A has three errors of 0; sample B has one error of 2.
    points: list[dict] = [
        {
            'id': str(i),
            'source_id': source,
            'sample_id': source,
            'observed': 0.0,
            'predicted': value,
            'pressure_kpa': pressure,
            'basis': 'volumetric_water_content',
            'profile_id': None,
        }
        for i, (source, value, pressure) in enumerate(
            (('a', 0, 1), ('a', 0, 10), ('a', 0, 100), ('b', 2, 1))
        )
    ]
    indices = {
        name: {p['id']: {**p, 'predicted': p['predicted'] * scale} for p in points}
        for name, scale in (('one', 1), ('two', 0.5))
    }
    result = ensemble_assessment(indices, ['one', 'two'], [p['id'] for p in points])
    # Mean predictions: [0,0,0,1.5]. Equal-sample MSE=(0+2.25)/2.
    assert result['ensembles']['mean']['rmse'] == pytest.approx(math.sqrt(1.125))
    assert result['ensembles']['mean']['mae'] == 0.75
    assert result['dimension'] == 'source_id'
    assert len(result['folds']) == 2
