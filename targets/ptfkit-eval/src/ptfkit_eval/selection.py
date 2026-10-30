"""Leakage-safe nested assessment of fixed atomic and registered ensemble candidates."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from .cohorts import build_retention_cohorts, run_candidate_comparisons
from .contracts import RangeGatedCurveCandidate
from .documents import object_records
from .folds import GroupedSample, NestedGroupFolds, NestedGroupPlan, build_nested_group_folds
from .losses import (
    SampleCurveLoss,
    SelectionLossPlan,
    SinglePressureLossPlan,
    evaluate_selection_loss,
    mean_finite_losses,
)


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .folds import GroupKey, InnerGroupFold, OuterGroupFold, SampleKey
    from .nested_applicability import NestedDomainPlan
    from .runner import RetentionRunResult


class FixedSelectionError(ValueError):
    """Raised when a fixed-candidate selection protocol is malformed or unsupported."""


@dataclass(frozen=True, kw_only=True)
class FixedSelectionPlan:
    """Explicit roster, loss, coverage, fold, tie-breaking, and failure policies."""

    candidate_ids: tuple[str, ...]
    folds: NestedGroupPlan
    loss: SelectionLossPlan
    minimum_coverage: float = 1.0
    tie_breaker: Literal['candidate_id'] = 'candidate_id'
    failure_policy: Literal['require_common_cohort'] = 'require_common_cohort'
    empirical_domains: NestedDomainPlan | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous registration before selection evidence is inspected."""
        if isinstance(self.loss, SinglePressureLossPlan) and self.empirical_domains is not None:
            message = 'Single-pressure selection does not support empirical-domain protocols.'
            raise FixedSelectionError(message)
        if (
            not self.candidate_ids
            or len(set(self.candidate_ids)) != len(self.candidate_ids)
            or any(not candidate.strip() for candidate in self.candidate_ids)
        ):
            message = 'Selection requires an explicit nonempty unique candidate roster.'
            raise FixedSelectionError(message)
        if (
            isinstance(self.minimum_coverage, bool)
            or not math.isfinite(self.minimum_coverage)
            or not 0 < self.minimum_coverage <= 1
        ):
            message = 'Selection coverage must be finite and in (0, 1].'
            raise FixedSelectionError(message)
        if self.tie_breaker != 'candidate_id' or self.failure_policy != 'require_common_cohort':
            message = 'Only lexical ties and a shared exact comparison cohort are supported.'
            raise FixedSelectionError(message)


@dataclass(frozen=True)
class ValidationLoss:
    """Per-sample loss and coverage in one inner validation or outer test partition."""

    fold_id: int
    total_sample_count: int
    eligible_sample_count: int
    coverage: float
    mean_loss: float | None
    samples: tuple[SampleCurveLoss, ...]
    reason: Literal['insufficient_coverage'] | None


@dataclass(frozen=True)
class InnerCandidateScore:
    """One candidate's complete inner-held-out evidence under an outer partition."""

    candidate_id: str
    folds: tuple[ValidationLoss, ...]
    mean_loss: float | None


@dataclass(frozen=True)
class LockedCandidateChoice:
    """A candidate chosen exclusively from inner validation, before outer scoring."""

    kind: Literal['atomic', 'ensemble']
    candidate_id: str | None
    inner_scores: tuple[InnerCandidateScore, ...]
    reason: Literal['no_registered_candidates', 'insufficient_inner_coverage'] | None


@dataclass(frozen=True)
class OuterCandidateAssessment:
    """Locked candidate and its single outer test assessment."""

    choice: LockedCandidateChoice
    assessment: ValidationLoss | None


@dataclass(frozen=True)
class OuterSelectionResult:
    """Atomic and ensemble choices assessed on the same untouched outer groups."""

    fold_id: int
    atomic: OuterCandidateAssessment
    ensemble: OuterCandidateAssessment


