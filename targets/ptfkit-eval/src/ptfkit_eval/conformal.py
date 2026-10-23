"""Whole-group split-conformal prediction intervals for a predeclared fixed candidate."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from typing import TYPE_CHECKING, Literal

from .metrics import summarize_retention_errors


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .contracts import TargetSpec
    from .folds import GroupedSample, GroupKey, SampleKey
    from .metrics import RetentionComparison


_MINIMUM_CALIBRATION_GROUPS = 2
_GROUP_KEY_SIZE = 2


class ConformalPlanError(ValueError):
    """Raised when a prediction-interval registration or its identities are invalid."""


class ConformalLeakageError(ConformalPlanError):
    """Raised when training, calibration, or test roles overlap or are misused."""


@dataclass(frozen=True, kw_only=True)
class GroupedConformalPlan:
    """Explicit disjoint roles and a fixed simultaneous pressure grid.

    Scores are maximum absolute residuals over each whole calibration group,
    including all declared samples and grid points. Coverage interpretation
    requires exchangeability of whole groups under a fixed prediction rule and
    observation design. It is not conditional coverage for every soil type.
    """

    candidate_id: str
    protocol_id: str
    target: TargetSpec
    calibration_groups: tuple[GroupKey, ...]
    training_groups: tuple[GroupKey, ...]
    test_groups: tuple[GroupKey, ...]
    pressure_grid_kpa: tuple[float, ...]
    confidence_level: float = 0.95
    minimum_calibration_groups: int = 2
    grouping: Literal['source', 'profile'] = 'source'
    method: Literal['fixed_group_max_split_conformal_v1'] = 'fixed_group_max_split_conformal_v1'

    def __post_init__(self) -> None:
        """Reject unsupported policies and leakage before any scores are inspected."""
        if (
            not self.candidate_id.strip()
            or not self.protocol_id.strip()
            or self.grouping not in ('source', 'profile')
            or self.method != 'fixed_group_max_split_conformal_v1'
        ):
            message = 'Conformal prediction requires identifiers and a supported grouping/method.'
            raise ConformalPlanError(message)
        if (
            self.target.quantity != 'volumetric_water_content'
            or self.target.unit != 'volume_fraction'
            or self.target.denominator_basis != 'bulk_volume'
            or not self.target.material_basis.strip()
        ):
            message = (
                'Conformal retention intervals require canonical volumetric target units and basis.'
            )
            raise ConformalPlanError(message)
        if (
            isinstance(self.confidence_level, bool)
            or not math.isfinite(self.confidence_level)
            or not 0 < self.confidence_level < 1
        ):
            message = 'Conformal confidence must be finite and strictly between zero and one.'
            raise ConformalPlanError(message)
        if (
            isinstance(self.minimum_calibration_groups, bool)
            or not isinstance(self.minimum_calibration_groups, int)
            or self.minimum_calibration_groups < _MINIMUM_CALIBRATION_GROUPS
        ):
            message = 'At least two independent calibration groups must be required.'
            raise ConformalPlanError(message)
        grid = self.pressure_grid_kpa
        if (
            not grid
            or len(set(grid)) != len(grid)
            or any(
                isinstance(value, bool) or not math.isfinite(value) or value < 0 for value in grid
            )
        ):
            message = 'Conformal pressure grids require distinct finite nonnegative kPa values.'
            raise ConformalPlanError(message)
        _validate_roles(self)


@dataclass(frozen=True)
class GroupResidualScore:
    """A complete whole-group residual score, or its missing-grid evidence."""

    group_id: GroupKey
    sample_count: int
    expected_point_count: int
    available_point_count: int
    maximum_absolute_error: float | None


@dataclass(frozen=True)
class GroupedConformalCalibration:
    """Retained calibration scores and the exact finite-sample rank decision."""

    plan: GroupedConformalPlan
    samples: tuple[GroupedSample, ...]
    scores: tuple[GroupResidualScore, ...]
    quantile_rank: int | None
    half_width: float | None
    reason: (
        Literal[
            'incomplete_calibration_grid',
            'too_few_calibration_groups',
            'unbounded_finite_sample_quantile',
        ]
        | None
    )

    @property
    def status(self) -> Literal['calibrated', 'insufficient_evidence']:
        """Never encode an unsupported infinite interval as a finite estimate."""
        return 'calibrated' if self.half_width is not None else 'insufficient_evidence'


@dataclass(frozen=True)
class ConformalPrediction:
    """An unlabelled test prediction: observed test targets are deliberately absent."""

    source_id: str
    sample_id: str
    profile_id: str | None
    suction_kpa: float
    predicted: float


@dataclass(frozen=True)
class ConformalPredictionInterval:
    """A prediction interval or a point-specific unsupported-evidence reason."""

    prediction: ConformalPrediction
    lower: float | None
    upper: float | None
    reason: str | None

    @property
    def status(self) -> Literal['computed', 'insufficient_evidence']:
        """Distinguish prediction bounds from missing or unsupported calibration."""
        return 'computed' if self.lower is not None else 'insufficient_evidence'


def calibrate_grouped_prediction_intervals(
    comparisons: Iterable[RetentionComparison],
    *,
    samples: Iterable[GroupedSample],
    plan: GroupedConformalPlan,
) -> GroupedConformalCalibration:
    """Calibrate a fixed rule using only complete declared calibration groups.

    The finite rank is ceil((G+1)*confidence); ranks exceeding G require an
    unbounded interval and are reported as insufficient evidence. Whole-group
    maximum scores preserve cluster membership and simultaneous grid scope.
    Training/test targets are rejected rather than filtered out implicitly.
    """
    roster, groups = _roster(samples, plan)
    points = tuple(comparisons)
    if points:
        summarize_retention_errors(points)
    index: dict[tuple[str, str, float], float] = {}
    sample_index = {(sample.source_id, sample.sample_id): sample for sample in roster}
    for point in points:
        key = (point.source_id, point.sample_id)
        sample = sample_index.get(key)
        if sample is None or sample.profile_id != point.profile_id:
            message = 'Conformal residuals must match the declared sample/profile roster.'
            raise ConformalPlanError(message)
        if _group(sample, plan) not in plan.calibration_groups:
            message = 'Training, test, or undeclared groups cannot supply calibration residuals.'
            raise ConformalLeakageError(message)
        if point.suction_kpa not in plan.pressure_grid_kpa:
            message = 'Calibration residuals must use the exact registered pressure grid.'
            raise ConformalPlanError(message)
        index[point.source_id, point.sample_id, point.suction_kpa] = abs(
            point.predicted - point.observed
        )
    scores: list[GroupResidualScore] = []
    for group_id in sorted(plan.calibration_groups):
        group_samples = groups[group_id]
        expected = [
            (source, sample, pressure)
            for source, sample in group_samples
            for pressure in plan.pressure_grid_kpa
        ]
        available = [index[key] for key in expected if key in index]
        scores.append(
            GroupResidualScore(
                group_id,
                len(group_samples),
                len(expected),
                len(available),
                max(available) if len(available) == len(expected) else None,
            )
        )
    if any(score.maximum_absolute_error is None for score in scores):
        return GroupedConformalCalibration(
            plan, roster, tuple(scores), None, None, 'incomplete_calibration_grid'
        )
    if len(scores) < plan.minimum_calibration_groups:
        return GroupedConformalCalibration(
            plan, roster, tuple(scores), None, None, 'too_few_calibration_groups'
        )
    rank = int(
        (Decimal(len(scores) + 1) * Decimal(str(plan.confidence_level))).to_integral_value(
            rounding=ROUND_CEILING
        )
    )
    if rank > len(scores):
        return GroupedConformalCalibration(
            plan, roster, tuple(scores), rank, None, 'unbounded_finite_sample_quantile'
        )
    values = sorted(
        float(score.maximum_absolute_error)
        for score in scores
        if score.maximum_absolute_error is not None
    )
    return GroupedConformalCalibration(plan, roster, tuple(scores), rank, values[rank - 1], None)


def apply_grouped_prediction_intervals(
    calibration: GroupedConformalCalibration,
    predictions: Iterable[ConformalPrediction],
) -> tuple[ConformalPredictionInterval, ...]:
    """Generate test intervals without accepting or inspecting observed test values."""
    plan = calibration.plan
    roster = {(sample.source_id, sample.sample_id): sample for sample in calibration.samples}
    result: list[ConformalPredictionInterval] = []
    seen: set[tuple[str, str, float]] = set()
    for prediction in predictions:
        sample = roster.get((prediction.source_id, prediction.sample_id))
        if sample is None or sample.profile_id != prediction.profile_id:
            message = 'Test predictions must match the declared sample/profile roster.'
            raise ConformalPlanError(message)
        if _group(sample, plan) not in plan.test_groups:
            message = 'Only declared untouched test groups can receive prediction intervals.'
            raise ConformalLeakageError(message)
        key = (prediction.source_id, prediction.sample_id, prediction.suction_kpa)
        if (
            key in seen
            or isinstance(prediction.predicted, bool)
            or isinstance(prediction.suction_kpa, bool)
            or not math.isfinite(prediction.predicted)
            or not math.isfinite(prediction.suction_kpa)
        ):
            message = 'Test prediction points must be unique and finite.'
            raise ConformalPlanError(message)
        seen.add(key)
        reason = (
            'unsupported_pressure'
            if prediction.suction_kpa not in plan.pressure_grid_kpa
            else calibration.reason
        )
        if reason is not None or calibration.half_width is None:
            result.append(ConformalPredictionInterval(prediction, None, None, reason))
        else:
            result.append(
                ConformalPredictionInterval(
                    prediction,
                    prediction.predicted - calibration.half_width,
                    prediction.predicted + calibration.half_width,
                    None,
                )
            )
    return tuple(result)


def _validate_roles(plan: GroupedConformalPlan) -> None:
    if not plan.calibration_groups or not plan.test_groups:
        message = 'Calibration and test group roles must be declared explicitly.'
        raise ConformalPlanError(message)
    seen: set[GroupKey] = set()
    for roles in (plan.training_groups, plan.calibration_groups, plan.test_groups):
        for group in roles:
            if (
                len(group) != _GROUP_KEY_SIZE
                or not group[0].strip()
                or (bool(group[1].strip()) != (plan.grouping == 'profile'))
            ):
                message = (
                    'Conformal group keys must match the registered source/profile convention.'
                )
                raise ConformalPlanError(message)
            if group in seen:
                message = (
                    'Training, calibration, and test groups must be unique and pairwise disjoint.'
                )
                raise ConformalLeakageError(message)
            seen.add(group)


def _group(sample: GroupedSample, plan: GroupedConformalPlan) -> GroupKey:
    if plan.grouping == 'profile' and not sample.profile_id:
        message = (
            'Profile-conformal intervals require complete identities; no fallback is implicit.'
        )
        raise ConformalPlanError(message)
    return (
        sample.source_id,
        sample.profile_id if plan.grouping == 'profile' and sample.profile_id is not None else '',
    )


def _roster(
    samples: Iterable[GroupedSample],
    plan: GroupedConformalPlan,
) -> tuple[tuple[GroupedSample, ...], Mapping[GroupKey, tuple[SampleKey, ...]]]:
    roster = tuple(sorted(samples, key=lambda sample: (sample.source_id, sample.sample_id)))
    groups: dict[GroupKey, list[SampleKey]] = defaultdict(list)
    seen: set[SampleKey] = set()
    for sample in roster:
        key = (sample.source_id, sample.sample_id)
        if key in seen or not sample.sample_id.strip() or not sample.source_id.strip():
            message = 'Conformal sample identities must be nonempty and unique.'
            raise ConformalPlanError(message)
        seen.add(key)
        groups[_group(sample, plan)].append(key)
    if {*plan.calibration_groups, *plan.training_groups, *plan.test_groups} - set(groups):
        message = 'Conformal roles reference groups absent from the sample roster.'
        raise ConformalPlanError(message)
    return roster, {key: tuple(value) for key, value in groups.items()}


def validate_prediction_interval_roster(
    samples: Iterable[GroupedSample],
    *,
    plan: GroupedConformalPlan,
) -> None:
    """Validate complete role identities without reading targets or calibration scores."""
    _roster(samples, plan)
