"""Repeat complete candidate selection on independent original-group blocks."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, replace
from typing import TYPE_CHECKING, Literal, cast

from .cohorts import build_retention_cohorts, run_candidate_comparisons
from .contracts import FunctionCurveCandidate
from .documents import EvaluationDocumentError, document_hash, object_records
from .folds import GroupedSample
from .learned import (
    select_grouped_forecast_holdout,
    validate_grouped_forecast_inputs,
    validate_learned_selection_candidates,
)
from .point_losses import PointErrorLossPlan, SamplePointLoss, evaluate_sample_point_losses
from .risk_bounds import BoundedRiskInterval
from .training_blocks import allocate_independent_training_blocks
from .training_pairs import (
    PairedTrainingRiskBound,
    PairedTrainingRiskPlan,
    bound_paired_independent_training_risk,
)
from .training_risk import (
    IndependentTrainingBlock,
    IndependentTrainingRiskPlan,
    TrainingRiskTestGroup,
    bound_independent_training_risk,
)


if TYPE_CHECKING:
    from collections.abc import Mapping

    from .cohorts import RetentionCandidateComparisons
    from .learned import LearnedNestedSelection, LearnedSelectionPlan
    from .runner import RetentionRunResult
    from .training_blocks import IndependentTrainingAllocation, TrainingBlockRoles
    from .training_risk import IndependentTrainingRiskBound


@dataclass(frozen=True, kw_only=True)
class SelectionTrainingRiskPlan:
    """One preregistered native policy before family error-budget allocation."""

    strategy: Literal['atomic', 'ensemble']
    seed: int
    bounds: IndependentTrainingRiskPlan

    def __post_init__(self) -> None:
        """Reject ambiguous strategies, noninteger seeds and preallocated budgets."""
        if (
            self.strategy not in ('atomic', 'ensemble')
            or isinstance(self.seed, bool)
            or not isinstance(self.seed, int)
            or self.bounds.simultaneous_policy_count != 1
        ):
            message = (
                'Training-risk policies require a strategy, integer seed and unallocated bounds.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True, kw_only=True)
class SelectionPairedTrainingRiskPlan:
    """A single oriented joint-success comparison on shared original blocks."""

    bounds: PairedTrainingRiskPlan
    left_strategy: Literal['atomic', 'ensemble']
    right_strategy: Literal['atomic', 'ensemble']
    seed: int

    def __post_init__(self) -> None:
        """Require distinct supported strategies and one unallocated comparison."""
        if (
            self.left_strategy not in ('atomic', 'ensemble')
            or self.right_strategy not in ('atomic', 'ensemble')
            or self.left_strategy == self.right_strategy
            or isinstance(self.seed, bool)
            or not isinstance(self.seed, int)
            or self.bounds.bounds.simultaneous_policy_count != 1
        ):
            message = (
                'Paired selection requires distinct strategies, integer seed and one comparison.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class IndependentSelectionBlock:
    """Full inner selection/refit evidence and complete test-loss/failure records."""

    roles: TrainingBlockRoles
    selection: LearnedNestedSelection
    evidence: IndependentTrainingBlock


@dataclass(frozen=True)
class PointSelectionBlock(IndependentSelectionBlock):
    """Retain every point-assessment sample and complete-grid failure reason."""

    point_losses: tuple[SamplePointLoss, ...]


@dataclass(frozen=True)
class IndependentSelectionTrainingRisk:
    """Auditable independent learner invocations, without success filtering."""

    allocation: IndependentTrainingAllocation
    selection_plan: LearnedSelectionPlan
    strategy: Literal['atomic', 'ensemble']
    candidate_kinds: tuple[tuple[str, Literal['atomic', 'ensemble']], ...]
    selector_sha256: str
    samples: tuple[GroupedSample, ...]
    candidates: tuple[RetentionCandidateComparisons, ...]
    blocks: tuple[IndependentSelectionBlock, ...]
    bound: IndependentTrainingRiskBound
    method: Literal['independent_blocks_complete_forecast_selection_v1'] = (
        'independent_blocks_complete_forecast_selection_v1'
    )


@dataclass(frozen=True, kw_only=True)
class PointSelectionTrainingRisk(IndependentSelectionTrainingRisk):
    """Sample point risk and the explicitly pooled square-root MSE functional."""

    assessment_loss: PointErrorLossPlan
    successful_training_pooled_rmse_interval: BoundedRiskInterval | None
    unconditional_pooled_rmse_interval: BoundedRiskInterval | None


@dataclass(frozen=True)
class PairedSelectionTrainingBlock:
    """The same learned rules and test roster, with separate fit-failure records."""

    roles: TrainingBlockRoles
    selection: LearnedNestedSelection
    left: IndependentTrainingBlock
    right: IndependentTrainingBlock


@dataclass(frozen=True)
class PairedPointSelectionTrainingBlock(PairedSelectionTrainingBlock):
    """Preserve separate point-assessment losses for the paired learners."""

    left_point_losses: tuple[SamplePointLoss, ...]
    right_point_losses: tuple[SamplePointLoss, ...]


@dataclass(frozen=True)
class PairedSelectionTrainingRisk:
    """A signed joint-success comparison, separate from marginal risk intervals."""

    allocation: IndependentTrainingAllocation
    selection_plan: LearnedSelectionPlan
    left_strategy: Literal['atomic', 'ensemble']
    right_strategy: Literal['atomic', 'ensemble']
    samples: tuple[GroupedSample, ...]
    candidates: tuple[RetentionCandidateComparisons, ...]
    blocks: tuple[PairedSelectionTrainingBlock, ...]
    bound: PairedTrainingRiskBound
    method: Literal['paired_complete_selector_joint_training_v1'] = (
        'paired_complete_selector_joint_training_v1'
    )


def pair_selection_training_evidence(
    selection: IndependentSelectionTrainingRisk,
    *,
    plan: PairedTrainingRiskPlan,
    left_strategy: Literal['atomic', 'ensemble'],
    right_strategy: Literal['atomic', 'ensemble'],
) -> PairedSelectionTrainingRisk:
    """Use both retained strategies from the same actual training invocations.

    No marginal risk intervals are subtracted. Bounds must describe exactly
    the allocated original block law, including its prior totality assertion.
    """
    if (
        left_strategy not in ('atomic', 'ensemble')
        or right_strategy not in ('atomic', 'ensemble')
        or left_strategy == right_strategy
        or plan.bounds != selection.allocation.plan
    ):
        message = 'Pairing requires two distinct strategies and the identical allocated block law.'
        raise EvaluationDocumentError(message)
    paired_blocks = []
    for block in selection.blocks:
        left = _block_evidence(
            block.roles,
            block.selection,
            left_strategy,
            point_loss=plan.bounds.loss
            if isinstance(plan.bounds.loss, PointErrorLossPlan)
            else None,
            candidates=selection.candidates,
        )
        right = _block_evidence(
            block.roles,
            block.selection,
            right_strategy,
            point_loss=plan.bounds.loss
            if isinstance(plan.bounds.loss, PointErrorLossPlan)
            else None,
            candidates=selection.candidates,
        )
        if isinstance(left, PointSelectionBlock) and isinstance(right, PointSelectionBlock):
            paired_blocks.append(
                PairedPointSelectionTrainingBlock(
                    block.roles,
                    block.selection,
                    left.evidence,
                    right.evidence,
                    left.point_losses,
                    right.point_losses,
                )
            )
        else:
            paired_blocks.append(
                PairedSelectionTrainingBlock(
                    block.roles,
                    block.selection,
                    left.evidence,
                    right.evidence,
                )
            )
    blocks = tuple(paired_blocks)
    bound = bound_paired_independent_training_risk(
        tuple(block.left for block in blocks), tuple(block.right for block in blocks), plan=plan
    )
    return PairedSelectionTrainingRisk(
        selection.allocation,
        selection.selection_plan,
        left_strategy,
        right_strategy,
        selection.samples,
        selection.candidates,
        blocks,
        bound,
    )


def assess_paired_selection_training(
    result: RetentionRunResult,
    *,
    plan: PairedTrainingRiskPlan,
    left_strategy: Literal['atomic', 'ensemble'],
    right_strategy: Literal['atomic', 'ensemble'],
    seed: int,
) -> PairedSelectionTrainingRisk:
    """Repeat both native strategies on identical roles and assess joint success."""
    trained = assess_independent_selection_training(
        result, bounds=plan.bounds, strategy=left_strategy, seed=seed
    )
    return pair_selection_training_evidence(
        trained, plan=plan, left_strategy=left_strategy, right_strategy=right_strategy
    )


def validate_independent_selection_policies(
    policies: tuple[SelectionTrainingRiskPlan, ...],
) -> None:
    """Freeze a unique strategy family sharing one nominal confidence level."""
    if (
        len({p.strategy for p in policies}) != len(policies)
        or len({p.bounds.confidence_level for p in policies}) > 1
    ):
        message = 'Training-risk policies need unique strategies and a common confidence level.'
        raise EvaluationDocumentError(message)


def assess_independent_selection_family(
    result: RetentionRunResult, *, policies: tuple[SelectionTrainingRiskPlan, ...]
) -> tuple[IndependentSelectionTrainingRisk, ...]:
    """Allocate the registered family budget, retaining unsuccessful policies."""
    validate_independent_selection_policies(policies)
    return tuple(
        assess_independent_selection_training(
            result,
            bounds=replace(policy.bounds, simultaneous_policy_count=len(policies)),
            strategy=policy.strategy,
            seed=policy.seed,
        )
        for policy in policies
    )


def validate_point_training_policies(policies: tuple[SelectionTrainingRiskPlan, ...]) -> None:
    """Allocate one family across strategy/point-metric pairs, including failures."""
    if (
        any(not isinstance(p.bounds.loss, PointErrorLossPlan) for p in policies)
        or len({(p.strategy, cast('PointErrorLossPlan', p.bounds.loss).metric) for p in policies})
        != len(policies)
        or len({p.bounds.confidence_level for p in policies}) > 1
    ):
        message = 'Point risk requires unique strategy/metric pairs and common confidence.'
        raise EvaluationDocumentError(message)


def assess_point_selection_family(
    result: RetentionRunResult, *, policies: tuple[SelectionTrainingRiskPlan, ...]
) -> tuple[PointSelectionTrainingRisk, ...]:
    """Assess registered point metrics without changing the selector objective."""
    validate_point_training_policies(policies)
    return tuple(
        cast(
            'PointSelectionTrainingRisk',
            assess_independent_selection_training(
                result,
                bounds=replace(policy.bounds, simultaneous_policy_count=len(policies)),
                strategy=policy.strategy,
                seed=policy.seed,
            ),
        )
        for policy in policies
    )


def assess_independent_selection_training(
    result: RetentionRunResult,
    *,
    bounds: IndependentTrainingRiskPlan,
    strategy: Literal['atomic', 'ensemble'],
    seed: int,
) -> IndependentSelectionTrainingRisk:
    """Cache eligible fixed native forecasts and repeat every target-dependent fit.

    The registered learned-selector plan supplies the whole training procedure.
    No parent inner/outer predictions, choices or fitted weights are reused.
    Population assertions, effective group size and learner totality remain the
    caller's responsibility. This API does not register a run-policy family.
    """
    plan = result.plan.learned_selection
    if plan is None:
        message = 'Independent selection training requires a registered learned selector.'
        raise EvaluationDocumentError(message)
    validate_learned_selection_candidates(plan, result.plan.evaluation)
    roster = tuple(
        GroupedSample(
            cast('str', sample['source_id']),
            cast('str', sample['sample_id']),
            cast('str | None', sample['profile_id']),
        )
        for sample in object_records(result.plan.dataset.document['samples'])
    )
    candidates = {candidate.id: candidate for candidate in result.plan.evaluation.candidates}
    kinds: dict[str, Literal['atomic', 'ensemble']] = {
        identifier: 'atomic'
        if isinstance(candidates[identifier], FunctionCurveCandidate)
        else 'ensemble'
        for identifier in plan.fixed.candidate_ids
    }
    # Resolve the original full-roster fallback once, before allocating blocks.
    grouping = plan.fixed.folds.grouping
    if (
        grouping == 'profile'
        and any(sample.profile_id is None for sample in roster)
        and plan.fixed.folds.missing_profiles == 'source'
    ):
        grouping = 'source'
    resolved = replace(
        plan,
        fixed=replace(
            plan.fixed,
            folds=replace(plan.fixed.folds, grouping=grouping, missing_profiles='reject'),
        ),
    )
    return assess_independent_forecast_training(
        run_candidate_comparisons(result, plan.fixed.candidate_ids),
        samples=roster,
        candidate_kinds=kinds,
        selection_plan=resolved,
        bounds=bounds,
        strategy=strategy,
        seed=seed,
    )


def assess_independent_forecast_training(
    candidates: tuple[RetentionCandidateComparisons, ...],
    *,
    samples: tuple[GroupedSample, ...],
    candidate_kinds: Mapping[str, Literal['atomic', 'ensemble']],
    selection_plan: LearnedSelectionPlan,
    bounds: IndependentTrainingRiskPlan,
    strategy: Literal['atomic', 'ensemble'],
    seed: int,
) -> IndependentSelectionTrainingRisk:
    """Allocate blocks, repeat inner tuning/refitting and bound training-law risk.

    Fixed forecast provenance and scientific eligibility belong to the caller.
    Bounds must use the same complete loss and resolved original grouping as
    the selector. The entire input roster and every failed invocation survive.
    Test missingness suppresses inference rather than changing training success.
    """
    objective = (
        bounds.loss.selection_loss if isinstance(bounds.loss, PointErrorLossPlan) else bounds.loss
    )
    if (
        strategy not in ('atomic', 'ensemble')
        or selection_plan.fixed.loss != objective
        or selection_plan.fixed.folds.grouping != bounds.grouping
    ):
        message = 'Independent selection requires matching loss, resolved grouping and strategy.'
        raise EvaluationDocumentError(message)
    validate_grouped_forecast_inputs(
        candidates, samples=samples, candidate_kinds=candidate_kinds, plan=selection_plan
    )
    allocation = allocate_independent_training_blocks(samples, plan=bounds, seed=seed)
    blocks = []
    for roles in allocation.blocks:
        keys = {
            key for group in (*roles.training_groups, *roles.test_groups) for key in group.samples
        }
        block_samples = tuple(s for s in samples if (s.source_id, s.sample_id) in keys)
        block_candidates = tuple(
            replace(
                candidate,
                comparisons=tuple(
                    point
                    for point in candidate.comparisons
                    if (point.source_id, point.sample_id) in keys
                ),
            )
            for candidate in candidates
        )
        selection = select_grouped_forecast_holdout(
            block_candidates,
            samples=block_samples,
            candidate_kinds=candidate_kinds,
            training_groups=roles.training_groups,
            test_groups=roles.test_groups,
            plan=selection_plan,
        )
        blocks.append(
            _block_evidence(
                roles,
                selection,
                strategy,
                point_loss=bounds.loss if isinstance(bounds.loss, PointErrorLossPlan) else None,
                candidates=block_candidates,
            )
        )
    evidence = tuple(blocks)
    fingerprint = document_hash(
        {
            'method': 'independent_blocks_complete_forecast_selection_v1',
            'selector': asdict(selection_plan),
            'strategy': strategy,
            'candidate_kinds': dict(candidate_kinds),
            'training_groups': bounds.training_groups_per_block,
        }
    )
    bound = bound_independent_training_risk(
        tuple(block.evidence for block in evidence), plan=bounds
    )
    shared = (
        allocation,
        selection_plan,
        strategy,
        tuple(sorted(candidate_kinds.items())),
        fingerprint,
        samples,
        candidates,
        evidence,
        bound,
    )
    if isinstance(bounds.loss, PointErrorLossPlan):
        squared = bounds.loss.metric == 'mse'
        return PointSelectionTrainingRisk(
            *shared,
            assessment_loss=bounds.loss,
            successful_training_pooled_rmse_interval=_root_interval(
                bound.successful_training_mean_risk_interval
            )
            if squared
            else None,
            unconditional_pooled_rmse_interval=_root_interval(
                bound.unconditional_model_risk_interval
            )
            if squared
            else None,
        )
    return IndependentSelectionTrainingRisk(*shared)


def _root_interval(interval: BoundedRiskInterval | None) -> BoundedRiskInterval | None:
    return (
        BoundedRiskInterval(math.sqrt(interval.lower), math.sqrt(interval.upper))
        if interval
        else None
    )


def _block_evidence(
    roles: TrainingBlockRoles,
    selection: LearnedNestedSelection,
    strategy: Literal['atomic', 'ensemble'],
    *,
    point_loss: PointErrorLossPlan | None = None,
    candidates: tuple[RetentionCandidateComparisons, ...] = (),
) -> IndependentSelectionBlock:
    failure = selection.splits.reason
    losses = {}
    predictions = ()
    if selection.folds:
        selected = getattr(selection.folds[0], strategy)
        failure = (
            selected.reason
            if selected.candidate_id is None
            else selected.outer_fit.reason
            if selected.outer_fit is not None
            else None
        )
        predictions = selected.predictions if failure is None else ()
        if failure is None and selected.assessment is not None:
            losses = {
                (sample.source_id, sample.sample_id): sample.loss
                for sample in selected.assessment.samples
            }
    point_records = ()
    if point_loss is not None:
        keys = tuple(sorted(key for group in roles.test_groups for key in group.samples))
        known = set(keys)
        common = build_retention_cohorts(candidates).common[0].comparisons
        reference = tuple(p for p in common if (p.source_id, p.sample_id) in known)
        point_records = evaluate_sample_point_losses(
            predictions,
            references=reference,
            sample_keys=keys,
            plan=point_loss,
            training_failed=failure is not None,
        )
        losses = {(sample.source_id, sample.sample_id): sample.loss for sample in point_records}
    tests = []
    for group in roles.test_groups:
        values = tuple(losses.get(key) for key in group.samples)
        tests.append(
            TrainingRiskTestGroup(
                group,
                None
                if failure is not None or any(value is None for value in values)
                else tuple(cast('float', value) for value in values),
            )
        )
    evidence = IndependentTrainingBlock(
        roles.block_id, roles.training_groups, tuple(tests), failure
    )
    if point_loss is not None:
        return PointSelectionBlock(roles, selection, evidence, point_records)
    return IndependentSelectionBlock(roles, selection, evidence)