@dataclass(frozen=True)
class SelectionProtocolAssessment:
    """Outer evidence for a selection strategy, without a post-hoc winning model."""

    kind: Literal['atomic', 'ensemble']
    mean_outer_loss: float | None
    total_sample_count: int
    eligible_sample_count: int
    selected_counts: tuple[tuple[str, int], ...]
    failed_fold_count: int

    @property
    def status(self) -> Literal['computed', 'insufficient_evidence']:
        """Require complete assessed folds before reporting strategy performance."""
        return 'computed' if self.mean_outer_loss is not None else 'insufficient_evidence'


@dataclass(frozen=True)
class FixedNestedSelection:
    """Reproducible nested evidence restricted to untrained fixed candidates."""

    plan: FixedSelectionPlan
    splits: NestedGroupFolds
    folds: tuple[OuterSelectionResult, ...]
    protocols: tuple[SelectionProtocolAssessment, ...]
    method: Literal['fixed_candidate_nested_selection_v1'] = 'fixed_candidate_nested_selection_v1'

    @property
    def status(self) -> Literal['computed', 'insufficient_evidence']:
        """Report whether either registered strategy has complete outer evidence."""
        return (
            'computed'
            if any(item.status == 'computed' for item in self.protocols)
            else 'insufficient_evidence'
        )


@dataclass(frozen=True)
class _SelectionContext:
    plan: FixedSelectionPlan
    splits: NestedGroupFolds
    losses: Mapping[str, Mapping[SampleKey, SampleCurveLoss]]
    kinds: Mapping[str, Literal['atomic', 'ensemble']]


def select_fixed_retention_candidates(
    result: RetentionRunResult,
    *,
    plan: FixedSelectionPlan,
) -> FixedNestedSelection:
    """Select fixed atomics/ensembles using only inner held-out sample losses.

    This function does not fit or tune candidates, boundaries, weights, or gates.
    Such learned candidates must use a separate training API and are rejected.
    Folds use the full declared sample roster. All candidates share an exact
    common point cohort and registered exact-point or observed-endpoint integral loss.
    Coverage denominators include samples with missing targets or failed inputs.
    Outer targets never select a candidate; no outer-error leaderboard is used
    to recommend a final function. Outputs assess the two selection strategies.
    """
    candidates = {candidate.id: candidate for candidate in result.plan.evaluation.candidates}
    if set(plan.candidate_ids) - set(candidates):
        message = 'Selection references candidates absent from the executed evaluation plan.'
        raise FixedSelectionError(message)
    for identifier in plan.candidate_ids:
        candidate = candidates[identifier]
        if isinstance(candidate, RangeGatedCurveCandidate) and candidate.provenance.kind != 'fixed':
            message = (
                'Learned ensembles require nested fitting and cannot use fixed-candidate selection.'
            )
            raise FixedSelectionError(message)
    roster = tuple(
        GroupedSample(
            cast('str', sample['source_id']),
            cast('str', sample['sample_id']),
            cast('str | None', sample['profile_id']),
        )
        for sample in object_records(result.plan.dataset.document['samples'])
    )
    splits = build_nested_group_folds(roster, plan=plan.folds)
    kinds: dict[str, Literal['atomic', 'ensemble']] = {
        identifier: 'ensemble'
        if isinstance(candidates[identifier], RangeGatedCurveCandidate)
        else 'atomic'
        for identifier in plan.candidate_ids
    }
    if splits.status != 'computed':
        return FixedNestedSelection(plan, splits, (), ())
    cohort_records = run_candidate_comparisons(result, plan.candidate_ids)
    common = build_retention_cohorts(cohort_records).common
    losses = {
        cohort.candidate_id: {
            (loss.source_id, loss.sample_id): loss
            for loss in evaluate_selection_loss(cohort.comparisons, plan=plan.loss)
        }
        for cohort in common
    }
    context = _SelectionContext(plan, splits, losses, kinds)
    folds = tuple(
        OuterSelectionResult(
            outer.fold_id,
            _outer_assessment(context, outer, 'atomic'),
            _outer_assessment(context, outer, 'ensemble'),
        )
        for outer in splits.folds
    )
    protocols = tuple(
        _protocol_assessment(folds, kind, len(roster)) for kind in ('atomic', 'ensemble')
    )
    return FixedNestedSelection(plan, splits, folds, protocols)


