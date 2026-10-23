"""Explicit sample-balanced point-error assessment on a frozen selection domain."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .losses import LogPressureLossPlan, RetentionLossError, mean_finite_losses


if TYPE_CHECKING:
    from collections.abc import Iterable

    from .folds import SampleKey
    from .metrics import RetentionComparison


@dataclass(frozen=True, kw_only=True)
class PointErrorLossPlan:
    """Mean point MAE/MSE per sample, separate from the unchanged selection loss.

    Every original eligible common point inside the selection domain is required.
    Points have equal weight within a sample; samples later have equal population
    weight. The domain endpoints and minimum grid size come from selection_loss.
    """

    selection_loss: LogPressureLossPlan
    metric: Literal['mae', 'mse']
    method: Literal['sample_point_error_mean_v1'] = 'sample_point_error_mean_v1'

    def __post_init__(self) -> None:
        """Require an explicit complete-domain protocol and supported point functional."""
        if (
            not isinstance(self.selection_loss, LogPressureLossPlan)
            or self.metric not in ('mae', 'mse')
            or self.method != 'sample_point_error_mean_v1'
        ):
            message = (
                'Point assessment requires a selection-domain plan and explicit MAE/MSE metric.'
            )
            raise RetentionLossError(message)

    @property
    def lower_suction_kpa(self) -> float:
        """Keep the scoring domain identical to the registered selection domain."""
        return self.selection_loss.lower_suction_kpa

    @property
    def upper_suction_kpa(self) -> float:
        """Expose the upper domain endpoint without a separate test-driven override."""
        return self.selection_loss.upper_suction_kpa

    @property
    def minimum_points(self) -> int:
        """Retain the original minimum complete sample-grid requirement."""
        return self.selection_loss.minimum_points


@dataclass(frozen=True)
class SamplePointLoss:
    """One full holdout sample, including missing-grid or failed-training evidence."""

    source_id: str
    sample_id: str
    point_count: int
    expected_point_count: int
    loss: float | None
    reason: (
        Literal[
            'insufficient_points',
            'missing_domain_endpoints',
            'incomplete_forecast_grid',
            'nonfinite_point_error',
            'training_failed',
        ]
        | None
    )


def evaluate_sample_point_losses(
    predictions: Iterable[RetentionComparison],
    *,
    references: Iterable[RetentionComparison],
    sample_keys: tuple[SampleKey, ...],
    plan: PointErrorLossPlan,
    training_failed: bool = False,
) -> tuple[SamplePointLoss, ...]:
    """Assess the exact original eligible grid without silently dropping predictions.

    References are the frozen fixed-roster common cohort, not selected by model
    quality. Observed values/profile identities must match. Extra in-domain
    forecasts are rejected, while missing forecasts make that sample unavailable.
    Failed training retains all sample identities with no invented model errors.
    """
    if len(set(sample_keys)) != len(sample_keys) or any(
        not source.strip() or not sample.strip() for source, sample in sample_keys
    ):
        message = 'Point assessment requires unique nonempty original sample identities.'
        raise RetentionLossError(message)
    known = set(sample_keys)
    prediction_records = tuple(predictions)
    predicted = _index(prediction_records, known, plan)
    expected = _index(tuple(references), known, plan)
    if training_failed and prediction_records:
        message = 'Failed training cannot supply point-loss model predictions.'
        raise RetentionLossError(message)
    result = []
    for key in sorted(sample_keys):
        actual, reference = predicted.get(key, {}), expected.get(key, {})
        if set(actual) - set(reference):
            message = 'Point forecasts include pressures outside the frozen eligible common grid.'
            raise RetentionLossError(message)
        if any(
            point.observed != reference[p].observed or point.profile_id != reference[p].profile_id
            for p, point in actual.items()
        ):
            message = 'Point forecasts must preserve original observations and profile identities.'
            raise RetentionLossError(message)
        reason = (
            'training_failed'
            if training_failed
            else 'insufficient_points'
            if len(reference) < plan.minimum_points
            else 'missing_domain_endpoints'
            if (
                min(reference) != plan.lower_suction_kpa or max(reference) != plan.upper_suction_kpa
            )
            else 'incomplete_forecast_grid'
            if set(actual) != set(reference)
            else None
        )
        values = []
        if reason is None:
            for point in actual.values():
                error = point.predicted - point.observed
                values.append(abs(error) if plan.metric == 'mae' else error * error)
            if any(not math.isfinite(value) for value in values):
                reason = 'nonfinite_point_error'
        result.append(
            SamplePointLoss(
                *key,
                len(actual),
                len(reference),
                mean_finite_losses(values) if reason is None else None,
                reason,
            )
        )
    return tuple(result)


def _index(
    points: tuple[RetentionComparison, ...], known: set[SampleKey], plan: PointErrorLossPlan
) -> dict[SampleKey, dict[float, RetentionComparison]]:
    result: dict[SampleKey, dict[float, RetentionComparison]] = {}
    seen = set()
    profiles = {}
    for point in points:
        key = (point.source_id, point.sample_id)
        if (
            key not in known
            or (point.profile_id is not None and not point.profile_id.strip())
            or any(
                isinstance(v, bool) or not math.isfinite(v)
                for v in (point.suction_kpa, point.observed, point.predicted)
            )
            or point.suction_kpa < 0
            or not 0 <= point.observed <= 1
            or (key, point.suction_kpa) in seen
            or (key in profiles and profiles[key] != point.profile_id)
        ):
            message = (
                'Point assessment requires unique finite canonical rows on the complete roster.'
            )
            raise RetentionLossError(message)
        seen.add((key, point.suction_kpa))
        profiles[key] = point.profile_id
        if plan.lower_suction_kpa <= point.suction_kpa <= plan.upper_suction_kpa:
            result.setdefault(key, {})[point.suction_kpa] = point
    return result
