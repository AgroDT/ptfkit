"""Bounded deterministic retention fitting with explicit failure and uncertainty contracts."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np
from scipy.optimize import least_squares
from scipy.stats import t as student_t

from .adapters import CLAPP1978_MAXIMUM_B
from .families import (
    RetentionFamily,
    evaluate_retention_family,
    retention_families,
)
from .fit_restarts import PressureIntervalTrial, pressure_interval_trials, pressure_partition_values
from .ordered_water import WATER_SEPARATION, OrderedWaterCoordinates
from .quality import RetentionSeriesPoint, diagnose_retention_series


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from numpy.typing import NDArray

    from .contracts import TargetSpec


class RetentionFitError(ValueError):
    """Raised when a fit plan or its canonical observations are invalid."""


RestartPolicy = Literal[
    'seeded_box_v1', 'brooks_corey_pressure_partitions_v1', 'brooks_corey_interval_solves_v1'
]

FitMethod = Literal['bounded_trf_uniform_multistart_v1', 'bounded_trf_ordered_water_multistart_v1']


@dataclass(frozen=True)
class FitParameterRange:
    """Explicit finite bounds and an interior initial value in the registry unit."""

    name: str
    lower: float
    upper: float
    initial: float


@dataclass(frozen=True, kw_only=True)
class RetentionFitPlan:
    """Fully registered local fitting policy; bounds are never inferred from data.

    The default uses nonoverlapping water boxes. The optional ordered-water
    method maps a residual-water fraction conditionally on saturation, allowing
    overlapping physical boxes with a numerical separation of 1e-10.
    Parameter uncertainty assumes local linearity and independent homoscedastic
    observation errors. It is conditional on the declared family and fit policy.
    The optional Brooks--Corey restart policy appends pressure-knot and geometric
    partition-midpoint starts to the n_starts original seeded box starts.
    Additional starts are explicit physical vectors in registered family
    parameter order. They append to, rather than replace, the seeded starts.
    """

    family_id: str
    target: TargetSpec
    parameters: tuple[FitParameterRange, ...]
    seed: int
    minimum_log10_span: float
    n_starts: int = 3
    restart_policy: Literal[
        'seeded_box_v1', 'brooks_corey_pressure_partitions_v1', 'brooks_corey_interval_solves_v1'
    ] = 'seeded_box_v1'
    max_evaluations: int = 2000
    optimizer_tolerance: float = 1e-10
    boundary_tolerance: float = 1e-6
    rank_tolerance: float = 1e-10
    maximum_condition_number: float = 1e10
    objective_agreement_tolerance: float = 1e-10
    parameter_agreement_tolerance: float = 1e-3
    confidence_level: float = 0.95
    method: FitMethod = 'bounded_trf_uniform_multistart_v1'
    uncertainty_method: Literal['local_linear_iid_student_t_v1'] = 'local_linear_iid_student_t_v1'
    additional_starts: tuple[tuple[float, ...], ...] = ()

    def __post_init__(self) -> None:
        """Validate scientific bounds and every numerical/evidence choice upfront."""
        family = retention_families().get(self.family_id)
        if family is None:
            message = f'Unknown retention fitting family: {self.family_id!r}.'
            raise RetentionFitError(message)
        _validate_plan(self, family)


@dataclass(frozen=True)
class ApproximationInterval:
    """A local conditional interval whose interpretation is given by its owner field."""

    lower: float
    upper: float


@dataclass(frozen=True)
class ApproximationParameter:
    """A family-specific fitted value and optional local parameter uncertainty."""

    name: str
    unit: str
    value: float
    standard_error: float | None
    parameter_interval: ApproximationInterval | None


@dataclass(frozen=True)
class ApproximationCurvePoint:
    """Fit at one observed pressure, separate from a PTF prediction error."""

    observation: RetentionSeriesPoint
    fitted_value: float
    mean_curve_confidence_interval: ApproximationInterval
    conditional_prediction_interval: ApproximationInterval


@dataclass(frozen=True)
class RetentionFitAttempt:
    """One explicit start, convergence status, objective, and parameter outcome."""

    start_index: int
    initial_values: tuple[float, ...]
    converged: bool
    optimizer_status: int | None
    evaluations: int
    sum_squared_error: float | None
    values: tuple[float, ...]
    error: str | None
    air_entry_interval: tuple[float, float] | None = None


@dataclass(frozen=True)
class FitIdentifiability:
    """Rank/conditioning in bounded parameter coordinates and competing-start checks."""

    jacobian_rank: int
    parameter_count: int
    scaled_condition_number: float | None
    boundary_parameters: tuple[str, ...]
    competing_starts: tuple[int, ...]


@dataclass(frozen=True)
class RetentionFitResult:
    """An accepted family fit or explicit failure; no other family is substituted."""

    plan: RetentionFitPlan
    observations: tuple[RetentionSeriesPoint, ...]
    status: Literal['fitted', 'failed']
    reason: str | None
    attempts: tuple[RetentionFitAttempt, ...]
    identifiability: FitIdentifiability | None
    parameters: tuple[ApproximationParameter, ...]
    points: tuple[ApproximationCurvePoint, ...]
    residual_variance: float | None
    parameter_covariance: tuple[tuple[float, ...], ...] | None


@dataclass(frozen=True)
class _FitContext:
    plan: RetentionFitPlan
    family: RetentionFamily
    ranges: tuple[FitParameterRange, ...]
    observations: tuple[RetentionSeriesPoint, ...]
    axis: NDArray[np.float64]
    observed: NDArray[np.float64]
    lower: NDArray[np.float64]
    upper: NDArray[np.float64]


@dataclass(frozen=True)
class _Solution:
    start_index: int
    values: NDArray[np.float64]
    jacobian: NDArray[np.float64]
    residuals: NDArray[np.float64]
    objective: float


@dataclass(frozen=True)
class _SolutionAnalysis:
    solution: _Solution
    diagnostic: FitIdentifiability
    singular_values: NDArray[np.float64]
    right_vectors: NDArray[np.float64]


def fit_retention_family(
    observations: Iterable[RetentionSeriesPoint],
    *,
    plan: RetentionFitPlan,
) -> RetentionFitResult:
    """Fit one family to one reviewed sample curve, independent of PTF assessment.

    Each observation receives equal objective weight. A supplied initial start
    is followed by seeded uniform bounded starts (log-uniform for declared scale
    parameters). Boundary, rank-deficient, ill-conditioned, or competing solutions
    are rejected. Local Student-t parameter/curve/prediction intervals assume
    independent homoscedastic residuals and do not estimate PTF prediction error.
    Explicit pressure-partition restarts preserve all original starts and bounds.
    """
    points = tuple(sorted(observations, key=lambda point: point.suction_kpa))
    diagnose_retention_series(points)
    if any(not 0 <= point.water_content <= 1 for point in points):
        message = 'Retention fitting requires physically valid observed volume fractions.'
        raise RetentionFitError(message)
    family = retention_families()[plan.family_id]
    if len(points) < family.minimum_points:
        return _failed(plan, points, 'insufficient_observations')
    positive = [point.suction_kpa for point in points if point.suction_kpa > 0]
    if (
        not positive
        or math.log10(max(positive)) - math.log10(min(positive)) < plan.minimum_log10_span
    ):
        return _failed(plan, points, 'insufficient_pressure_span')
    ranges = tuple(
        next(item for item in plan.parameters if item.name == parameter.name)
        for parameter in family.parameters
    )
    context = _FitContext(
        plan,
        family,
        ranges,
        points,
        np.array([point.suction_kpa for point in points], dtype=np.float64),
        np.array([point.water_content for point in points], dtype=np.float64),
        np.array([item.lower for item in ranges], dtype=np.float64),
        np.array([item.upper for item in ranges], dtype=np.float64),
    )
    attempts, solutions = _solve_starts(context)
    if not solutions:
        return _failed(plan, points, 'optimizer_failed', attempts)
    best = min(solutions, key=lambda solution: (solution.objective, solution.start_index))
    widths = context.upper - context.lower
    scaled_jacobian = best.jacobian * widths
    _, singular, right = np.linalg.svd(scaled_jacobian, full_matrices=False)
    singular = np.asarray(singular, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    rank = int(np.count_nonzero(singular > plan.rank_tolerance * singular[0]))
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else None
    if condition is not None and not math.isfinite(condition):
        condition = None
    boundary = tuple(
        item.name
        for index, item in enumerate(ranges)
        if min(best.values[index] - item.lower, item.upper - best.values[index])
        <= plan.boundary_tolerance * widths[index]
    )
    if plan.method == 'bounded_trf_ordered_water_multistart_v1':
        estimates = dict(zip((item.name for item in ranges), best.values, strict=True))
        if estimates['theta_s'] - estimates['theta_r'] <= (
            WATER_SEPARATION + plan.boundary_tolerance * max(widths)
        ):
            boundary += ('theta_s_minus_theta_r',)
        residual_upper = next(item.upper for item in ranges if item.name == 'theta_r')
        if abs(estimates['theta_s'] - WATER_SEPARATION - residual_upper) <= (
            4 * np.cbrt(np.finfo(float).eps)
        ):
            diagnostic = FitIdentifiability(rank, len(ranges), condition, boundary, ())
            return _failed(plan, points, 'water_coordinate_kink', attempts, diagnostic)
    competing = tuple(
        solution.start_index
        for solution in solutions
        if abs(solution.objective - best.objective)
        <= plan.objective_agreement_tolerance * max(1.0, best.objective)
        and np.max(np.abs((solution.values - best.values) / widths))
        > plan.parameter_agreement_tolerance
    )
    diagnostic = FitIdentifiability(rank, len(ranges), condition, boundary, competing)
    reason = (
        'boundary_solution'
        if boundary
        else 'nonidentifiable'
        if rank < len(ranges) or condition is None or condition > plan.maximum_condition_number
        else 'competing_solutions'
        if competing
        else None
    )
    if reason is not None:
        return _failed(plan, points, reason, attempts, diagnostic)
    return _accepted_fit(context, _SolutionAnalysis(best, diagnostic, singular, right), attempts)


def _accepted_fit(
    context: _FitContext,
    analysis: _SolutionAnalysis,
    attempts: tuple[RetentionFitAttempt, ...],
) -> RetentionFitResult:
    plan, points, family, ranges = (
        context.plan,
        context.observations,
        context.family,
        context.ranges,
    )
    best, diagnostic = analysis.solution, analysis.diagnostic
    singular, right = analysis.singular_values, analysis.right_vectors
    widths = context.upper - context.lower
    variance = best.objective / (len(points) - len(ranges))
    root_covariance = (right.T / singular) * math.sqrt(variance) * widths[:, None]
    covariance = root_covariance @ root_covariance.T
    standard_errors = np.linalg.norm(root_covariance, axis=1)
    curve_errors = np.linalg.norm(best.jacobian @ root_covariance, axis=1)
    critical = float(student_t.isf((1 - plan.confidence_level) / 2, len(points) - len(ranges)))
    estimates = tuple(
        ApproximationParameter(
            parameter.name,
            parameter.unit,
            float(value),
            float(error),
            ApproximationInterval(float(value - critical * error), float(value + critical * error)),
        )
        for parameter, value, error in zip(
            family.parameters, best.values, standard_errors, strict=True
        )
    )
    fitted = context.observed + best.residuals
    if not np.all(np.isfinite(covariance)):
        return _failed(plan, points, 'nonfinite_uncertainty', attempts, diagnostic)
    if np.any(fitted < 0) or np.any(fitted > 1) or np.any(np.diff(fitted) > 0):
        return _failed(plan, points, 'nonphysical_solution', attempts, diagnostic)
    curve = tuple(
        ApproximationCurvePoint(
            point,
            float(value),
            ApproximationInterval(float(value - critical * error), float(value + critical * error)),
            ApproximationInterval(
                float(value - critical * math.sqrt(error**2 + variance)),
                float(value + critical * math.sqrt(error**2 + variance)),
            ),
        )
        for point, value, error in zip(points, fitted, curve_errors, strict=True)
    )
    return RetentionFitResult(
        plan,
        points,
        'fitted',
        None,
        attempts,
        diagnostic,
        estimates,
        curve,
        variance,
        tuple(tuple(float(value) for value in row) for row in covariance),
    )


def evaluate_retention_fit(
    result: RetentionFitResult, suction_kpa: Sequence[float]
) -> tuple[float, ...]:
    """Evaluate an accepted approximation only within its observed pressure extent."""
    if result.status != 'fitted':
        message = 'Cannot evaluate a failed retention approximation.'
        raise RetentionFitError(message)
    if any(
        value < result.observations[0].suction_kpa or value > result.observations[-1].suction_kpa
        for value in suction_kpa
    ):
        message = 'Retention approximation extrapolation is disabled.'
        raise RetentionFitError(message)
    values = evaluate_retention_family(
        result.plan.family_id,
        {parameter.name: parameter.value for parameter in result.parameters},
        suction_kpa,
    )
    return tuple(float(value) for value in values)


def _solve_starts(context: _FitContext) -> tuple[tuple[RetentionFitAttempt, ...], list[_Solution]]:
    generator = np.random.default_rng(context.plan.seed)
    initial = np.array([item.initial for item in context.ranges], dtype=np.float64)
    starts = [initial]
    for _ in range(context.plan.n_starts - 1):
        values = []
        for parameter, bounds in zip(context.family.parameters, context.ranges, strict=True):
            fraction = float(generator.random())
            values.append(
                math.exp(
                    math.log(bounds.lower)
                    + fraction * (math.log(bounds.upper) - math.log(bounds.lower))
                )
                if parameter.logarithmic_restarts
                else bounds.lower + fraction * (bounds.upper - bounds.lower)
            )
        starts.append(np.array(values, dtype=np.float64))
    coordinates = None
    if context.plan.method == 'bounded_trf_ordered_water_multistart_v1':
        coordinates = OrderedWaterCoordinates.create(
            tuple(item.name for item in context.ranges), context.lower, context.upper
        )
        starts = [
            starts[0],
            *(
                coordinates.map_box_draw(start, context.lower, context.upper)
                for start in starts[1:]
            ),
        ]
    starts.extend(np.array(start, dtype=np.float64) for start in context.plan.additional_starts)
    if context.plan.restart_policy == 'brooks_corey_pressure_partitions_v1':
        index = next(
            index for index, bounds in enumerate(context.ranges) if bounds.name == 'air_entry'
        )
        for value in pressure_partition_values(
            context.axis, context.lower[index], context.upper[index]
        ):
            start = initial.copy()
            start[index] = value
            starts.append(start)
    trials = [PressureIntervalTrial(start, context.lower, context.upper) for start in starts]
    if context.plan.restart_policy == 'brooks_corey_interval_solves_v1':
        air_index = next(
            index for index, bounds in enumerate(context.ranges) if bounds.name == 'air_entry'
        )
        trials = pressure_interval_trials(
            starts, context.lower, context.upper, air_index=air_index, pressures=context.axis
        )
    attempts: list[RetentionFitAttempt] = []
    solutions: list[_Solution] = []
    for index, trial in enumerate(trials):
        start = trial.initial
        try:
            transform = (
                OrderedWaterCoordinates.create(
                    tuple(item.name for item in context.ranges), trial.lower, trial.upper
                )
                if coordinates is not None
                else None
            )
            optimized = least_squares(
                (lambda values, transform=transform: _residuals(transform.decode(values), context))
                if transform is not None
                else _residuals,
                transform.encode(start) if transform is not None else start,
                args=() if transform is not None else (context,),
                bounds=transform.optimizer_bounds()
                if transform is not None
                else (trial.lower, trial.upper),
                method='trf',
                jac='3-point',
                x_scale='jac',
                loss='linear',
                ftol=context.plan.optimizer_tolerance,
                xtol=context.plan.optimizer_tolerance,
                gtol=context.plan.optimizer_tolerance,
                max_nfev=context.plan.max_evaluations,
            )
            objective = float(optimized.fun @ optimized.fun)
            physical_values = (
                transform.decode(optimized.x) if transform is not None else optimized.x
            )
            physical_jacobian = (
                transform.physical_jacobian(optimized.x, optimized.jac)
                if transform is not None
                else optimized.jac
            )
            converged = (
                bool(optimized.success)
                and math.isfinite(objective)
                and bool(np.all(np.isfinite(physical_jacobian)))
            )
            attempts.append(
                RetentionFitAttempt(
                    index,
                    tuple(float(value) for value in start),
                    converged,
                    int(optimized.status),
                    int(optimized.nfev),
                    objective if math.isfinite(objective) else None,
                    tuple(float(value) for value in physical_values),
                    None,
                    trial.air_entry_interval,
                )
            )
            if converged:
                solutions.append(
                    _Solution(
                        index,
                        np.asarray(physical_values, dtype=np.float64),
                        np.asarray(physical_jacobian, dtype=np.float64),
                        np.asarray(optimized.fun, dtype=np.float64),
                        objective,
                    )
                )
        except (ValueError, ArithmeticError) as error:
            attempts.append(
                RetentionFitAttempt(
                    start_index=index,
                    initial_values=tuple(float(value) for value in start),
                    converged=False,
                    optimizer_status=None,
                    evaluations=0,
                    sum_squared_error=None,
                    values=(),
                    error=f'{type(error).__name__}: {error}',
                    air_entry_interval=trial.air_entry_interval,
                )
            )
    return tuple(attempts), solutions


def _residuals(values: NDArray[np.float64], context: _FitContext) -> NDArray[np.float64]:
    parameters = {
        parameter.name: float(value)
        for parameter, value in zip(context.family.parameters, values, strict=True)
    }
    with np.errstate(over='raise', invalid='raise', divide='raise'):
        prediction = evaluate_retention_family(context.plan.family_id, parameters, context.axis)
    return np.asarray(prediction - context.observed, dtype=np.float64)


def _failed(
    plan: RetentionFitPlan,
    points: tuple[RetentionSeriesPoint, ...],
    reason: str,
    attempts: tuple[RetentionFitAttempt, ...] = (),
    diagnostic: FitIdentifiability | None = None,
) -> RetentionFitResult:
    return RetentionFitResult(
        plan, points, 'failed', reason, attempts, diagnostic, (), (), None, None
    )


def _validate_plan(plan: RetentionFitPlan, family: RetentionFamily) -> None:
    if plan.restart_policy not in (
        'seeded_box_v1',
        'brooks_corey_pressure_partitions_v1',
        'brooks_corey_interval_solves_v1',
    ) or (plan.restart_policy != 'seeded_box_v1' and plan.family_id != 'brooks_corey_v1'):
        message = 'Unsupported restart policy for the declared retention family.'
        raise RetentionFitError(message)
    if (
        plan.target.quantity != family.target_quantity
        or plan.target.unit != family.target_unit
        or (
            plan.target.denominator_basis != family.denominator_basis
            or not plan.target.material_basis.strip()
        )
    ):
        message = (
            'Fit target must declare canonical volumetric water content and its material basis.'
        )
        raise RetentionFitError(message)
    _validate_numerical_policy(plan)
    bounds = _parameter_boxes(plan, family)
    _validate_physical_ranges(plan, bounds)
    _validate_additional_starts(plan, family, bounds)
    if (
        plan.method
        not in ('bounded_trf_uniform_multistart_v1', 'bounded_trf_ordered_water_multistart_v1')
        or plan.uncertainty_method != 'local_linear_iid_student_t_v1'
    ):
        message = 'Unsupported fitting or uncertainty policy.'
        raise RetentionFitError(message)


def _validate_additional_starts(
    plan: RetentionFitPlan, family: RetentionFamily, bounds: Mapping[str, FitParameterRange]
) -> None:
    names = tuple(parameter.name for parameter in family.parameters)
    if not isinstance(plan.additional_starts, tuple) or any(
        not isinstance(start, tuple) or len(start) != len(names) for start in plan.additional_starts
    ):
        message = (
            'Additional starts must be immutable vectors in registered family parameter order.'
        )
        raise RetentionFitError(message)
    for start in plan.additional_starts:
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not bounds[name].lower <= value <= bounds[name].upper
            for name, value in zip(names, start, strict=True)
        ):
            message = (
                'Additional starts must be finite physical values inside their declared boxes.'
            )
            raise RetentionFitError(message)
        mapping = dict(zip(names, start, strict=True))
        if plan.method == 'bounded_trf_ordered_water_multistart_v1' and (
            mapping['theta_r'] + WATER_SEPARATION >= mapping['theta_s']
        ):
            message = 'Additional ordered-water starts must preserve physical water separation.'
            raise RetentionFitError(message)


def _validate_numerical_policy(plan: RetentionFitPlan) -> None:
    if isinstance(plan.seed, bool) or not isinstance(plan.seed, int) or plan.seed < 0:
        message = 'Fit seed must be an explicit nonnegative integer.'
        raise RetentionFitError(message)
    for name in ('n_starts', 'max_evaluations'):
        value = getattr(plan, name)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            message = f'{name} must be a positive integer.'
            raise RetentionFitError(message)
    for name in (
        'minimum_log10_span',
        'optimizer_tolerance',
        'boundary_tolerance',
        'rank_tolerance',
        'maximum_condition_number',
        'objective_agreement_tolerance',
        'parameter_agreement_tolerance',
    ):
        value = getattr(plan, name)
        if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            message = f'{name} must be finite and positive.'
            raise RetentionFitError(message)
    if not np.finfo(float).eps < plan.optimizer_tolerance < 1 or plan.maximum_condition_number < 1:
        message = (
            'Optimizer tolerance and maximum condition number are outside their supported ranges.'
        )
        raise RetentionFitError(message)
    if not 0 < plan.confidence_level < 1 or isinstance(plan.confidence_level, bool):
        message = 'Fit confidence level must be strictly between zero and one.'
        raise RetentionFitError(message)


def _parameter_boxes(
    plan: RetentionFitPlan, family: RetentionFamily
) -> dict[str, FitParameterRange]:
    bounds = {item.name: item for item in plan.parameters}
    if len(bounds) != len(plan.parameters) or set(bounds) != {
        parameter.name for parameter in family.parameters
    }:
        message = 'Parameter boxes must cover each registered family parameter exactly once.'
        raise RetentionFitError(message)
    for item in plan.parameters:
        if (
            any(
                not math.isfinite(value) or isinstance(value, bool)
                for value in (item.lower, item.upper, item.initial)
            )
            or not item.lower < item.initial < item.upper
        ):
            message = 'Parameter boxes require finite ordered bounds and an interior initial value.'
            raise RetentionFitError(message)
    return bounds


def _validate_physical_ranges(
    plan: RetentionFitPlan, bounds: Mapping[str, FitParameterRange]
) -> None:
    theta_s = bounds['theta_s']
    ordered = plan.method == 'bounded_trf_ordered_water_multistart_v1'
    if ordered and (
        'theta_r' not in bounds
        or bounds['theta_r'].upper > 1
        or bounds['theta_r'].lower + WATER_SEPARATION >= theta_s.lower
        or bounds['theta_r'].initial + WATER_SEPARATION >= theta_s.initial
    ):
        message = 'Ordered water fitting requires feasible water bounds and initial values.'
        raise RetentionFitError(message)
    if (
        theta_s.lower < 0
        or theta_s.upper > 1
        or (
            'theta_r' in bounds
            and (
                bounds['theta_r'].lower < 0
                or (not ordered and bounds['theta_r'].upper >= theta_s.lower)
            )
        )
    ):
        message = 'Fitting requires physical, nonoverlapping theta_r and theta_s boxes.'
        raise RetentionFitError(message)
    for name, item in bounds.items():
        if name not in ('theta_r', 'theta_s') and item.lower <= (
            1 if name == 'n' and plan.family_id == 'van_genuchten_mualem_v1' else 0
        ):
            message = 'Shape and suction-scale bounds violate the registered physical convention.'
            raise RetentionFitError(message)
    if plan.family_id == 'clapp1978_gradual_air_entry_v1' and (
        theta_s.lower <= 0 or theta_s.upper >= 1 or bounds['b'].upper >= CLAPP1978_MAXIMUM_B
    ):
        message = (
            'Clapp fitting requires 0 < theta_s < 1 and 0 < b < 11.5 for its parabolic branch.'
        )
        raise RetentionFitError(message)
