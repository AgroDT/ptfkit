import math
from dataclasses import replace

import numpy as np
import pytest

from ptfkit_eval import TargetSpec
from ptfkit_eval.families import RetentionFamilyError, evaluate_retention_family
from ptfkit_eval.fitting import (
    FitParameterRange,
    RetentionFitError,
    RetentionFitPlan,
    evaluate_retention_fit,
    fit_retention_family,
)
from ptfkit_eval.quality import RetentionSeriesPoint


TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')
VG_PLAN = RetentionFitPlan(
    family_id='van_genuchten_mualem_v1',
    target=TARGET,
    seed=381,
    minimum_log10_span=2,
    parameters=(
        FitParameterRange('theta_r', 0, 0.2, 0.05),
        FitParameterRange('theta_s', 0.3, 0.8, 0.45),
        FitParameterRange('alpha', 0.01, 1, 0.08),
        FitParameterRange('n', 1.1, 4, 1.8),
    ),
)


@pytest.mark.parametrize(
    ('family', 'expected'),
    [
        ('van_genuchten_mualem_v1', 0.1 + 0.4 / math.sqrt(2)),
        ('van_genuchten_m1_v1', 0.3),
    ],
)
def test_registered_van_genuchten_variants_have_distinct_equations(family: str, expected: float):
    values = evaluate_retention_family(
        family, {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.1, 'n': 2}, [0, 10]
    )
    assert values == pytest.approx([0.5, expected])


def test_brooks_corey_retains_its_saturated_plateau_and_published_power_branch():
    values = evaluate_retention_family(
        'brooks_corey_v1',
        {'theta_r': 0.1, 'theta_s': 0.5, 'air_entry': 10, 'lambda': 0.5},
        [0, 5, 10, 40],
    )
    assert values == pytest.approx([0.5, 0.5, 0.5, 0.3])


@pytest.mark.parametrize('family', ['van_genuchten_mualem_v1', 'van_genuchten_m1_v1'])
def test_recovers_noiseless_van_genuchten_parameters_from_independent_curves(family: str):
    pressures = [0, 0.1, 1, 3, 10, 30, 100, 300, 1000]
    points = [
        RetentionSeriesPoint(
            h,
            0.1 + 0.4 / ((1 + (h / 10) ** 2) ** (0.5 if family.endswith('mualem_v1') else 1)),
            str(h),
        )
        for h in pressures
    ]
    plan = replace(VG_PLAN, family_id=family)
    result = fit_retention_family(points, plan=plan)
    assert result.status == 'fitted', result.reason
    assert {parameter.name: parameter.value for parameter in result.parameters} == pytest.approx(
        {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.1, 'n': 2}, abs=1e-6
    )
    assert result == fit_retention_family(reversed(points), plan=plan)
    assert evaluate_retention_fit(result, [0, 1000]) == pytest.approx(
        [points[0].water_content, points[-1].water_content]
    )
    with pytest.raises(RetentionFitError, match='extrapolation'):
        evaluate_retention_fit(result, [1001])


def test_recovers_brooks_corey_parameters_with_wet_and_dry_observations():
    pressures = [0, 0.1, 1, 5, 20, 50, 100, 1000, 10000]
    points = [
        RetentionSeriesPoint(h, 0.5 if h <= 10 else 0.1 + 0.4 * math.sqrt(10 / h), str(h))
        for h in pressures
    ]
    plan = replace(
        VG_PLAN,
        family_id='brooks_corey_v1',
        parameters=(
            *VG_PLAN.parameters[:2],
            FitParameterRange('air_entry', 1, 30, 7),
            FitParameterRange('lambda', 0.1, 2, 0.8),
        ),
    )
    result = fit_retention_family(points, plan=plan)
    assert result.status == 'fitted', result.reason
    assert {parameter.name: parameter.value for parameter in result.parameters} == pytest.approx(
        {'theta_r': 0.1, 'theta_s': 0.5, 'air_entry': 10, 'lambda': 0.5}, abs=1e-5
    )


def test_recovers_clapp_parameters_in_kpa_without_reusing_the_adapter_as_an_oracle():
    points = [
        RetentionSeriesPoint(h, 0.4 if h == 0 else 0.4 / h**0.25, str(h))
        for h in [0, 2, 5, 10, 20, 100, 1000]
    ]
    plan = replace(
        VG_PLAN,
        family_id='clapp1978_gradual_air_entry_v1',
        parameters=(
            FitParameterRange('theta_s', 0.3, 0.8, 0.45),
            FitParameterRange('saturation_suction', 0.2, 2, 0.8),
            FitParameterRange('b', 2, 6, 3.8),
        ),
    )
    result = fit_retention_family(points, plan=plan)
    assert result.status == 'fitted', result.reason
    assert {parameter.name: parameter.value for parameter in result.parameters} == pytest.approx(
        {'theta_s': 0.4, 'saturation_suction': 1, 'b': 4}, abs=1e-5
    )


