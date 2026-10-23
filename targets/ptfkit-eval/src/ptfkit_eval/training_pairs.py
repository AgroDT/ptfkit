"""Paired training-law risk differences with explicit joint training success."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Literal

from .documents import EvaluationDocumentError
from .risk_bounds import BoundedRiskInterval
from .training_risk import (
    IndependentTrainingBlock,
    IndependentTrainingRiskBound,
    IndependentTrainingRiskPlan,
    TrainingRiskTestGroup,
    bound_independent_training_risk,
)


@dataclass(frozen=True, kw_only=True)
class PairedTrainingRiskPlan:
    """A joint learner and signed left-minus-right risk on identical block roles.

    The bound B applies separately to each learner's sample loss. Totality, if
    asserted, concerns the joint procedure: both learners always return models.
    """

    bounds: IndependentTrainingRiskPlan
    left_learner_id: str
    right_learner_id: str
    method: Literal['independent_blocks_affine_paired_training_law_v1'] = (
        'independent_blocks_affine_paired_training_law_v1'
    )

    def __post_init__(self) -> None:
        """Require explicit distinct learner identities and supported orientation."""
        if (
            not self.left_learner_id.strip()
            or not self.right_learner_id.strip()
            or self.left_learner_id == self.right_learner_id
            or self.method != 'independent_blocks_affine_paired_training_law_v1'
        ):
            message = (
                'Paired training risk requires two distinct named learners and a valid method.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class PairedTrainingRiskBound:
    """Joint success/failure and signed risk difference, without dropping fits."""

    plan: PairedTrainingRiskPlan
    transformed_bound: IndependentTrainingRiskBound | None
    joint_success_probability_interval: BoundedRiskInterval | None
    joint_failure_probability_interval: BoundedRiskInterval | None
    risk_difference_mass_on_joint_success_interval: BoundedRiskInterval | None
    joint_success_mean_risk_difference_interval: BoundedRiskInterval | None
    unconditional_mean_risk_difference_interval: BoundedRiskInterval | None
    reason: str | None
    joint_success_risk_reason: str | None = None
    target: Literal['training_law_left_minus_right_on_joint_success'] = (
        'training_law_left_minus_right_on_joint_success'
    )
    transform: Literal['half_shifted_normalized_sample_loss_difference_v1'] = (
        'half_shifted_normalized_sample_loss_difference_v1'
    )

    @property
    def status(self) -> str:
        """Risk mass can be computed even when joint-success risk is unavailable."""
        return 'computed' if self.reason is None else 'insufficient_evidence'


def bound_paired_independent_training_risk(
    left: tuple[IndependentTrainingBlock, ...],
    right: tuple[IndependentTrainingBlock, ...],
    *,
    plan: PairedTrainingRiskPlan,
) -> PairedTrainingRiskBound:
    """Pair complete original-group roles and apply a bounded affine loss map.

    On joint training success, t=(left_loss/B-right_loss/B+1)/2 lies in [0,1].
    The existing simultaneous kernel bounds E[I R_t] and p=P(joint success).
    Signed difference mass is B*(2*E[I R_t]-p). Conditional risk differences
    use B*(2*E[R_t|joint success]-1); they do not subtract marginal successful-
    training risks with different conditioning events. A one-sided training
    failure leaves the joint test loss unavailable and retains its group sizes.
    """
    # Reuse the public kernel's full structural validation. Marginal test
    # missingness does not invalidate a pair already undefined by the other fit.
    validation_plan = replace(plan.bounds, total_learner=False)
    validations = (
        bound_independent_training_risk(left, plan=validation_plan),
        bound_independent_training_risk(right, plan=validation_plan),
    )
    left_by_id = {block.block_id: block for block in left}
    right_by_id = {block.block_id: block for block in right}
    if set(left_by_id) != set(right_by_id):
        message = 'Paired learners must have identical original block identities.'
        raise EvaluationDocumentError(message)
    for identifier, one in left_by_id.items():
        two = right_by_id[identifier]
        if one.training_groups != two.training_groups or tuple(
            t.group for t in one.test_groups
        ) != tuple(t.group for t in two.test_groups):
            message = 'Paired learners must preserve identical original training/test roles.'
            raise EvaluationDocumentError(message)
    reason = next(
        (
            result.reason
            for result in validations
            if result.reason
            in ('observed_group_size_bound_violation', 'observed_sample_loss_bound_violation')
        ),
        None,
    )
    reason = reason or _raw_loss_reason((*left, *right), plan.bounds.maximum_sample_loss)
    if reason is not None:
        return PairedTrainingRiskBound(plan, None, None, None, None, None, None, reason)
    transformed = []
    scale = plan.bounds.maximum_sample_loss
    for identifier in sorted(left_by_id):
        one, two = left_by_id[identifier], right_by_id[identifier]
        failure = (
            f'left:{one.training_failure_reason}' if one.training_failure_reason is not None else ''
        )
        if two.training_failure_reason is not None:
            failure += f';right:{two.training_failure_reason}'
        groups = tuple(
            TrainingRiskTestGroup(a.group, _paired_losses(a, b, scale) if not failure else None)
            for a, b in zip(one.test_groups, two.test_groups, strict=True)
        )
        transformed.append(
            IndependentTrainingBlock(identifier, one.training_groups, groups, failure or None)
        )
    bound = bound_independent_training_risk(
        tuple(transformed), plan=replace(plan.bounds, maximum_sample_loss=1)
    )
    mass, success = bound.risk_mass_on_success_interval, bound.training_success_probability_interval
    signed_mass = None
    if mass is not None and success is not None:
        upper = min(success.upper, 2 * mass.upper - success.lower)
        lower = min(upper, max(-success.upper, 2 * mass.lower - success.upper))
        signed_mass = BoundedRiskInterval(scale * lower, scale * upper)
    return PairedTrainingRiskBound(
        plan,
        bound,
        success,
        bound.training_failure_probability_interval,
        signed_mass,
        _signed_interval(bound.successful_training_mean_risk_interval, scale),
        _signed_interval(bound.unconditional_model_risk_interval, scale),
        bound.reason,
        joint_success_risk_reason=bound.successful_training_risk_reason,
    )


def _raw_loss_reason(blocks: tuple[IndependentTrainingBlock, ...], scale: float) -> str | None:
    for block in blocks:
        for test in block.test_groups:
            if test.sample_losses is None:
                continue
            if len(test.sample_losses) != len(test.group.samples):
                return 'incomplete_paired_test_losses'
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 <= value <= scale
                for value in test.sample_losses
            ):
                return 'observed_sample_loss_bound_violation'
    return None


def _paired_losses(
    left: TrainingRiskTestGroup, right: TrainingRiskTestGroup, scale: float
) -> tuple[float, ...] | None:
    if left.sample_losses is None or right.sample_losses is None:
        return None
    return tuple(
        ((a - b) / scale + 1) / 2
        for a, b in zip(left.sample_losses, right.sample_losses, strict=True)
    )


def _signed_interval(
    interval: BoundedRiskInterval | None, scale: float
) -> BoundedRiskInterval | None:
    return (
        BoundedRiskInterval(scale * (2 * interval.lower - 1), scale * (2 * interval.upper - 1))
        if interval is not None
        else None
    )
