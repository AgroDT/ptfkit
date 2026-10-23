from dataclasses import replace

import pytest

from ptfkit_eval import (
    ConformalLeakageError,
    ConformalPrediction,
    GroupedConformalPlan,
    GroupedSample,
    RetentionComparison,
    TargetSpec,
    apply_grouped_prediction_intervals,
    calibrate_grouped_prediction_intervals,
)


def _fixture(
    count: int = 9, confidence: float = 0.9
) -> tuple[GroupedConformalPlan, tuple[GroupedSample, ...], tuple[RetentionComparison, ...]]:
    plan = GroupedConformalPlan(
        candidate_id='fixed_candidate',
        protocol_id='synthetic_grid',
        target=TargetSpec(
            'volumetric_water_content', 'volume_fraction', 'fine_earth', 'bulk_volume'
        ),
        calibration_groups=tuple((f'cal_{index}', '') for index in range(count)),
        training_groups=(('train', ''),),
        test_groups=(('test', ''),),
        pressure_grid_kpa=(10, 100),
        confidence_level=confidence,
    )
    samples = tuple(
        GroupedSample(source, 'one', 'profile')
        for source in (*(f'cal_{index}' for index in range(count)), 'train', 'test')
    )
    points = tuple(
        RetentionComparison(
            f'cal_{index}', 'one', pressure, 0.5 + (index + 1) * 0.01 * factor, 0.5, 'profile'
        )
        for index in range(count)
        for pressure, factor in ((10, 0.5), (100, 1))
    )
    return plan, samples, points


def test_whole_group_maximum_and_finite_sample_rank_give_hand_calculated_bounds():
    plan, samples, points = _fixture()
    calibration = calibrate_grouped_prediction_intervals(points, samples=samples, plan=plan)

    assert calibration.status == 'calibrated'
    assert calibration.quantile_rank == 9
    assert calibration.half_width == pytest.approx(0.09)
    assert len(calibration.scores) == 9
    assert calibration.scores[0].maximum_absolute_error == pytest.approx(0.01)
    future = ConformalPrediction('test', 'one', 'profile', 10, 0.25)
    interval = apply_grouped_prediction_intervals(calibration, [future])[0]
    assert interval.status == 'computed'
    assert (interval.lower, interval.upper) == pytest.approx((0.16, 0.34))
    assert calibration == calibrate_grouped_prediction_intervals(
        reversed(points), samples=reversed(samples), plan=plan
    )


@pytest.mark.parametrize(('count', 'confidence'), [(8, 0.9), (18, 0.95)])
def test_unsupported_finite_sample_confidence_is_not_replaced_with_an_interpolated_quantile(
    count: int, confidence: float
):
    plan, samples, points = _fixture(count, confidence)
    calibration = calibrate_grouped_prediction_intervals(points, samples=samples, plan=plan)
    assert calibration.status == 'insufficient_evidence'
    assert calibration.reason == 'unbounded_finite_sample_quantile'
    assert calibration.half_width is None
    assert calibration.quantile_rank == count + 1


def test_nineteen_groups_support_the_literal_95_percent_boundary():
    plan, samples, points = _fixture(19, 0.95)
    calibration = calibrate_grouped_prediction_intervals(points, samples=samples, plan=plan)
    assert calibration.quantile_rank == 19
    assert calibration.half_width == pytest.approx(0.19)


def test_profile_identifiers_are_namespaced_by_source():
    plan, samples, points = _fixture()
    plan = replace(
        plan,
        grouping='profile',
        training_groups=tuple((group[0], 'profile') for group in plan.training_groups),
        calibration_groups=tuple((group[0], 'profile') for group in plan.calibration_groups),
        test_groups=tuple((group[0], 'profile') for group in plan.test_groups),
    )
    calibration = calibrate_grouped_prediction_intervals(points, samples=samples, plan=plan)
    assert calibration.status == 'calibrated'
    assert len(calibration.scores) == 9


def test_incomplete_calibration_groups_are_not_silently_dropped():
    plan, samples, points = _fixture()
    calibration = calibrate_grouped_prediction_intervals(points[1:], samples=samples, plan=plan)
    assert calibration.reason == 'incomplete_calibration_grid'
    assert calibration.scores[0].maximum_absolute_error is None
    assert calibration.scores[0].available_point_count == 1
    assert calibration.scores[0].expected_point_count == 2


def test_extra_samples_do_not_inflate_the_independent_group_count():
    plan, samples, points = _fixture()
    samples = (*samples, GroupedSample('cal_0', 'two', 'profile'))
    points = (
        *points,
        *(
            RetentionComparison('cal_0', 'two', pressure, 0.7, 0.5, 'profile')
            for pressure in (10, 100)
        ),
    )
    calibration = calibrate_grouped_prediction_intervals(points, samples=samples, plan=plan)
    assert calibration.quantile_rank == 9
    assert len(calibration.scores) == 9
    assert calibration.half_width == pytest.approx(0.2)


def test_training_test_and_calibration_roles_cannot_overlap():
    plan, _, _ = _fixture()
    with pytest.raises(ConformalLeakageError):
        replace(plan, training_groups=(plan.calibration_groups[0],))


def test_calibration_rejects_test_targets_instead_of_filtering_them():
    plan, samples, points = _fixture()
    test_target = RetentionComparison('test', 'one', 10, 0.5, 0.5, 'profile')
    with pytest.raises(ConformalLeakageError):
        calibrate_grouped_prediction_intervals((*points, test_target), samples=samples, plan=plan)


def test_interval_generation_rejects_reused_calibration_groups_and_unvalidated_pressures():
    plan, samples, points = _fixture()
    calibration = calibrate_grouped_prediction_intervals(points, samples=samples, plan=plan)
    with pytest.raises(ConformalLeakageError):
        apply_grouped_prediction_intervals(
            calibration, [ConformalPrediction('cal_0', 'one', 'profile', 10, 0.5)]
        )
    unsupported = apply_grouped_prediction_intervals(
        calibration, [ConformalPrediction('test', 'one', 'profile', 33, 0.5)]
    )[0]
    assert unsupported.reason == 'unsupported_pressure'
    assert unsupported.lower is None
