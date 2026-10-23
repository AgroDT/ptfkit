"""Target-free contrasts at locked outer-training hard-switch boundaries."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .hard_switch import HardSwitchGridFit


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
