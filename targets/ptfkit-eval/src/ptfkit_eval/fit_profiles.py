"""Bounded nuisance-parameter refits on an explicit parameter profile grid."""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING, Literal

import numpy as np
from scipy.optimize import least_squares

from .families import evaluate_retention_family, retention_families
from .fit_restarts import PressureIntervalTrial, pressure_interval_trials, pressure_partition_values
from .fitting import RetentionFitError
from .ordered_water import OrderedWaterCoordinates


if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from .fitting import FitParameterRange, RetentionFitResult


def _profile_grid(grid: Sequence[float], fixed_range: FitParameterRange) -> tuple[float, ...]:
    values = tuple(grid)
    if (
        not values
        or any(isinstance(value, bool) or not math.isfinite(value) for value in values)
        or any(value < fixed_range.lower or value > fixed_range.upper for value in values)
        or any(left >= right for left, right in pairwise(values))
    ):
        message = 'Profile grid must be finite, strictly increasing, and inside declared bounds.'
        raise RetentionFitError(message)
    return values


def _additional_profile_starts(
    result: RetentionFitResult, names: tuple[str, ...], nuisance: tuple[int, ...]
) -> list[NDArray[np.float64]]:
    registered = tuple(p.name for p in retention_families()[result.plan.family_id].parameters)
    positions = tuple(registered.index(names[index]) for index in nuisance)
    return [
        np.array([start[index] for index in positions], dtype=np.float64)
        for start in result.plan.additional_starts
    ]


def _profile_coordinates(
    result: RetentionFitResult,
    trial: PressureIntervalTrial,
    names: tuple[str, ...],
    *,
    parameter_name: str,
    fixed_value: float,
    start_index: int,
) -> tuple[OrderedWaterCoordinates | None, NDArray[np.float64]] | None:
    if result.plan.method != 'bounded_trf_ordered_water_multistart_v1':
        return None, trial.initial
    try:
        transform = OrderedWaterCoordinates.create(
            names, trial.lower, trial.upper, fixed={parameter_name: fixed_value}
        )
    except ValueError:
        return None
    start = (
        transform.map_box_draw(trial.initial, trial.lower, trial.upper)
        if 0 < start_index < result.plan.n_starts
        else transform.feasible(trial.initial)
    )
    return transform, start


@dataclass(frozen=True)
class ProfileRefitAttempt:
    """One bounded local nuisance fit; boundary solutions remain visible."""

    start_index: int
    initial_values: tuple[float, ...]
    converged: bool
    evaluations: int
    sum_squared_error: float | None
    values: tuple[float, ...]
    air_entry_interval: tuple[float, float] | None = None


@dataclass(frozen=True)
class ParameterProfilePoint:
    """Grid objective after nuisance refitting, without a coverage claim."""

    fixed_value: float
    sum_squared_error: float | None
    attempts: tuple[ProfileRefitAttempt, ...]


@dataclass(frozen=True)
class RetentionParameterProfile:
    """A numerical profile, not an interval or globally certified optimum."""

    parameter_name: str
    parameter_order: tuple[str, ...]
    baseline_sum_squared_error: float
    points: tuple[ParameterProfilePoint, ...]
    method: str = 'bounded_nuisance_multistart_grid_v1'
    residual_degrees_of_freedom: int | None = None
    parameter_bounds: tuple[float, float] | None = None


@dataclass(frozen=True)
class ProfileOptimalityAssessment:
    """A grid counterexample can refute, but cannot establish, optimality."""

    status: Literal['lower_objective_found', 'no_improvement_detected', 'no_converged_points']
    absolute_tolerance: float
    relative_tolerance: float
    improvement_threshold: float
    best_fixed_value: float | None
    best_sum_squared_error: float | None
    objective_improvement: float | None
    failed_grid_points: int


def assess_profile_optimality(
    profile: RetentionParameterProfile, *, absolute_tolerance: float, relative_tolerance: float
) -> ProfileOptimalityAssessment:
    """Compare converged grid SSE with baseline using explicit error budgets.

    Improvement must strictly exceed atol + rtol * abs(baseline SSE). A negative
    improvement is retained. Missing solves never count as objective evidence.
    A clean assessment is limited to this grid and its local nuisance solves.
    """
    if any(
        isinstance(value, bool) or not math.isfinite(value) or value < 0
        for value in (absolute_tolerance, relative_tolerance)
    ):
        message = 'Profile comparison tolerances must be finite and nonnegative.'
        raise RetentionFitError(message)
    threshold = absolute_tolerance + relative_tolerance * abs(profile.baseline_sum_squared_error)
    valid = [point for point in profile.points if point.sum_squared_error is not None]
    best = (
        min(valid, key=lambda point: (point.sum_squared_error, point.fixed_value))
        if valid
        else None
    )
    objective = None if best is None else best.sum_squared_error
    improvement = None if objective is None else profile.baseline_sum_squared_error - objective
    return ProfileOptimalityAssessment(
        'no_converged_points'
        if improvement is None
        else 'lower_objective_found'
        if improvement > threshold
        else 'no_improvement_detected',
        absolute_tolerance,
        relative_tolerance,
        threshold,
        None if best is None else best.fixed_value,
        objective,
        improvement,
        len(profile.points) - len(valid),
    )


