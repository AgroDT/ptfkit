from dataclasses import replace

import pytest

from ptfkit_eval import ProfileGridRegion, assess_profile_grid_region
from ptfkit_eval.fit_profiles import ParameterProfilePoint, RetentionParameterProfile


def _profile() -> RetentionParameterProfile:
    return RetentionParameterProfile(
        'theta_s',
        ('theta_s',),
        8,
        tuple(
            ParameterProfilePoint(value, sse, ())
            for value, sse in (
                (0.3, 12),
                (0.4, 20),
                (0.5, 8),
                (0.6, 12),
                (0.8, 24),
            )
        ),
        residual_degrees_of_freedom=1,
        parameter_bounds=(0.3, 0.8),
    )


def _assess(profile: RetentionParameterProfile) -> ProfileGridRegion:
    return assess_profile_grid_region(
        profile, confidence_level=0.5, absolute_tolerance=0, relative_tolerance=0
    )


def test_f_grid_region_uses_single_parameter_df_and_preserves_disconnected_runs():
    # F(1,1) has median 1 by reciprocal symmetry, so SSE threshold is 8*(1+1)=16.
    region = _assess(_profile())
    assert region.status == 'assessed'
    assert region.objective_threshold == pytest.approx(16)
    assert region.accepted_runs == ((0.3,), (0.5, 0.6))
    assert region.reaches_lower_bound
    assert not region.reaches_upper_bound


@pytest.mark.parametrize(
    ('change', 'reason'),
    [
        ({'residual_degrees_of_freedom': None}, 'missing_profile_metadata'),
        ({'residual_degrees_of_freedom': 0}, 'invalid_residual_variance'),
        ({'baseline_sum_squared_error': 0}, 'invalid_residual_variance'),
        ({'parameter_bounds': (0.2, 0.8)}, 'incomplete_box_grid'),
        ({'points': ()}, 'incomplete_grid'),
    ],
)
def test_grid_region_withholds_incomplete_or_degenerate_inference(change: dict, reason: str):
    region = _assess(replace(_profile(), **change))
    assert region.status == 'unavailable'
    assert region.reason == reason
    assert region.objective_threshold is None
    assert region.accepted_runs == ()


def test_grid_region_withholds_missing_solves_and_improved_baseline():
    profile = _profile()
    for objective, reason in ((None, 'incomplete_grid'), (7, 'lower_objective_found')):
        points = (replace(profile.points[0], sum_squared_error=objective), *profile.points[1:])
        assert _assess(replace(profile, points=points)).reason == reason
