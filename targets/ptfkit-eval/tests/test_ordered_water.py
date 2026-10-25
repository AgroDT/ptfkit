from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

import numpy as np
import pytest

from ptfkit_eval import (
    FitParameterRange,
    RetentionFitPlan,
    RetentionSeriesPoint,
    TargetSpec,
    fit_retention_family,
    profile_retention_parameter,
)
from ptfkit_eval.fitting import RetentionFitError
from ptfkit_eval.ordered_water import OrderedWaterCoordinates


if TYPE_CHECKING:
    from numpy.typing import NDArray

    from ptfkit_eval import RetentionFitResult


@pytest.mark.parametrize('saturation', [0.3, 0.8])
def test_conditional_coordinates_preserve_physical_jacobian(saturation: float):
    coordinates = OrderedWaterCoordinates.create(
        ('theta_r', 'theta_s'), np.array([0.0, 0.1]), np.array([0.533, 0.96])
    )
    encoded = np.array([0.5, saturation])
    cap = min(0.533, saturation - 1e-10)
    assert coordinates.decode(encoded) == pytest.approx([0.5 * cap, saturation])
    # For the independent linear oracle f=2*r+3*s, J_u=2*cap and
    # J_s=3+2*u in the conditional branch, otherwise J_s=3.
    optimizer_jacobian = np.array([[2 * cap, 4 if saturation == 0.3 else 3]])
    np.testing.assert_allclose(coordinates.physical_jacobian(encoded, optimizer_jacobian), [[2, 3]])


@pytest.fixture(params=['van_genuchten_mualem_v1', 'van_genuchten_m1_v1', 'brooks_corey_v1'])
def ordered_fit(request: pytest.FixtureRequest):
    family = request.param
    axis = np.geomspace(0.01, 10000, 35)
    residual, saturated = 0.26, 0.45
    if family == 'brooks_corey_v1':
        observed = residual + (saturated - residual) * np.minimum(1, (axis / 3) ** -0.6)
        shapes = (
            FitParameterRange('air_entry', 0.01, 30, 1),
            FitParameterRange('lambda', 0.05, 2, 0.5),
        )
    else:
        n = 1.8
        m = 1 - 1 / n if family == 'van_genuchten_mualem_v1' else 1
        observed = residual + (saturated - residual) / (1 + (0.4 * axis) ** n) ** m
        shapes = (FitParameterRange('alpha', 0.001, 10, 0.1), FitParameterRange('n', 1.05, 5, 2))
    observed += np.array([(-1) ** i * 1e-5 for i in range(len(axis))])
    points = tuple(
        RetentionSeriesPoint(float(h), float(w), str(i))
        for i, (h, w) in enumerate(zip(axis, observed, strict=True))
    )
    plan = RetentionFitPlan(
        family_id=family,
        target=TargetSpec(
            'volumetric_water_content', 'volume_fraction', 'unspecified', 'bulk_volume'
        ),
        parameters=(
            FitParameterRange('theta_r', 0, 0.533, 0.2),
            FitParameterRange('theta_s', 0.1, 0.96, 0.7),
            *shapes,
        ),
        seed=7123,
        minimum_log10_span=2,
        n_starts=4,
        method='bounded_trf_ordered_water_multistart_v1',
    )
    with pytest.raises(RetentionFitError, match='nonoverlapping'):
        replace(plan, method='bounded_trf_uniform_multistart_v1')
    result = fit_retention_family(points, plan=plan)
    assert result.status == 'fitted', result.reason
    estimates = {p.name: p.value for p in result.parameters}
    assert estimates['theta_r'] == pytest.approx(residual, abs=1e-4)
    assert estimates['theta_s'] == pytest.approx(saturated, abs=1e-4)
    for attempt in result.attempts:
        assert attempt.initial_values[0] < attempt.initial_values[1]
        if attempt.converged:
            assert attempt.values[0] < attempt.values[1]
    return result


