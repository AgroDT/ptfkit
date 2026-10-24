import math
from dataclasses import replace

import numpy as np
import pytest

from ptfkit_eval import (
    TargetSpec,
    assess_profile_optimality,
    diagnose_fit_uncertainty_support,
    profile_retention_parameter,
)
from ptfkit_eval.families import RetentionFamilyError, evaluate_retention_family
from ptfkit_eval.fit_profiles import ParameterProfilePoint, RetentionParameterProfile
from ptfkit_eval.fitting import (
    ApproximationCurvePoint,
    ApproximationInterval,
    ApproximationParameter,
    FitParameterRange,
    RetentionFitError,
    RetentionFitPlan,
    evaluate_retention_fit,
    fit_retention_family,
)
from ptfkit_eval.quality import RetentionSeriesPoint


TARGET = TargetSpec('volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume')


def test_profile_optimality_uses_explicit_tolerance_and_retains_missing_evidence():
    profile = RetentionParameterProfile(
        'theta_s',
        ('theta_s',),
        8,
        (
            ParameterProfilePoint(0.4, None, ()),
            ParameterProfilePoint(0.5, 6, ()),
        ),
    )
    contact = assess_profile_optimality(profile, absolute_tolerance=1, relative_tolerance=0.125)
    assert contact.improvement_threshold == 2
    assert contact.objective_improvement == 2
    assert contact.status == 'no_improvement_detected'
    assert contact.failed_grid_points == 1
    improved = assess_profile_optimality(profile, absolute_tolerance=0, relative_tolerance=0.125)
    assert improved.status == 'lower_objective_found'
    assert improved.best_fixed_value == 0.5
    assert improved.best_sum_squared_error == 6
    empty = assess_profile_optimality(
        replace(profile, points=profile.points[:1]), absolute_tolerance=0, relative_tolerance=0
    )
    assert empty.status == 'no_converged_points'
    assert empty.objective_improvement is None
    for tolerance in (-1, float('inf'), float('nan'), True):
        with pytest.raises(RetentionFitError, match='tolerances'):
            assess_profile_optimality(profile, absolute_tolerance=tolerance, relative_tolerance=0)


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


def test_uncertainty_support_keeps_parameter_and_curve_violations_separate():
    failed = fit_retention_family([], plan=VG_PLAN)
    assert diagnose_fit_uncertainty_support(failed).status == 'fit_failed'
    point = RetentionSeriesPoint(10, 0.5, 'measured-row-7')
    parameters = tuple(
        ApproximationParameter(
            bounds.name,
            'test_unit',
            bounds.initial,
            None,
            ApproximationInterval(bounds.lower, bounds.upper),
        )
        for bounds in VG_PLAN.parameters
    )
    accepted = replace(
        failed,
        status='fitted',
        reason=None,
        parameters=parameters,
        points=(
            ApproximationCurvePoint(
                point,
                0.5,
                ApproximationInterval(0, 1),
                ApproximationInterval(-0.01, 1.01),
            ),
        ),
    )
    diagnosis = diagnose_fit_uncertainty_support(accepted)
    assert diagnosis.status == 'diagnosed'
    assert diagnosis.parameter_intervals_outside_bounds == ()
    assert diagnosis.mean_intervals_outside_physical_bounds == ()
    assert diagnosis.prediction_intervals_outside_physical_bounds == ('measured-row-7',)
    changed = replace(
        accepted,
        parameters=(
            replace(parameters[0], parameter_interval=ApproximationInterval(-0.01, 0.2)),
            replace(parameters[1], parameter_interval=ApproximationInterval(0.3, 0.81)),
            replace(parameters[2], parameter_interval=None),
            parameters[3],
        ),
        points=(
            replace(
                accepted.points[0],
                mean_curve_confidence_interval=ApproximationInterval(-0.01, 1),
                conditional_prediction_interval=ApproximationInterval(0, 1),
            ),
        ),
    )
    diagnosis = diagnose_fit_uncertainty_support(changed)
    assert diagnosis.parameter_intervals_outside_bounds == ('theta_r', 'theta_s')
    assert diagnosis.unavailable_parameter_intervals == ('alpha',)
    assert diagnosis.mean_intervals_outside_physical_bounds == ('measured-row-7',)
    assert diagnosis.prediction_intervals_outside_physical_bounds == ()
    assert changed.parameters[0].parameter_interval == ApproximationInterval(-0.01, 0.2)
    assert changed.points[0].mean_curve_confidence_interval.lower == -0.01


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


def test_parameter_profile_refits_nuisance_parameters_and_preserves_box_endpoints():
    points = tuple(
        RetentionSeriesPoint(h, 0.1 + 0.4 / math.sqrt(1 + (h / 10) ** 2), str(h))
        for h in [0, 0.1, 1, 3, 10, 30, 100, 300, 1000]
    )
    result = fit_retention_family(points, plan=VG_PLAN)
    assert result.status == 'fitted'
    profile = profile_retention_parameter(result, parameter_name='theta_s', grid=[0.3, 0.5, 0.8])
    assert tuple(point.fixed_value for point in profile.points) == (0.3, 0.5, 0.8)
    assert profile.points[1].sum_squared_error == pytest.approx(0, abs=1e-15)
    for point, lower_bound in zip(profile.points, [0.04, 0, 0.09], strict=True):
        assert point.sum_squared_error is not None
        assert point.sum_squared_error >= lower_bound - 1e-12
        assert len(point.attempts) == 3
        converged = [attempt for attempt in point.attempts if attempt.converged]
        assert converged
        for attempt in converged:
            assert all(
                bound.lower <= value <= bound.upper
                for bound, value in zip(
                    (VG_PLAN.parameters[0], *VG_PLAN.parameters[2:]), attempt.values, strict=True
                )
            )
    # Reoptimizing nuisance parameters must improve on holding every parameter fixed.
    held_fixed = math.fsum(
        (0.1 + 0.2 / math.sqrt(1 + (point.suction_kpa / 10) ** 2) - point.water_content) ** 2
        for point in points
    )
    profiled_error = profile.points[0].sum_squared_error
    assert profiled_error is not None
    assert profiled_error < held_fixed - 1e-4
    exhausted = profile_retention_parameter(
        replace(result, plan=replace(VG_PLAN, max_evaluations=1)),
        parameter_name='theta_s',
        grid=[0.3],
    )
    assert exhausted.points[0].sum_squared_error is None
    assert len(exhausted.points[0].attempts) == 3
    assert all(not attempt.converged for attempt in exhausted.points[0].attempts)
    assert profile == profile_retention_parameter(
        result, parameter_name='theta_s', grid=[0.3, 0.5, 0.8]
    )
    for grid in ([], [0.5, 0.5], [0.8, 0.3], [0.29], [float('nan')], [True]):
        with pytest.raises(RetentionFitError, match='grid'):
            profile_retention_parameter(result, parameter_name='theta_s', grid=grid)
    with pytest.raises(RetentionFitError, match='belong'):
        profile_retention_parameter(result, parameter_name='unknown', grid=[0.5])
    with pytest.raises(RetentionFitError, match='accepted'):
        profile_retention_parameter(
            fit_retention_family([], plan=VG_PLAN), parameter_name='theta_s', grid=[0.5]
        )