def profile_retention_parameter(
    result: RetentionFitResult, *, parameter_name: str, grid: Sequence[float]
) -> RetentionParameterProfile:
    """Fix one parameter and refit all others within the original fit boxes.

    The first nuisance start is the accepted fit; subsequent starts use the
    original seed and uniform box draws. All grid values use the same starts.
    Failed solves remain explicit. Neither grid spacing nor a confidence
    threshold is inferred, and profile endpoints are never labeled CI limits.
    A declared pressure-partition policy also appends air-entry starts when
    air_entry remains a nuisance parameter; fixed air-entry profiles omit them.
    Ordered-water fits restrict nuisance boxes to the fixed water value's
    feasible region. Infeasible grid points retain no converged objective.
    """
    if result.status != 'fitted':
        message = 'Parameter profiling requires an accepted retention fit.'
        raise RetentionFitError(message)
    ranges = result.plan.parameters
    names = tuple(item.name for item in ranges)
    if parameter_name not in names:
        message = 'Profile parameter must belong to the fitted family.'
        raise RetentionFitError(message)
    fixed_index = names.index(parameter_name)
    fixed_range = ranges[fixed_index]
    values = _profile_grid(grid, fixed_range)
    nuisance = tuple(index for index in range(len(names)) if index != fixed_index)
    lower = np.array([ranges[index].lower for index in nuisance])
    upper = np.array([ranges[index].upper for index in nuisance])
    fitted = {parameter.name: parameter.value for parameter in result.parameters}
    initial = np.array([fitted[names[index]] for index in nuisance])
    rng = np.random.default_rng(result.plan.seed)
    starts = [
        initial,
        *rng.uniform(lower, upper, size=(result.plan.n_starts - 1, len(nuisance))),
        *_additional_profile_starts(result, names, nuisance),
    ]
    if (
        result.plan.restart_policy == 'brooks_corey_pressure_partitions_v1'
        and parameter_name != 'air_entry'
    ):
        index = next(
            index for index, position in enumerate(nuisance) if names[position] == 'air_entry'
        )
        for value in pressure_partition_values(
            (point.suction_kpa for point in result.observations), lower[index], upper[index]
        ):
            start = initial.copy()
            start[index] = value
            starts.append(start)
    trials = [PressureIntervalTrial(start, lower, upper) for start in starts]
    if (
        result.plan.restart_policy == 'brooks_corey_interval_solves_v1'
        and parameter_name != 'air_entry'
    ):
        air_index = next(
            index for index, position in enumerate(nuisance) if names[position] == 'air_entry'
        )
        trials = pressure_interval_trials(
            starts,
            lower,
            upper,
            air_index=air_index,
            pressures=(point.suction_kpa for point in result.observations),
        )
    axis = np.array([point.suction_kpa for point in result.observations])
    observed = np.array([point.water_content for point in result.observations])
    points = []
    for fixed_value in values:
        attempts = []

        def residual(parameters: np.ndarray, fixed: float = fixed_value) -> np.ndarray:
            mapping = {
                names[index]: float(value)
                for index, value in zip(nuisance, parameters, strict=True)
            }
            mapping[parameter_name] = fixed
            return evaluate_retention_family(result.plan.family_id, mapping, axis) - observed

        for start_index, trial in enumerate(trials):
            setup = _profile_coordinates(
                result,
                trial,
                tuple(names[index] for index in nuisance),
                parameter_name=parameter_name,
                fixed_value=fixed_value,
                start_index=start_index,
            )
            if setup is None:
                continue
            transform, start = setup
            optimizer_lower, optimizer_upper = (
                transform.optimizer_bounds()
                if transform is not None
                else (trial.lower, trial.upper)
            )
            solution = least_squares(
                (lambda values, transform=transform: residual(transform.decode(values)))
                if transform is not None
                else residual,
                transform.encode(start) if transform is not None else start,
                bounds=(optimizer_lower, optimizer_upper),
                method='trf',
                x_scale=optimizer_upper - optimizer_lower
                if transform is not None
                else upper - lower,
                max_nfev=result.plan.max_evaluations,
                ftol=result.plan.optimizer_tolerance,
                xtol=result.plan.optimizer_tolerance,
                gtol=result.plan.optimizer_tolerance,
            )
            objective = float(np.dot(solution.fun, solution.fun))
            finite = math.isfinite(objective) and bool(np.all(np.isfinite(solution.x)))
            physical_values = transform.decode(solution.x) if transform is not None else solution.x
            attempts.append(
                ProfileRefitAttempt(
                    start_index,
                    tuple(float(value) for value in start),
                    bool(solution.success) and finite,
                    solution.nfev,
                    objective if finite else None,
                    tuple(float(value) for value in physical_values),
                    trial.air_entry_interval,
                )
            )
        objectives = [
            attempt.sum_squared_error
            for attempt in attempts
            if attempt.converged and attempt.sum_squared_error is not None
        ]
        points.append(
            ParameterProfilePoint(
                fixed_value, min(objectives) if objectives else None, tuple(attempts)
            )
        )
    baseline = math.fsum(
        (point.fitted_value - point.observation.water_content) ** 2 for point in result.points
    )
    return RetentionParameterProfile(
        parameter_name,
        names,
        baseline,
        tuple(points),
        residual_degrees_of_freedom=len(result.observations) - len(names),
        parameter_bounds=(fixed_range.lower, fixed_range.upper),
    )
