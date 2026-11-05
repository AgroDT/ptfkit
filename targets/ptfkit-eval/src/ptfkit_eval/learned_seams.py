"""Target-free contrasts at locked outer-training hard-switch boundaries."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .blend_grid import BlendGridFit
from .hard_switch import HardSwitchGridFit
from .sigmoid_grid import SigmoidGridFit


if TYPE_CHECKING:
    from .runner import RetentionRunResult, RunFuturePrediction


@dataclass(frozen=True)
class LearnedSwitchSeam:
    """Both member forecasts at a fitted seam, independent of observed targets."""

    outer_fold_id: int
    candidate_id: str
    suction_kpa: float
    boundary_member: str
    left: RunFuturePrediction
    right: RunFuturePrediction
    right_minus_left: float | None
    status: str
    method: str = 'locked_outer_switch_member_contrast_v1'


def diagnose_learned_switch_seams(result: RetentionRunResult) -> tuple[LearnedSwitchSeam, ...]:
    """Evaluate both members for outer test samples at their already locked seam.

    This diagnostic does not read observations, refit a boundary, or change
    routing/eligibility. A contrast implies a jump only for member curves
    continuous at the boundary. Failed inputs stay explicit in the forecasts.
    """
    from .runner import predict_retention_grid  # noqa: PLC0415 - Runtime runner integration.

    selection = result.learned_selection
    if selection is None:
        return ()
    output = []
    for fold in selection.folds:
        fit = fold.ensemble.outer_fit
        if not isinstance(fit, HardSwitchGridFit) or fit.switch_suction_kpa is None:
            continue
        outer = next(item for item in selection.splits.folds if item.fold_id == fold.fold_id)
        keys = tuple(
            sample
            for group in selection.splits.groups
            if group.group_id in outer.test_groups
            for sample in group.samples
        )
        forecasts = [
            predict_retention_grid(
                result.plan,
                candidate_id=identifier,
                sample_keys=keys,
                pressure_grid_kpa=(fit.switch_suction_kpa,),
            )
            for identifier in (fit.plan.left_candidate_id, fit.plan.right_candidate_id)
        ]
        for left, right in zip(*forecasts, strict=True):
            difference = (
                right.predicted - left.predicted
                if left.predicted is not None and right.predicted is not None
                else None
            )
            status = 'computed' if difference is not None else 'unavailable'
            if difference is not None and not math.isfinite(difference):
                difference = None
                status = 'nonfinite_contrast'
            output.append(
                LearnedSwitchSeam(
                    fold.fold_id,
                    fit.plan.id,
                    fit.switch_suction_kpa,
                    fit.plan.boundary_member,
                    left,
                    right,
                    difference,
                    status,
                )
            )
    return tuple(output)


@dataclass(frozen=True)
class LearnedBlendEndpoint:
    """Target-free member forecasts at one locked blend endpoint, not a jump estimate."""

    outer_fold_id: int
    candidate_id: str
    side: Literal['lower', 'upper']
    suction_kpa: float
    active_member: Literal['left', 'right']
    left: RunFuturePrediction
    right: RunFuturePrediction
    right_minus_left: float | None
    status: str
    method: str = 'locked_outer_blend_endpoint_contrast_v1'


def diagnose_learned_blend_endpoints(
    result: RetentionRunResult,
) -> tuple[LearnedBlendEndpoint, ...]:
    """Forecast both atomic members at already trained lower and upper endpoints.

    No observations are read and no interval is refitted. A member contrast is
    not a discontinuity of the blend: endpoint weights select one member. This
    diagnostic neither repairs physical curves nor changes input eligibility.
    """
    from .runner import predict_retention_grid  # noqa: PLC0415 - Runtime runner integration.

    selection = result.learned_selection
    if selection is None:
        return ()
    output = []
    for fold in selection.folds:
        fit = fold.ensemble.outer_fit
        if not isinstance(fit, BlendGridFit) or fit.interval_kpa is None:
            continue
        outer = next(item for item in selection.splits.folds if item.fold_id == fold.fold_id)
        keys = tuple(
            sample
            for group in selection.splits.groups
            if group.group_id in outer.test_groups
            for sample in group.samples
        )
        forecasts = [
            predict_retention_grid(
                result.plan,
                candidate_id=identifier,
                sample_keys=keys,
                pressure_grid_kpa=fit.interval_kpa,
            )
            for identifier in (fit.plan.left_candidate_id, fit.plan.right_candidate_id)
        ]
        for left, right in zip(*forecasts, strict=True):
            difference = (
                right.predicted - left.predicted
                if left.predicted is not None and right.predicted is not None
                else None
            )
            status = 'computed' if difference is not None else 'unavailable'
            if difference is not None and not math.isfinite(difference):
                difference, status = None, 'nonfinite_contrast'
            lower = left.suction_kpa == fit.interval_kpa[0]
            output.append(
                LearnedBlendEndpoint(
                    fold.fold_id,
                    fit.plan.id,
                    'lower' if lower else 'upper',
                    left.suction_kpa,
                    'left' if lower else 'right',
                    left,
                    right,
                    difference,
                    status,
                )
            )
    return tuple(output)


@dataclass(frozen=True)
class LearnedSigmoidCenter:
    """Both member traces at the locked sigmoid center, without reading targets."""

    fold_id: int
    ensemble_id: str
    suction_kpa: float
    steepness: float
    left: RunFuturePrediction
    right: RunFuturePrediction
    predicted: float | None
    status: str
    method: str = 'locked_outer_sigmoid_center_prediction_v1'


def diagnose_learned_sigmoid_centers(
    result: RetentionRunResult,
) -> tuple[LearnedSigmoidCenter, ...]:
    """Forecast each original outer-test sample at a trained equal-weight center."""
    from .runner import predict_retention_grid  # noqa: PLC0415 - Runtime runner integration.

    selection = result.learned_selection
    if selection is None:
        return ()
    output = []
    for fold in selection.folds:
        fit = fold.ensemble.outer_fit
        if not isinstance(fit, SigmoidGridFit) or fit.parameters is None:
            continue
        center, steepness = fit.parameters
        outer = next(item for item in selection.splits.folds if item.fold_id == fold.fold_id)
        keys = tuple(
            key
            for group in selection.splits.groups
            if group.group_id in outer.test_groups
            for key in group.samples
        )
        forecasts = [
            predict_retention_grid(
                result.plan,
                candidate_id=identifier,
                sample_keys=keys,
                pressure_grid_kpa=(center,),
            )
            for identifier in (fit.plan.left_candidate_id, fit.plan.right_candidate_id)
        ]
        for left, right in zip(*forecasts, strict=True):
            prediction = (
                left.predicted / 2 + right.predicted / 2
                if left.predicted is not None and right.predicted is not None
                else None
            )
            status = 'computed' if prediction is not None else 'unavailable'
            if prediction is not None and not math.isfinite(prediction):
                prediction, status = None, 'nonfinite_prediction'
            output.append(
                LearnedSigmoidCenter(
                    fold.fold_id,
                    fit.plan.id,
                    center,
                    steepness,
                    left,
                    right,
                    prediction,
                    status,
                )
            )
    return tuple(output)
