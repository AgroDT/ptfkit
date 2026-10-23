import math
from dataclasses import replace

import pytest

from ptfkit_eval import (
    LogPressureLossPlan,
    RetentionComparison,
    RetentionLossError,
    evaluate_log_pressure_loss,
)
from ptfkit_eval.losses import mean_finite_losses


PLAN = LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100)
POINTS = (
    RetentionComparison('source', 'sample', 1, 0.5, 0.5),
    RetentionComparison('source', 'sample', 10, 0.5, 1.0),
    RetentionComparison('source', 'sample', 100, 0.5, 1.0),
)


def test_log_pressure_integral_uses_equal_decades_and_exact_registered_endpoints():
    loss = evaluate_log_pressure_loss(reversed(POINTS), plan=PLAN)[0]
    # Equal decades have trapezoid mean squared errors 1/8 and 1/4: mean 3/16.
    assert loss.loss == pytest.approx(3 / 16)
    assert loss.reason is None
    assert loss.point_count == 3


def test_subdividing_piecewise_linear_squared_error_does_not_change_loss():
    middle = replace(POINTS[0], suction_kpa=math.sqrt(10), predicted=0.5 + math.sqrt(1 / 8))
    loss = evaluate_log_pressure_loss((*POINTS, middle), plan=PLAN)[0]
    assert loss.loss == pytest.approx(3 / 16)


def test_missing_endpoints_are_not_interpolated_or_extrapolated():
    points = (replace(POINTS[0], suction_kpa=2), *POINTS[1:])
    loss = evaluate_log_pressure_loss(points, plan=PLAN)[0]
    assert loss.loss is None
    assert loss.reason == 'missing_domain_endpoints'


def test_finite_large_errors_remain_finite_after_log_pressure_normalization():
    points = tuple(replace(point, predicted=1e154) for point in POINTS)
    loss = evaluate_log_pressure_loss(points, plan=PLAN)[0]
    assert loss.loss is not None
    assert math.isfinite(loss.loss)
    assert loss.loss == pytest.approx(1e308)


def test_loss_mean_preserves_subnormal_values_and_handles_a_large_finite_mean():
    smallest = math.ulp(0.0)
    assert mean_finite_losses([smallest, smallest]) == smallest
    assert mean_finite_losses([1e308, 1e308, 1e308]) == pytest.approx(1e308)


def test_adjacent_large_pressures_have_a_positive_logarithmic_span():
    lower = 1e300
    upper = math.nextafter(lower, math.inf)
    points = (
        RetentionComparison('source', 'sample', lower, 0.5, 0.75),
        RetentionComparison('source', 'sample', upper, 0.5, 0.75),
    )
    policy = LogPressureLossPlan(lower_suction_kpa=lower, upper_suction_kpa=upper)
    assert evaluate_log_pressure_loss(points, plan=policy)[0].loss == pytest.approx(1 / 16)


@pytest.mark.parametrize(('lower', 'upper'), [(0, 10), (-1, 10), (10, 10), (100, 1), (1, math.inf)])
def test_invalid_log_pressure_domains_cannot_define_selection_loss(lower: float, upper: float):
    with pytest.raises(RetentionLossError):
        LogPressureLossPlan(lower_suction_kpa=lower, upper_suction_kpa=upper)
