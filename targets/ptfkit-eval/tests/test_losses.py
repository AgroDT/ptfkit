import math
from dataclasses import replace

import pytest

from ptfkit_eval import (
    LogPressureLossPlan,
    RetentionComparison,
    RetentionLossError,
    evaluate_log_pressure_loss,
)


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


@pytest.mark.parametrize(('lower', 'upper'), [(0, 10), (-1, 10), (10, 10), (100, 1), (1, math.inf)])
def test_invalid_log_pressure_domains_cannot_define_selection_loss(lower: float, upper: float):
    with pytest.raises(RetentionLossError):
        LogPressureLossPlan(lower_suction_kpa=lower, upper_suction_kpa=upper)
