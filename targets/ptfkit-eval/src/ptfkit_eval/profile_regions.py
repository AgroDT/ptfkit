"""Approximate F-threshold regions on explicit bounded profile grids."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from scipy.stats import f

from .fit_profiles import assess_profile_optimality
from .fitting import RetentionFitError


if TYPE_CHECKING:
    from .fit_profiles import RetentionParameterProfile


@dataclass(frozen=True)
class ProfileGridRegion:
    """Accepted grid nodes are not interpolated confidence interval endpoints."""

    status: Literal['assessed', 'unavailable']
    reason: str | None
    confidence_level: float
    objective_threshold: float | None
    accepted_runs: tuple[tuple[float, ...], ...]
    reaches_lower_bound: bool
    reaches_upper_bound: bool
    method: str = 'approximate_profile_f_grid_v1'


def assess_profile_grid_region(
    profile: RetentionParameterProfile,
    *,
    confidence_level: float,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> ProfileGridRegion:
    """Classify nodes using SSEmin * (1 + F(1, n-p; level)/(n-p)).

    This is approximate nonlinear regression inference conditional on the
    family, declared boxes, iid Gaussian homoscedastic residuals, and adequate
    optimization. No simultaneous coverage or constrained-boundary calibration
    is claimed. Missing solves, an improved baseline, or an incomplete box grid
    withhold the assessment. Disconnected node runs remain separate.
    """
    if (
        isinstance(confidence_level, bool)
        or not math.isfinite(confidence_level)
        or not 0 < confidence_level < 1
    ):
        message = 'Profile confidence level must be finite and strictly between zero and one.'
        raise RetentionFitError(message)
    optimality = assess_profile_optimality(
        profile,
        absolute_tolerance=absolute_tolerance,
        relative_tolerance=relative_tolerance,
    )
    df, bounds = profile.residual_degrees_of_freedom, profile.parameter_bounds
    baseline = profile.baseline_sum_squared_error
    reason = (
        'missing_profile_metadata'
        if df is None or bounds is None
        else 'invalid_residual_variance'
        if isinstance(df, bool) or df <= 0 or not math.isfinite(baseline) or baseline <= 0
        else 'lower_objective_found'
        if optimality.status == 'lower_objective_found'
        else 'incomplete_grid'
        if not profile.points or optimality.failed_grid_points
        else 'incomplete_box_grid'
        if (profile.points[0].fixed_value, profile.points[-1].fixed_value) != bounds
        else None
    )
    if reason is not None:
        return ProfileGridRegion(
            'unavailable',
            reason,
            confidence_level,
            None,
            (),
            reaches_lower_bound=False,
            reaches_upper_bound=False,
        )
    threshold = baseline * (1 + float(f.ppf(confidence_level, 1, df)) / cast('int', df))
    if not math.isfinite(threshold):
        return ProfileGridRegion(
            'unavailable',
            'nonfinite_threshold',
            confidence_level,
            None,
            (),
            reaches_lower_bound=False,
            reaches_upper_bound=False,
        )
    runs: list[list[float]] = []
    current: list[float] = []
    for point in profile.points:
        if point.sum_squared_error is not None and point.sum_squared_error <= threshold:
            current.append(point.fixed_value)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    return ProfileGridRegion(
        'assessed',
        None,
        confidence_level,
        threshold,
        tuple(tuple(run) for run in runs),
        bool(runs and runs[0][0] == profile.points[0].fixed_value),
        bool(runs and runs[-1][-1] == profile.points[-1].fixed_value),
    )