def test_ordered_fit_covariance_uses_physical_coordinates(ordered_fit: RetentionFitResult):
    result = ordered_fit
    assert result.parameter_covariance is not None
    assert result.residual_variance is not None
    values = np.array([p.value for p in result.parameters])
    axis = np.array([p.suction_kpa for p in result.observations])

    def oracle(parameters: NDArray[np.float64]) -> NDArray[np.float64]:
        r, s, scale, shape = parameters
        if result.plan.family_id == 'brooks_corey_v1':
            return r + (s - r) * np.minimum(1, (axis / scale) ** -shape)
        m = 1 - 1 / shape if result.plan.family_id == 'van_genuchten_mualem_v1' else 1
        return r + (s - r) / (1 + (scale * axis) ** shape) ** m

    columns = []
    for index in range(4):
        delta = np.zeros(4)
        delta[index] = 1e-6
        columns.append((oracle(values + delta) - oracle(values - delta)) / (2e-6))
    jacobian = np.column_stack(columns)
    expected = np.linalg.inv(jacobian.T @ jacobian) * result.residual_variance
    np.testing.assert_allclose(result.parameter_covariance, expected, rtol=2e-4, atol=1e-18)


@pytest.mark.parametrize(
    ('parameter', 'grid'), [('theta_s', [0.15, 0.61, 0.8]), ('theta_r', [0, 0.26, 0.5])]
)
def test_ordered_profiles_restrict_nuisance_water_to_feasible_region(
    ordered_fit: RetentionFitResult, parameter: str, grid: list[float]
):
    profile = profile_retention_parameter(ordered_fit, parameter_name=parameter, grid=grid)
    nuisance = [name for name in profile.parameter_order if name != parameter]
    for point in profile.points:
        assert point.sum_squared_error is not None
        for attempt in point.attempts:
            values = dict(zip(nuisance, attempt.values, strict=True))
            values[parameter] = point.fixed_value
            assert values['theta_r'] < values['theta_s']


def test_additional_physical_start_preserves_seeded_solves_and_profile_order(
    ordered_fit: RetentionFitResult,
):
    truth = (
        (0.26, 0.45, 3, 0.6)
        if ordered_fit.plan.family_id == 'brooks_corey_v1'
        else (0.26, 0.45, 0.4, 1.8)
    )
    plan = replace(
        ordered_fit.plan,
        parameters=tuple(reversed(ordered_fit.plan.parameters)),
        additional_starts=(truth,),
    )
    result = fit_retention_family(ordered_fit.observations, plan=plan)
    assert result.attempts[: plan.n_starts] == ordered_fit.attempts
    assert len(result.attempts) == plan.n_starts + 1
    added = result.attempts[-1]
    assert added.initial_values == truth
    assert added.converged
    assert added.sum_squared_error is not None
    assert (
        added.sum_squared_error
        <= min(
            a.sum_squared_error
            for a in ordered_fit.attempts
            if a.converged and a.sum_squared_error is not None
        )
        + 1e-12
    )
    assert result.status == 'fitted'
    profile = profile_retention_parameter(result, parameter_name='theta_s', grid=[0.45])
    assert len(profile.points[0].attempts) == plan.n_starts + 1
    names = tuple(name for name in profile.parameter_order if name != 'theta_s')
    initial = dict(zip(names, profile.points[0].attempts[-1].initial_values, strict=True))
    assert initial['theta_r'] == pytest.approx(0.26)
    if plan.family_id == 'brooks_corey_v1':
        assert initial['air_entry'] == 3
        assert initial['lambda'] == 0.6
    else:
        assert initial['alpha'] == 0.4
        assert initial['n'] == 1.8


@pytest.mark.parametrize(
    'start',
    [
        (0.26, 0.45, 0.4),
        (float('nan'), 0.45, 0.4, 1.8),
        (True, 0.45, 0.4, 1.8),
        (-0.1, 0.45, 0.4, 1.8),
        (0.5, 0.2, 0.4, 1.8),
    ],
)
def test_invalid_additional_starts_are_rejected(ordered_fit: RetentionFitResult, start: tuple):
    with pytest.raises(RetentionFitError, match='Additional'):
        replace(ordered_fit.plan, additional_starts=(start,))
