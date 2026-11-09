"""Training-input support for learned inner predictions and locked outer strategies."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from .applicability import EmpiricalDomainPlan, RunEmpiricalDomain, assess_retention_applicability
from .documents import EvaluationDocumentError
from .nested_applicability import (
    NestedApplicabilityResult,
    NestedDomainPlan,
    NestedFoldDomain,
    combine_member_input_statuses,
    summarize_domain_strata,
)


if TYPE_CHECKING:
    from .folds import GroupKey
    from .learned import LearnedNestedSelection
    from .metrics import RetentionComparison
    from .runner import RetentionRunResult


@dataclass(frozen=True)
class _DiagnosticRequest:
    identifier: str
    outer_id: int
    inner_id: int | None
    training: tuple[GroupKey, ...]
    held_out: tuple[GroupKey, ...]
    predictions: tuple[RetentionComparison, ...]


def diagnose_learned_applicability(
    result: RetentionRunResult, *, policy: NestedDomainPlan
) -> NestedApplicabilityResult:
    """Diagnose inner candidates and only locked outer choices after training.

    An ensemble's domain is the intersection of its two constituent input
    envelopes, including a zero-weight member. The conservative registered
    all-member rule is independent of fitted weight and observed targets.
    No new weights are fitted or predictions selected by this diagnostic.
    """
    selection = result.learned_selection
    if selection is None:
        message = 'Learned applicability requires completed learned selection evidence.'
        raise EvaluationDocumentError(message)
    if selection.splits.status != 'computed':
        return NestedApplicabilityResult(policy, (), selection.splits.reason)
    output = []
    for request in _requests(selection):
        domain_policy = EmpiricalDomainPlan(
            candidate_id=request.identifier,
            training_groups=request.training,
            test_groups=request.held_out,
            minimum_training_groups=policy.minimum_training_groups,
            grouping=selection.splits.effective_grouping,
        )
        domain = _domain(result, selection, domain_policy)
        samples = combine_member_input_statuses(domain)
        strata = summarize_domain_strata(
            result,
            samples=samples,
            comparisons=request.predictions,
            loss_plan=selection.plan.fixed.loss,
        )
        output.append(
            NestedFoldDomain(
                request.outer_id,
                request.inner_id,
                'outer_test' if request.inner_id is None else 'inner_validation',
                domain,
                samples,
                strata,
                request.inner_id is None,
            )
        )
    return NestedApplicabilityResult(policy, tuple(output), None)


def _requests(selection: LearnedNestedSelection) -> tuple[_DiagnosticRequest, ...]:
    output = []
    for fold in selection.folds:
        outer = next(item for item in selection.splits.folds if item.fold_id == fold.fold_id)
        for strategy in (fold.atomic, fold.ensemble):
            if strategy.candidate_id is not None:
                output.append(
                    _DiagnosticRequest(
                        strategy.candidate_id,
                        fold.fold_id,
                        None,
                        outer.training_groups,
                        outer.test_groups,
                        strategy.predictions,
                    )
                )
            for score in strategy.inner_scores:
                for evidence in score.folds:
                    inner = next(item for item in outer.inner if item.fold_id == evidence.fold_id)
                    output.append(
                        _DiagnosticRequest(
                            score.candidate_id,
                            fold.fold_id,
                            inner.fold_id,
                            inner.training_groups,
                            inner.validation_groups,
                            evidence.predictions,
                        )
                    )
    return tuple(output)


def _domain(
    result: RetentionRunResult, selection: LearnedNestedSelection, policy: EmpiricalDomainPlan
) -> RunEmpiricalDomain:
    ensembles = {ensemble.id: ensemble for ensemble in selection.plan.ensembles}
    if policy.candidate_id not in ensembles:
        return assess_retention_applicability(result.plan, policy=policy)
    ensemble = ensembles[policy.candidate_id]
    members = tuple(
        replace(member, member_id=f'{side}:{member.member_id}')
        for side, identifier in (
            ('left', ensemble.left_candidate_id),
            ('right', ensemble.right_candidate_id),
        )
        for member in assess_retention_applicability(
            result.plan, policy=replace(policy, candidate_id=identifier)
        ).members
    )
    return RunEmpiricalDomain(policy, members)
