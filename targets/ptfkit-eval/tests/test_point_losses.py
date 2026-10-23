import math
from dataclasses import replace

import pytest

from ptfkit_eval import (
    LogPressureLossPlan,
    PointErrorLossPlan,
    RetentionComparison,
    RetentionLossError,
    evaluate_sample_point_losses,
)


DOMAIN = LogPressureLossPlan(lower_suction_kpa=1, upper_suction_kpa=100)
ROSTER = (('source', 'a'), ('source', 'b'))
POINTS = tuple(
    RetentionComparison('source', sample, pressure, 0.5, predicted)
    for sample, rows in (('a', ((1, 0.5), (2, 0.75), (100, 1))), ('b', ((1, 0.75), (100, 0.75))))
    for pressure, predicted in rows
)


def test_mae_and_mse_use_equal_points_inside_each_full_original_sample_grid():
    mae = evaluate_sample_point_losses(
        POINTS,
        references=POINTS,
        sample_keys=ROSTER,
        plan=PointErrorLossPlan(selection_loss=DOMAIN, metric='mae'),
    )
    mse = evaluate_sample_point_losses(
        reversed(POINTS),
        references=reversed(POINTS),
        sample_keys=tuple(reversed(ROSTER)),
        plan=PointErrorLossPlan(selection_loss=DOMAIN, metric='mse'),
    )
    assert [s.point_count for s in mae] == [3, 2]
    assert [s.expected_point_count for s in mae] == [3, 2]
    assert [s.loss for s in mae] == [1 / 4, 1 / 4]
    assert [s.loss for s in mse] == pytest.approx([5 / 48, 1 / 16])
    assert all(s.reason is None for s in (*mae, *mse))


def test_missing_interior_forecast_is_not_a_smaller_scored_grid_with_fewer_errors():
    predictions = tuple(p for p in POINTS if p.suction_kpa != 2)
    result = evaluate_sample_point_losses(
        predictions,
        references=POINTS,
        sample_keys=ROSTER,
        plan=PointErrorLossPlan(selection_loss=DOMAIN, metric='mae'),
    )
    assert len(result) == 2
    assert result[0].loss is None
    assert result[0].point_count == 2
    assert result[0].expected_point_count == 3
    assert result[0].reason == 'incomplete_forecast_grid'
    assert result[1].loss == 1 / 4


def test_outside_domain_diagnostic_points_do_not_change_the_registered_assessment():
    outside = (*POINTS, RetentionComparison('source', 'a', 1000, 0.5, 1e308))
    plan = PointErrorLossPlan(selection_loss=DOMAIN, metric='mse')
    assert evaluate_sample_point_losses(
        outside, references=POINTS, sample_keys=ROSTER, plan=plan
    ) == (evaluate_sample_point_losses(POINTS, references=POINTS, sample_keys=ROSTER, plan=plan))


def test_unavailable_observations_and_training_failure_keep_original_sample_identities():
    keys = (*ROSTER, ('source', 'missing'))
    plan = PointErrorLossPlan(selection_loss=DOMAIN, metric='mae')
    result = evaluate_sample_point_losses(POINTS, references=POINTS, sample_keys=keys, plan=plan)
    assert len(result) == 3
    assert result[-1].sample_id == 'missing'
    assert result[-1].loss is None
    assert result[-1].reason == 'insufficient_points'
    failed = evaluate_sample_point_losses(
        (), references=POINTS, sample_keys=keys, plan=plan, training_failed=True
    )
    assert all(s.loss is None and s.reason == 'training_failed' for s in failed)
    assert [s.expected_point_count for s in failed] == [3, 2, 0]


def test_finite_large_absolute_error_is_retained_while_squared_overflow_stays_unavailable():
    large = tuple(replace(p, predicted=1e308) for p in POINTS)
    mae = evaluate_sample_point_losses(
        large,
        references=POINTS,
        sample_keys=ROSTER,
        plan=PointErrorLossPlan(selection_loss=DOMAIN, metric='mae'),
    )
    assert all(s.loss == pytest.approx(1e308) for s in mae)
    mse = evaluate_sample_point_losses(
        large,
        references=POINTS,
        sample_keys=ROSTER,
        plan=PointErrorLossPlan(selection_loss=DOMAIN, metric='mse'),
    )
    assert all(s.loss is None and s.reason == 'nonfinite_point_error' for s in mse)


@pytest.mark.parametrize(
    'change', ['observed', 'profile', 'extra', 'duplicate', 'unknown', 'nonfinite', 'failed']
)
def test_invalid_point_metadata_cannot_redefine_the_original_target_grid(change: str):
    predictions = POINTS
    if change == 'observed':
        predictions = (replace(POINTS[0], observed=0.25), *POINTS[1:])
    elif change == 'profile':
        predictions = (replace(POINTS[0], profile_id='other'), *POINTS[1:])
    elif change == 'extra':
        predictions = (*POINTS, replace(POINTS[0], suction_kpa=3))
    elif change == 'duplicate':
        predictions = (*POINTS, POINTS[0])
    elif change == 'unknown':
        predictions = (*POINTS, replace(POINTS[0], source_id='other'))
    elif change == 'nonfinite':
        predictions = (replace(POINTS[0], predicted=math.nan), *POINTS[1:])
    plan = PointErrorLossPlan(selection_loss=DOMAIN, metric='mae')
    with pytest.raises(RetentionLossError):
        evaluate_sample_point_losses(
            predictions,
            references=POINTS,
            sample_keys=ROSTER,
            plan=plan,
            training_failed=change == 'failed',
        )
