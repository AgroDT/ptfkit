import math
from dataclasses import replace

import pytest

from ptfkit_eval import RetentionQualityError, RetentionSeriesPoint, diagnose_retention_series


POINTS = (RetentionSeriesPoint(10, 0.4, 'a'), RetentionSeriesPoint(100, 0.3, 'b'))


def test_reports_exact_points_for_bounds_and_increasing_water_without_repair():
    points = (*POINTS, RetentionSeriesPoint(1000, 1.1, 'bad'))
    result = diagnose_retention_series(reversed(points))

    assert result.point_count == 3
    assert (result.minimum_suction_kpa, result.maximum_suction_kpa) == (10, 1000)
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        'water_outside_physical_bounds',
        'increasing_water_with_suction',
    ]
    assert result.diagnostics[0].points == (points[-1],)
    assert result.diagnostics[1].points == (points[1], points[2])
    assert points[-1].water_content == 1.1


def test_tolerance_is_explicit_and_does_not_widen_physical_bounds():
    points = (RetentionSeriesPoint(1, 0.5, 'a'), RetentionSeriesPoint(10, 0.625, 'b'))
    assert diagnose_retention_series(points, monotonicity_tolerance=0.125).diagnostics == ()
    assert len(diagnose_retention_series(points, monotonicity_tolerance=0.124).diagnostics) == 1
    outside = (RetentionSeriesPoint(1, -0.001, 'outside'),)
    assert (
        diagnose_retention_series(outside, monotonicity_tolerance=0.1).diagnostics[0].code
        == 'water_outside_physical_bounds'
    )


@pytest.mark.parametrize('tolerance', [-1, math.nan, math.inf, True])
def test_rejects_invalid_tolerances(tolerance: float):
    with pytest.raises(RetentionQualityError):
        diagnose_retention_series(POINTS, monotonicity_tolerance=tolerance)


def test_empty_and_monotone_curves_remain_distinct_from_violations():
    empty = diagnose_retention_series([])
    assert empty.point_count == 0
    assert empty.minimum_suction_kpa is None
    assert diagnose_retention_series(POINTS).diagnostics == ()


@pytest.mark.parametrize(
    'point', [replace(POINTS[0], suction_kpa=-1), replace(POINTS[0], water_content=math.nan)]
)
def test_invalid_canonical_values_do_not_turn_into_passing_quality_results(
    point: RetentionSeriesPoint,
):
    with pytest.raises(RetentionQualityError):
        diagnose_retention_series([point])
