import math
from dataclasses import replace

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
from ptfkit_eval.fit_restarts import pressure_interval_trials, pressure_partition_values
from ptfkit_eval.fitting import RetentionFitError


def test_pressure_partitions_ignore_order_duplicates_zero_and_outside_pressures():
    expected = (math.sqrt(2), 2, 4, 8, math.sqrt(128))
    assert pressure_partition_values([0, 8, 2, 2, 32], 1, 16) == pytest.approx(expected)
    assert pressure_partition_values([], 1, 16) == pytest.approx((4,))


def test_interval_trials_cover_the_box_without_changing_original_bounds_or_starts():
    initial = np.array([0.5, 7.0])
    lower, upper = np.array([0.3, 1.0]), np.array([0.8, 16.0])
    trials = pressure_interval_trials([initial], lower, upper, air_index=1, pressures=[0, 2, 8, 32])
    assert [trial.air_entry_interval for trial in trials] == [None, (1, 2), (2, 8), (8, 16)]
    assert trials[0].initial.tolist() == [0.5, 7]
    for trial, midpoint in zip(trials[1:], [math.sqrt(2), 4, math.sqrt(128)], strict=True):
        assert trial.initial.tolist() == pytest.approx([0.5, midpoint])
        assert trial.lower[0] == 0.3
        assert trial.upper[0] == 0.8
        assert trial.lower[1] < trial.initial[1] < trial.upper[1]
    assert lower.tolist() == [0.3, 1]
    assert upper.tolist() == [0.8, 16]
    assert initial.tolist() == [0.5, 7]


def test_pressure_restarts_preserve_original_attempts_and_apply_to_nuisance_profiles():
    plan = RetentionFitPlan(
        family_id='brooks_corey_v1',
        target=TargetSpec(
            'volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume'
        ),
        seed=17,
        minimum_log10_span=2,
        n_starts=2,
        parameters=(
            FitParameterRange('theta_r', 0, 0.2, 0.05),
            FitParameterRange('theta_s', 0.3, 0.8, 0.45),
            FitParameterRange('air_entry', 1, 16, 7),
            FitParameterRange('lambda', 0.1, 2, 0.8),
        ),
    )
    points = tuple(
        RetentionSeriesPoint(h, 0.5 if h <= 4 else 0.1 + 0.4 * math.sqrt(4 / h), str(h))
        for h in (0, 2, 8, 32, 100, 300, 1000)
    )
    original = fit_retention_family(points, plan=plan)
    expanded = fit_retention_family(
        points, plan=replace(plan, restart_policy='brooks_corey_pressure_partitions_v1')
    )
    assert expanded.status == 'fitted', expanded.reason
    assert expanded.attempts[:2] == original.attempts
    assert len(expanded.attempts) == 7
    assert [attempt.initial_values[2] for attempt in expanded.attempts[2:]] == pytest.approx(
        (math.sqrt(2), 2, 4, 8, math.sqrt(128))
    )
    assert all(
        attempt.initial_values[:2] == (0.05, 0.45) and attempt.initial_values[3] == 0.8
        for attempt in expanded.attempts[2:]
    )
    profile = profile_retention_parameter(expanded, parameter_name='theta_s', grid=[0.3, 0.5, 0.8])
    assert all(len(point.attempts) == 7 for point in profile.points)
    fixed = profile_retention_parameter(expanded, parameter_name='air_entry', grid=[1, 4, 16])
    assert all(len(point.attempts) == 2 for point in fixed.points)
    interval_fit = fit_retention_family(
        points, plan=replace(plan, restart_policy='brooks_corey_interval_solves_v1')
    )
    assert interval_fit.status == 'fitted', interval_fit.reason
    assert interval_fit.attempts[:2] == original.attempts
    assert len(interval_fit.attempts) == 8
    assert [attempt.air_entry_interval for attempt in interval_fit.attempts[2:]] == [
        (1, 2),
        (1, 2),
        (2, 8),
        (2, 8),
        (8, 16),
        (8, 16),
    ]
    interval_profile = profile_retention_parameter(
        interval_fit, parameter_name='theta_s', grid=[0.3, 0.5, 0.8]
    )
    assert all(len(point.attempts) == 8 for point in interval_profile.points)
    knot_points = tuple(
        RetentionSeriesPoint(h, 0.5 if h <= 8 else 0.1 + 0.4 * math.sqrt(8 / h), str(h))
        for h in (0, 2, 8, 32, 100, 300, 1000)
    )
    knot_fit = fit_retention_family(
        knot_points, plan=replace(plan, restart_policy='brooks_corey_interval_solves_v1')
    )
    assert knot_fit.status == 'fitted', knot_fit.reason
    assert knot_fit.identifiability is not None
    assert knot_fit.identifiability.boundary_parameters == ()
    assert next(
        item.value for item in knot_fit.parameters if item.name == 'air_entry'
    ) == pytest.approx(8, abs=1e-5)
    with pytest.raises(RetentionFitError, match='restart policy'):
        replace(
            plan,
            family_id='van_genuchten_mualem_v1',
            restart_policy='brooks_corey_pressure_partitions_v1',
        )
