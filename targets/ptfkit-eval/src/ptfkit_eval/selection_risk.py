"""Complete native selection evidence adapted to conditional outer-risk bounds."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal, cast

from .cohorts import build_retention_cohorts, run_candidate_comparisons
from .documents import EvaluationDocumentError, object_records
from .folds import GroupedSample, build_nested_group_folds
from .losses import (
    SampleCurveLoss,
    SelectionLossPlan,
    evaluate_selection_loss,
    mean_finite_losses,
)
from .risk_bounds import (
    BoundedGroupLoss,
    ConditionalOuterFoldLoss,
    ConditionalOuterRiskBound,
    ConditionalOuterRiskPlan,
    bound_conditional_outer_risks,
)
from .selection import FixedNestedSelection
from .selection_predictions import selection_prediction_frames


if TYPE_CHECKING:
    from .folds import GroupMembership, NestedGroupFolds
    from .runner import RetentionRunResult
    from .selection_predictions import SelectionPredictionFrame


@dataclass(frozen=True, kw_only=True)
class SelectionRiskPlan:
    """One preregistered protocol/strategy within the run's simultaneous family."""

    protocol: Literal['fixed', 'learned']
    strategy: Literal['atomic', 'ensemble']
    bounds: ConditionalOuterRiskPlan

    def __post_init__(self) -> None:
        """Keep family allocation controlled by the full registered roster."""
        if (
            self.protocol not in ('fixed', 'learned')
            or self.strategy not in ('atomic', 'ensemble')
            or self.bounds.simultaneous_policy_count != 1
        ):
            message = (
                'Selection risk requires a supported protocol/strategy and unallocated bounds.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class ConditionalRiskFoldFailure:
    """An outer fit/coverage/bound failure retained without a substitute interval."""

    fold_id: int
    reason: str


@dataclass(frozen=True)
class SelectionConditionalRisk:
    """One simultaneous-family member, including explicitly unavailable bounds."""

    policy: SelectionRiskPlan
    family_size: int
    allocated_error_probability: float
    bound: ConditionalOuterRiskBound | None
    fold_failures: tuple[ConditionalRiskFoldFailure, ...]
    reason: str | None

    @property
    def status(self) -> str:
        """Only a complete population-compatible strategy receives intervals."""
        return 'computed' if self.bound is not None else 'insufficient_evidence'


def validate_selection_risk_policies(policies: tuple[SelectionRiskPlan, ...]) -> None:
    """Use one explicit family confidence level and count failed policies too."""
    if (
        len({(policy.protocol, policy.strategy) for policy in policies}) != len(policies)
        or len({policy.bounds.confidence_level for policy in policies}) > 1
    ):
        message = (
            'Conditional risk policies require unique protocol/strategy pairs '
            'and one family confidence level.'
        )
        raise EvaluationDocumentError(message)


def assess_selection_conditional_risks(
    result: RetentionRunResult,
    *,
    policies: tuple[SelectionRiskPlan, ...],
) -> tuple[SelectionConditionalRisk, ...]:
    """Validate complete locked outer evidence before applying declared risk bounds.

    Each registered policy receives alpha/family_size, including failed policies.
    There is no success-conditioned reallocation. Grouping, loss and population
    bounds are explicit; source/profile IDs alone do not establish IID sampling.
    """
    validate_selection_risk_policies(policies)
    frames = selection_prediction_frames(result) if policies else ()
    return tuple(_assess(result, policy, len(policies), frames) for policy in policies)


def _assess(
    result: RetentionRunResult,
    policy: SelectionRiskPlan,
    family_size: int,
    frames: tuple[SelectionPredictionFrame, ...],
) -> SelectionConditionalRisk:
    selection = result.selection if policy.protocol == 'fixed' else result.learned_selection
    if selection is None:
        message = 'Conditional risk references an unexecuted selection protocol.'
        raise EvaluationDocumentError(message)
    fixed = selection.plan if isinstance(selection, FixedNestedSelection) else selection.plan.fixed
    if (
        selection.splits.plan != fixed.folds
        or policy.bounds.loss != fixed.loss
        or policy.bounds.grouping != selection.splits.effective_grouping
    ):
        message = 'Conditional risk must match registered folds, loss and resolved grouping.'
        raise EvaluationDocumentError(message)
    allocation = (1 - policy.bounds.confidence_level) / family_size
    if selection.splits.status != 'computed':
        return SelectionConditionalRisk(
            policy, family_size, allocation, None, (), selection.splits.reason
        )
    _validate_roster(result, selection.splits)
    if any(
        not policy.bounds.minimum_group_size
        <= len(group.samples)
        <= policy.bounds.maximum_group_size
        for group in selection.splits.groups
    ):
        return SelectionConditionalRisk(
            policy, family_size, allocation, None, (), 'observed_group_size_bound_violation'
        )
    outer = tuple(
        frame
        for frame in frames
        if frame.protocol == policy.protocol
        and frame.strategy == policy.strategy
        and frame.inner_fold_id is None
    )
    if sorted(frame.outer_fold_id for frame in outer) != sorted(
        fold.fold_id for fold in selection.splits.folds
    ):
        message = 'Conditional risk requires exactly one outer frame per registered fold.'
        raise EvaluationDocumentError(message)
    _validate_common_grid(result, fixed.candidate_ids, outer, fixed.loss)
    groups = {group.group_id: group for group in selection.splits.groups}
    evidence = []
    failures = []
    for frame in outer:
        fold, reason = _fold_evidence(frame, groups, policy.bounds)
        if reason is not None:
            failures.append(ConditionalRiskFoldFailure(frame.outer_fold_id, reason))
        elif fold is not None:
            evidence.append(fold)
    if failures:
        return SelectionConditionalRisk(
            policy, family_size, allocation, None, tuple(failures), 'incomplete_outer_strategy'
        )
    allocated_plan = replace(policy.bounds, simultaneous_policy_count=family_size)
    bound = bound_conditional_outer_risks(tuple(evidence), plan=allocated_plan)
    return SelectionConditionalRisk(policy, family_size, allocation, bound, (), None)


def _validate_common_grid(
    result: RetentionRunResult,
    candidate_ids: tuple[str, ...],
    outer: tuple[SelectionPredictionFrame, ...],
    loss: SelectionLossPlan,
) -> None:
    common = build_retention_cohorts(run_candidate_comparisons(result, candidate_ids)).common
    grid = {
        (point.source_id, point.sample_id, point.suction_kpa): (point.observed, point.profile_id)
        for point in common[0].comparisons
    }
    if any(
        grid.get((point.source_id, point.sample_id, point.suction_kpa))
        != (point.observed, point.profile_id)
        for frame in outer
        for point in frame.predictions
    ):
        message = 'Conditional risk forecasts must retain the eligible common observation grid.'
        raise EvaluationDocumentError(message)

    expected = {key for key in grid if loss.lower_suction_kpa <= key[2] <= loss.upper_suction_kpa}
    for frame in outer:
        if (
            frame.reason is not None
            or frame.assessment is None
            or frame.assessment.mean_loss is None
        ):
            continue
        if frame.assessment.coverage != 1:
            continue
        held_out = set(frame.samples)
        expected_keys = {key for key in expected if key[:2] in held_out}
        actual_keys = {
            (point.source_id, point.sample_id, point.suction_kpa)
            for point in frame.predictions
            if loss.lower_suction_kpa <= point.suction_kpa <= loss.upper_suction_kpa
        }
        if actual_keys != expected_keys:
            message = 'Conditional risk requires the complete retained common pressure grid.'
            raise EvaluationDocumentError(message)


def _validate_roster(result: RetentionRunResult, splits: NestedGroupFolds) -> None:
    samples = {
        (str(sample['source_id']), str(sample['sample_id'])): sample
        for sample in object_records(result.plan.dataset.document['samples'])
    }
    roster = tuple(
        GroupedSample(
            str(sample['source_id']),
            str(sample['sample_id']),
            cast('str | None', sample['profile_id']),
        )
        for sample in samples.values()
    )
    if build_nested_group_folds(roster, plan=splits.plan) != splits:
        message = 'Conditional risk nested partition differs from the original identity-only split.'
        raise EvaluationDocumentError(message)


def _fold_evidence(
    frame: SelectionPredictionFrame,
    groups: dict[tuple[str, str], GroupMembership],
    plan: ConditionalOuterRiskPlan,
) -> tuple[ConditionalOuterFoldLoss | None, str | None]:
    if frame.assessment is None:
        return None, frame.reason or 'unavailable_outer_assessment'
    computed = {
        (item.source_id, item.sample_id): item
        for item in evaluate_selection_loss(frame.predictions, plan=plan.loss)
    }
    reproduced = tuple(
        computed.get(key, SampleCurveLoss(*key, 0, None, 'insufficient_points'))
        for key in frame.samples
    )
    assessed = frame.assessment
    if (
        tuple(sorted(assessed.samples, key=lambda item: (item.source_id, item.sample_id)))
        != reproduced
        or assessed.fold_id != frame.outer_fold_id
        or assessed.total_sample_count != len(frame.samples)
        or assessed.eligible_sample_count != sum(item.loss is not None for item in reproduced)
        or assessed.coverage
        != sum(item.loss is not None for item in reproduced) / len(frame.samples)
    ):
        message = (
            'Conditional risk retained forecasts do not reproduce the complete outer loss roster.'
        )
        raise EvaluationDocumentError(message)
    if frame.candidate_id is None or assessed.mean_loss is None:
        return None, frame.reason or assessed.reason or 'unavailable_outer_choice_or_loss'
    valid_losses = [item.loss for item in reproduced if item.loss is not None]
    if assessed.mean_loss != mean_finite_losses(valid_losses):
        message = 'Conditional risk retained losses do not reproduce the outer mean.'
        raise EvaluationDocumentError(message)
    if (
        frame.reason is not None
        or assessed.reason is not None
        or any(item.loss is None for item in reproduced)
    ):
        return None, frame.reason or assessed.reason or 'incomplete_outer_sample_losses'
    losses = {(item.source_id, item.sample_id): item.loss for item in reproduced}
    if any(value is not None and value > plan.maximum_sample_loss for value in losses.values()):
        return None, 'observed_sample_loss_bound_violation'
    grouped = []
    for identifier in frame.held_out_groups:
        values = []
        for key in groups[identifier].samples:
            loss = losses[key]
            values.append(cast('float', loss))
        grouped.append(BoundedGroupLoss(identifier, tuple(values)))
    return ConditionalOuterFoldLoss(
        frame.outer_fold_id, frame.training_groups, tuple(grouped)
    ), None