def test_local_uncertainty_matches_independent_analytic_jacobian_and_distinguishes_prediction():
    pressures = [0, 1, 10, 100, 1000]
    points = [
        RetentionSeriesPoint(h, 0.1 + 0.4 / math.sqrt(1 + (h / 10) ** 2) + noise, str(h))
        for h, noise in zip(pressures, [0.001, -0.002, 0.003, -0.001, 0.001], strict=True)
    ]
    result = fit_retention_family(points, plan=replace(VG_PLAN, confidence_level=0.5))
    assert result.status == 'fitted', result.reason
    residual_variance = math.fsum(
        (point.fitted_value - point.observation.water_content) ** 2 for point in result.points
    )
    assert result.residual_variance == pytest.approx(residual_variance)
    parameters = {parameter.name: parameter.value for parameter in result.parameters}
    delta = parameters['theta_s'] - parameters['theta_r']
    alpha, n = parameters['alpha'], parameters['n']
    m = 1 - 1 / n
    jacobian = []
    for h in pressures:
        if h == 0:
            jacobian.append([0, 1, 0, 0])
            continue
        z = (alpha * h) ** n
        effective = (1 + z) ** -m
        jacobian.append(
            [
                1 - effective,
                effective,
                -delta * effective * m * n * z / (alpha * (1 + z)),
                -delta
                * effective
                * (math.log(1 + z) / n**2 + m * z * math.log(alpha * h) / (1 + z)),
            ]
        )
    design = np.array(jacobian)
    expected = np.linalg.inv(design.T @ design) * residual_variance
    assert result.parameter_covariance is not None
    np.testing.assert_allclose(result.parameter_covariance, expected, rtol=1e-4, atol=1e-12)
    # Five observations minus four parameters gives df=1; the central 50% critical value is 1.
    for parameter in result.parameters:
        assert parameter.standard_error is not None
        assert parameter.parameter_interval is not None
        assert parameter.parameter_interval.upper - parameter.value == pytest.approx(
            parameter.standard_error
        )
    for point in result.points:
        mean_width = point.mean_curve_confidence_interval.upper - point.fitted_value
        future_width = point.conditional_prediction_interval.upper - point.fitted_value
        assert future_width**2 - mean_width**2 == pytest.approx(residual_variance)


def test_rank_deficient_plateau_is_not_reported_as_a_parameter_fit():
    plan = replace(
        VG_PLAN,
        family_id='brooks_corey_v1',
        parameters=(
            *VG_PLAN.parameters[:2],
            FitParameterRange('air_entry', 10, 100, 30),
            FitParameterRange('lambda', 0.1, 2, 0.8),
        ),
    )
    points = [RetentionSeriesPoint(h, 0.4, str(h)) for h in [0, 0.01, 0.1, 1, 2]]
    result = fit_retention_family(points, plan=plan)
    assert result.status == 'failed'
    assert result.reason == 'nonidentifiable'
    assert result.parameters == ()
    assert result.identifiability is not None
    assert result.identifiability.jacobian_rank < 4


def test_insufficient_data_and_optimizer_failure_remain_explicit():
    points = [
        RetentionSeriesPoint(h, 0.1 + 0.4 / math.sqrt(1 + (h / 10) ** 2), str(h))
        for h in [0, 1, 3, 10, 30, 100, 1000]
    ]
    assert fit_retention_family(points[:3], plan=VG_PLAN).reason == 'insufficient_observations'
    assert (
        fit_retention_family(points, plan=replace(VG_PLAN, max_evaluations=1)).reason
        == 'optimizer_failed'
    )


def test_physically_ambiguous_boxes_are_rejected_before_optimization():
    with pytest.raises(RetentionFitError, match='nonoverlapping'):
        replace(
            VG_PLAN, parameters=(replace(VG_PLAN.parameters[0], upper=0.4), *VG_PLAN.parameters[1:])
        )
    with pytest.raises(RetentionFamilyError):
        evaluate_retention_family(
            'van_genuchten_mualem_v1', {'theta_r': 0.1, 'theta_s': 0.5, 'alpha': 0.1, 'n': 1}, [10]
        )