def _outer_assessment(
    context: _SelectionContext,
    outer: OuterGroupFold,
    kind: Literal['atomic', 'ensemble'],
) -> OuterCandidateAssessment:
    identifiers = sorted(
        identifier for identifier, candidate_kind in context.kinds.items() if candidate_kind == kind
    )
    scores = tuple(_inner_score(context, outer.inner, identifier) for identifier in identifiers)
    valid = [score for score in scores if score.mean_loss is not None]
    if not valid:
        reason: Literal['no_registered_candidates', 'insufficient_inner_coverage'] = (
            'no_registered_candidates' if not identifiers else 'insufficient_inner_coverage'
        )
        return OuterCandidateAssessment(LockedCandidateChoice(kind, None, scores, reason), None)
    selected = min(valid, key=lambda score: (cast('float', score.mean_loss), score.candidate_id))
    choice = LockedCandidateChoice(kind, selected.candidate_id, scores, None)
    assessment = _validation_loss(
        context,
        selected.candidate_id,
        _samples_in(context.splits, outer.test_groups),
        outer.fold_id,
    )
    return OuterCandidateAssessment(choice, assessment)


def _inner_score(
    context: _SelectionContext,
    folds: Sequence[InnerGroupFold],
    identifier: str,
) -> InnerCandidateScore:
    evidence = tuple(
        _validation_loss(
            context, identifier, _samples_in(context.splits, fold.validation_groups), fold.fold_id
        )
        for fold in folds
    )
    samples = [sample for fold in evidence for sample in fold.samples if sample.loss is not None]
    mean = (
        None
        if any(fold.mean_loss is None for fold in evidence)
        else (mean_finite_losses([cast('float', sample.loss) for sample in samples]))
    )
    return InnerCandidateScore(identifier, evidence, mean)


def _validation_loss(
    context: _SelectionContext,
    identifier: str,
    samples: tuple[SampleKey, ...],
    fold_id: int,
) -> ValidationLoss:
    records = tuple(
        context.losses[identifier].get(
            sample, SampleCurveLoss(*sample, 0, None, 'insufficient_points')
        )
        for sample in samples
    )
    valid = [record for record in records if record.loss is not None]
    coverage = len(valid) / len(samples) if samples else 0.0
    if not valid or coverage < context.plan.minimum_coverage:
        return ValidationLoss(
            fold_id, len(samples), len(valid), coverage, None, records, 'insufficient_coverage'
        )
    mean = mean_finite_losses([cast('float', record.loss) for record in valid])
    return ValidationLoss(fold_id, len(samples), len(valid), coverage, mean, records, None)


def _samples_in(splits: NestedGroupFolds, groups: Sequence[GroupKey]) -> tuple[SampleKey, ...]:
    selected = set(groups)
    return tuple(
        sorted(
            sample
            for group in splits.groups
            if group.group_id in selected
            for sample in group.samples
        )
    )


def _protocol_assessment(
    folds: Sequence[OuterSelectionResult],
    kind: Literal['atomic', 'ensemble'],
    total: int,
) -> SelectionProtocolAssessment:
    assessments = [fold.atomic if kind == 'atomic' else fold.ensemble for fold in folds]
    failed = sum(
        item.assessment is None or item.assessment.mean_loss is None for item in assessments
    )
    values = [
        sample
        for item in assessments
        if item.assessment is not None
        for sample in item.assessment.samples
        if sample.loss is not None
    ]
    mean = (
        mean_finite_losses([cast('float', sample.loss) for sample in values])
        if not failed and values
        else None
    )
    counts = Counter(
        item.choice.candidate_id for item in assessments if item.choice.candidate_id is not None
    )
    return SelectionProtocolAssessment(
        kind, mean, total, len(values), tuple(sorted(counts.items())), failed
    )
