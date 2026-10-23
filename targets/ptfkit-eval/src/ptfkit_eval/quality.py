"""Noncorrecting physical diagnostics for observed and predicted retention curves."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from typing import TYPE_CHECKING, Literal, cast

from .documents import object_records
from .selection_predictions import selection_prediction_frames


if TYPE_CHECKING:
    from collections.abc import Iterable

    from .runner import RetentionRunResult


class RetentionQualityError(ValueError):
    """Raised when a physical diagnostic receives invalid canonical arguments."""


@dataclass(frozen=True)
class RetentionSeriesPoint:
    """One observed or predicted volumetric point with an auditable reference."""

    suction_kpa: float
    water_content: float
    reference: str


@dataclass(frozen=True)
class RetentionSeriesDiagnostic:
    """A physical inconsistency with the exact points responsible."""

    code: Literal['water_outside_physical_bounds', 'increasing_water_with_suction']
    points: tuple[RetentionSeriesPoint, ...]


@dataclass(frozen=True)
class RetentionSeriesQuality:
    """Observed grid extent and physical findings, without modifying the series."""

    point_count: int
    minimum_suction_kpa: float | None
    maximum_suction_kpa: float | None
    diagnostics: tuple[RetentionSeriesDiagnostic, ...]


@dataclass(frozen=True)
class RunCurveQuality:
    """One observed or candidate-predicted series in a canonical run."""

    source_id: str
    sample_id: str
    kind: Literal['observed', 'predicted']
    candidate_id: str | None
    quality: RetentionSeriesQuality


@dataclass(frozen=True)
class SelectionCurveQuality:
    """A noncorrecting curve diagnostic in one explicitly labeled holdout frame."""

    protocol: str
    selection_method: str
    strategy: str
    outer_fold_id: int
    inner_fold_id: int | None
    candidate_id: str | None
    source_id: str
    sample_id: str
    assessment_status: str
    quality: RetentionSeriesQuality

    @property
    def status(self) -> str:
        """Keep absent predictions separate from a valid curve with no findings."""
        return 'diagnosed' if self.quality.point_count else 'no_predictions'

    @property
    def partition(self) -> str:
        """Inner validation curves are not untouched outer strategy assessments."""
        return 'outer_test' if self.inner_fold_id is None else 'inner_validation'


def diagnose_retention_series(
    points: Iterable[RetentionSeriesPoint],
    *,
    monotonicity_tolerance: float = 0.0,
) -> RetentionSeriesQuality:
    """Report bounds and monotonicity without clipping, smoothing, or exclusion.

    Tolerance applies only to increases in volume fraction between adjacent
    distinct pressures. Physical bounds remain exactly [0, 1]. The pressure
    extent is descriptive support, not an applicability or uncertainty interval.
    """
    if (
        isinstance(monotonicity_tolerance, bool)
        or not math.isfinite(monotonicity_tolerance)
        or monotonicity_tolerance < 0
    ):
        message = 'Monotonicity tolerance must be finite and nonnegative.'
        raise RetentionQualityError(message)
    ordered = sorted(points, key=lambda point: point.suction_kpa)
    seen: set[float] = set()
    for point in ordered:
        if (
            not math.isfinite(point.suction_kpa)
            or point.suction_kpa < 0
            or not math.isfinite(point.water_content)
            or not point.reference.strip()
        ):
            message = 'Curve quality requires finite canonical points and nonempty references.'
            raise RetentionQualityError(message)
        if point.suction_kpa in seen:
            message = 'Curve quality requires distinct pressure points.'
            raise RetentionQualityError(message)
        seen.add(point.suction_kpa)
    diagnostics = [
        RetentionSeriesDiagnostic('water_outside_physical_bounds', (point,))
        for point in ordered
        if not 0 <= point.water_content <= 1
    ]
    diagnostics.extend(
        RetentionSeriesDiagnostic('increasing_water_with_suction', (left, right))
        for left, right in pairwise(ordered)
        if right.water_content - left.water_content > monotonicity_tolerance
    )
    return RetentionSeriesQuality(
        len(ordered),
        ordered[0].suction_kpa if ordered else None,
        ordered[-1].suction_kpa if ordered else None,
        tuple(diagnostics),
    )


def diagnose_retention_run(
    result: RetentionRunResult,
    *,
    monotonicity_tolerance: float = 0.0,
) -> tuple[RunCurveQuality, ...]:
    """Diagnose all canonical observations and scored predictions independently.

    Observations include blocked and flagged rows so their inconsistencies stay
    visible. Their diagnostic presence does not make them eligible for scoring.
    Only successfully scored predictions enter predicted-series diagnostics.
    """
    groups: dict[tuple[str, str, str, str], list[RetentionSeriesPoint]] = defaultdict(list)
    for observation in object_records(result.plan.dataset.document['observations']):
        groups[
            cast('str', observation['source_id']),
            cast('str', observation['sample_id']),
            'observed',
            '',
        ].append(
            RetentionSeriesPoint(
                cast('float', observation['suction_kpa']),
                cast('float', observation['value']),
                cast('str', observation['id']),
            )
        )
    for point in result.points:
        if point.comparison is not None:
            groups[point.source_id, point.sample_id, 'predicted', point.candidate_id].append(
                RetentionSeriesPoint(
                    point.suction_kpa, point.comparison.predicted, point.observation_id
                )
            )
    return tuple(
        RunCurveQuality(
            source,
            sample,
            cast("Literal['observed', 'predicted']", kind),
            candidate or None,
            diagnose_retention_series(points, monotonicity_tolerance=monotonicity_tolerance),
        )
        for (source, sample, kind, candidate), points in sorted(groups.items())
    )


def diagnose_selection_curves(
    result: RetentionRunResult, *, monotonicity_tolerance: float = 0.0
) -> tuple[SelectionCurveQuality, ...]:
    """Diagnose inner candidates and locked outer predictions without repairing them.

    Frames stay separate across protocols, folds, candidates and strategies.
    Every declared held-out sample receives a record even if it lacks targets,
    inputs or a fitted choice. Only retained predictions are inspected; observed
    values cannot change these findings. No finding changes eligibility or model
    selection. Pressure support is descriptive and does not certify continuity
    or monotonicity between observed grid points.
    """
    # Validate tolerance even when no selection protocol produced any frames.
    diagnose_retention_series((), monotonicity_tolerance=monotonicity_tolerance)
    output = []
    for frame in selection_prediction_frames(result):
        groups: dict[tuple[str, str], list[RetentionSeriesPoint]] = defaultdict(list)
        for point in frame.predictions:
            groups[point.source_id, point.sample_id].append(
                RetentionSeriesPoint(
                    point.suction_kpa,
                    point.predicted,
                    f'{frame.candidate_id}@{point.suction_kpa:.17g}',
                )
            )
        for source, sample in frame.samples:
            output.append(
                SelectionCurveQuality(
                    frame.protocol,
                    frame.selection_method,
                    frame.strategy,
                    frame.outer_fold_id,
                    frame.inner_fold_id,
                    frame.candidate_id,
                    source,
                    sample,
                    frame.status,
                    diagnose_retention_series(
                        groups[source, sample], monotonicity_tolerance=monotonicity_tolerance
                    ),
                )
            )
    return tuple(output)
