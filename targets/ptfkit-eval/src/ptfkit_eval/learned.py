"""Nested training of constant weights, finite-grid switches and blend intervals."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from itertools import pairwise
from typing import TYPE_CHECKING, Literal, TypeAlias, cast

from .blend_grid import BlendGridFit, BlendGridPlan, BlendIntervalScore, blend_left_weight
from .cohorts import (
    RetentionCandidateComparisons,
    build_retention_cohorts,
    run_candidate_comparisons,
)
from .contracts import FixedPointPrediction, FunctionCurveCandidate, RangeGatedCurveCandidate
from .documents import EvaluationDocumentError, object_records
from .folds import (
    GroupedSample,
    NestedGroupFolds,
    build_group_holdout,
    build_nested_group_folds,
)
from .hard_switch import (
    HardSwitchBoundaryScore,
    HardSwitchGridFit,
    HardSwitchGridPlan,
    hard_switch_uses_left,
)
from .losses import (
    SampleCurveLoss,
    evaluate_log_pressure_loss,
    log10_pressure_span,
    mean_finite_losses,
)
from .selection import (
    FixedSelectionPlan,
    SelectionProtocolAssessment,
    ValidationLoss,
)
from .sigmoid_grid import (
    SigmoidGridFit,
    SigmoidGridPlan,
    SigmoidParameterScore,
    sigmoid_left_weight,
)


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from .cohorts import RetentionCohortSet
    from .contracts import EvaluationPlan
    from .folds import GroupKey, GroupMembership, InnerGroupFold, OuterGroupFold, SampleKey
    from .metrics import RetentionComparison
    from .nested_applicability import NestedDomainPlan
    from .runner import RetentionRunResult


@dataclass(frozen=True, kw_only=True)
class ConvexPairPlan:
    """A fixed two-member roster and preregistered training evidence gates."""

    id: str
    left_candidate_id: str
    right_candidate_id: str
    minimum_training_groups: int
    minimum_mean_squared_contrast: float
    method: Literal['constant_convex_pair_log_pressure_v1'] = 'constant_convex_pair_log_pressure_v1'

    def __post_init__(self) -> None:
        """Reject ambiguous identities or unsupported training choices."""
        if (
            any(
                not value.strip()
                for value in (self.id, self.left_candidate_id, self.right_candidate_id)
            )
            or self.left_candidate_id == self.right_candidate_id
            or self.id in (self.left_candidate_id, self.right_candidate_id)
            or isinstance(self.minimum_training_groups, bool)
            or not isinstance(self.minimum_training_groups, int)
            or self.minimum_training_groups < 1
            or isinstance(self.minimum_mean_squared_contrast, bool)
            or not math.isfinite(self.minimum_mean_squared_contrast)
            or self.minimum_mean_squared_contrast <= 0
            or self.method != 'constant_convex_pair_log_pressure_v1'
        ):
            message = (
                'Convex pair training requires distinct identities and positive evidence gates.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True, kw_only=True)
class LearnedSelectionPlan:
    """Fixed candidate roster plus explicitly registered trainable ensembles."""

    fixed: FixedSelectionPlan
    ensembles: tuple[ConvexPairPlan | HardSwitchGridPlan | BlendGridPlan | SigmoidGridPlan, ...]
    empirical_domains: NestedDomainPlan | None = None
    method: Literal['nested_convex_pair_selection_v1', 'nested_two_curve_selection_v1'] = (
        'nested_convex_pair_selection_v1'
    )

    def __post_init__(self) -> None:
        """Require a nonempty unique learned roster with registered fixed members."""
        if self.method == 'nested_convex_pair_selection_v1' and any(
            isinstance(ensemble, (HardSwitchGridPlan, BlendGridPlan, SigmoidGridPlan))
            for ensemble in self.ensembles
        ):
            message = 'Grid-trained transitions require nested_two_curve_selection_v1.'
            raise EvaluationDocumentError(message)
        identifiers = [ensemble.id for ensemble in self.ensembles]
        if (
            not identifiers
            or len(set(identifiers)) != len(identifiers)
            or set(identifiers).intersection(self.fixed.candidate_ids)
            or any(
                {ensemble.left_candidate_id, ensemble.right_candidate_id}
                - set(self.fixed.candidate_ids)
                for ensemble in self.ensembles
            )
            or self.method
            not in ('nested_convex_pair_selection_v1', 'nested_two_curve_selection_v1')
            or self.fixed.empirical_domains is not None
        ):
            message = (
                'Learned ensembles require unique IDs and members in the fixed candidate roster.'
            )
            raise EvaluationDocumentError(message)
        if any(
            isinstance(ensemble, HardSwitchGridPlan)
            and any(
                not self.fixed.loss.lower_suction_kpa < boundary < self.fixed.loss.upper_suction_kpa
                for boundary in ensemble.boundary_grid_kpa
            )
            for ensemble in self.ensembles
        ):
            message = 'Every learned hard-switch boundary must be strictly inside the loss domain.'
            raise EvaluationDocumentError(message)
        if any(
            isinstance(ensemble, BlendGridPlan)
            and any(
                not self.fixed.loss.lower_suction_kpa
                < lower
                < upper
                < self.fixed.loss.upper_suction_kpa
                for lower, upper in ensemble.interval_grid_kpa
            )
            for ensemble in self.ensembles
        ):
            message = 'Every learned blend interval must be strictly inside the loss domain.'
            raise EvaluationDocumentError(message)

        if any(
            isinstance(ensemble, SigmoidGridPlan)
            and any(
                not self.fixed.loss.lower_suction_kpa < center < self.fixed.loss.upper_suction_kpa
                for center, _ in ensemble.parameter_grid
            )
            for ensemble in self.ensembles
        ):
            message = 'Every sigmoid center must be strictly inside the selection loss domain.'
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class ConvexPairFit:
    """Training-only fitted weight, exact usable sample keys, and failure evidence."""

    plan: ConvexPairPlan
    training_groups: tuple[GroupKey, ...]
    training_sample_count: int
    usable_samples: tuple[SampleKey, ...]
    usable_group_count: int
    coverage: float
    mean_squared_contrast: float | None
    left_weight: float | None
    training_loss: float | None
    reason: str | None

    @property
    def status(self) -> str:
        """Boundary weights are valid; unsupported weights are never defaulted."""
        return 'fitted' if self.left_weight is not None else 'insufficient_evidence'


LearnedFit: TypeAlias = ConvexPairFit | HardSwitchGridFit | BlendGridFit | SigmoidGridFit


@dataclass(frozen=True)
class LearnedInnerEvidence:
    """Each fold retains the training fit and disjoint validation loss."""

    fold_id: int
    fit: LearnedFit | None
    assessment: ValidationLoss
    predictions: tuple[RetentionComparison, ...]


@dataclass(frozen=True)
class LearnedCandidateScore:
    """A fixed or trainable candidate's complete inner-held-out evidence."""

    candidate_id: str
    folds: tuple[LearnedInnerEvidence, ...]
    mean_loss: float | None


@dataclass(frozen=True)
class LearnedOuterAssessment:
    """A locked choice, optional outer-training refit, and untouched test loss."""

    kind: Literal['atomic', 'ensemble']
    candidate_id: str | None
    inner_scores: tuple[LearnedCandidateScore, ...]
    outer_fit: LearnedFit | None
    assessment: ValidationLoss | None
    reason: str | None
    predictions: tuple[RetentionComparison, ...] = ()


@dataclass(frozen=True)
class LearnedOuterFold:
    """Separate atomic/ensemble strategies in one external holdout."""

    fold_id: int
    atomic: LearnedOuterAssessment
    ensemble: LearnedOuterAssessment


@dataclass(frozen=True)
class LearnedNestedSelection:
    """Training provenance and assessed strategies; no final outer-error winner."""

    plan: LearnedSelectionPlan
    splits: NestedGroupFolds
    folds: tuple[LearnedOuterFold, ...]
    protocols: tuple[SelectionProtocolAssessment, ...]
    method: str = 'nested_convex_pair_selection_v1'

    @property
    def status(self) -> str:
        """Require complete outer evidence for at least one strategy."""
        return (
            'computed'
            if any(item.status == 'computed' for item in self.protocols)
            else 'insufficient_evidence'
        )


@dataclass(frozen=True)
class _Context:
    plan: LearnedSelectionPlan
    splits: NestedGroupFolds
    points: Mapping[str, tuple[RetentionComparison, ...]]
    ensembles: Mapping[str, ConvexPairPlan | HardSwitchGridPlan | BlendGridPlan | SigmoidGridPlan]
    kinds: Mapping[str, Literal['atomic', 'ensemble']]


def select_learned_retention_candidates(
    result: RetentionRunResult, *, plan: LearnedSelectionPlan
) -> LearnedNestedSelection:
    """Fit each inner training fold, lock a candidate, refit only outer training.

    A registration learns a constant convex weight, finite-grid hard-switch
    boundary or blend interval under a fixed axis/weighting rule. It minimizes the
    same sample-balanced exact-grid log-pressure MSE used in validation. Member
    identities and boundary ownership are fixed; no predictor-dependent gate
    is learned. Fixed composites may compete; trainable members are atomic.
    """
    validate_learned_selection_candidates(plan, result.plan.evaluation)
    candidates = {candidate.id: candidate for candidate in result.plan.evaluation.candidates}
    roster = tuple(
        GroupedSample(
            cast('str', sample['source_id']),
            cast('str', sample['sample_id']),
            cast('str | None', sample['profile_id']),
        )
        for sample in object_records(result.plan.dataset.document['samples'])
    )
    kinds: dict[str, Literal['atomic', 'ensemble']] = {
        identifier: 'atomic'
        if isinstance(candidates[identifier], FunctionCurveCandidate)
        else 'ensemble'
        for identifier in plan.fixed.candidate_ids
    }
    return select_grouped_forecast_candidates(
        run_candidate_comparisons(result, plan.fixed.candidate_ids),
        samples=roster,
        candidate_kinds=kinds,
        plan=plan,
    )


def select_grouped_forecast_candidates(
    candidates: Iterable[RetentionCandidateComparisons],
    *,
    samples: Iterable[GroupedSample],
    candidate_kinds: Mapping[str, Literal['atomic', 'ensemble']],
    plan: LearnedSelectionPlan,
) -> LearnedNestedSelection:
    """Select supplied eligible forecasts without executing a native PTF.

    Callers own forecast provenance and scientific eligibility, as for retention
    cohorts. Supply every sample, including samples without eligible forecasts.
    Fixed forecasts must not have been fitted using held-out observations. The
    native run entry point additionally validates registered member provenance.
    Candidate kinds describe only the fixed roster; learned pairs are ensembles.
    """
    records = tuple(candidates)
    roster = tuple(samples)
    _validate_forecast_sample_identities(roster)
    splits = build_nested_group_folds(roster, plan=plan.fixed.folds)
    context = _forecast_context(records, roster, candidate_kinds, plan, splits)
    if splits.status != 'computed':
        return LearnedNestedSelection(plan, splits, (), (), method=plan.method)
    folds = tuple(
        LearnedOuterFold(
            outer.fold_id,
            _outer(context, outer, 'atomic'),
            _outer(context, outer, 'ensemble'),
        )
        for outer in splits.folds
    )
    protocols = tuple(_strategy(folds, kind, len(roster)) for kind in ('atomic', 'ensemble'))
    return LearnedNestedSelection(plan, splits, folds, protocols, method=plan.method)


def select_grouped_forecast_holdout(
    candidates: Iterable[RetentionCandidateComparisons],
    *,
    samples: Iterable[GroupedSample],
    candidate_kinds: Mapping[str, Literal['atomic', 'ensemble']],
    training_groups: tuple[GroupMembership, ...],
    test_groups: tuple[GroupMembership, ...],
    plan: LearnedSelectionPlan,
) -> LearnedNestedSelection:
    """Repeat full inner selection/refitting on preallocated train/test roles.

    The single external holdout is never selected by its error. Every choice,
    learned weight and boundary uses only the explicit training groups. Fixed
    forecasts must be independent of held-out targets, as in the nested API.
    The outer fold count does not apply to explicit roles; inner gates do.
    """
    records = tuple(candidates)
    roster = tuple(samples)
    _validate_forecast_sample_identities(roster)
    splits = build_group_holdout(
        roster, training_groups=training_groups, test_groups=test_groups, plan=plan.fixed.folds
    )
    context = _forecast_context(records, roster, candidate_kinds, plan, splits)
    if splits.status != 'computed':
        return LearnedNestedSelection(plan, splits, (), (), method=plan.method)
    outer = splits.folds[0]
    fold = LearnedOuterFold(0, _outer(context, outer, 'atomic'), _outer(context, outer, 'ensemble'))
    total = sum(len(group.samples) for group in test_groups)
    protocols = tuple(_strategy((fold,), kind, total) for kind in ('atomic', 'ensemble'))
    return LearnedNestedSelection(plan, splits, (fold,), protocols, method=plan.method)


def _validate_forecast_sample_identities(roster: tuple[GroupedSample, ...]) -> None:
    if len({(sample.source_id, sample.sample_id) for sample in roster}) != len(roster):
        message = 'Forecast sample roster must contain unique source-local identities.'
        raise EvaluationDocumentError(message)


def _forecast_context(
    records: tuple[RetentionCandidateComparisons, ...],
    roster: tuple[GroupedSample, ...],
    candidate_kinds: Mapping[str, Literal['atomic', 'ensemble']],
    plan: LearnedSelectionPlan,
    splits: NestedGroupFolds,
) -> _Context:
    cohorts = validate_grouped_forecast_inputs(
        records, samples=roster, candidate_kinds=candidate_kinds, plan=plan
    )
    points = {cohort.candidate_id: cohort.comparisons for cohort in cohorts.common}
    kinds = dict(candidate_kinds)
    kinds.update({ensemble.id: 'ensemble' for ensemble in plan.ensembles})
    return _Context(plan, splits, points, {item.id: item for item in plan.ensembles}, kinds)


def validate_grouped_forecast_inputs(
    records: tuple[RetentionCandidateComparisons, ...],
    *,
    samples: tuple[GroupedSample, ...],
    candidate_kinds: Mapping[str, Literal['atomic', 'ensemble']],
    plan: LearnedSelectionPlan,
) -> RetentionCohortSet:
    """Validate all supplied rows before any subset can discard invalid records."""
    roster = samples
    _validate_forecast_sample_identities(roster)
    expected = set(plan.fixed.candidate_ids)
    if (
        {item.candidate_id for item in records} != expected
        or set(candidate_kinds) != expected
        or any(kind not in ('atomic', 'ensemble') for kind in candidate_kinds.values())
    ):
        message = 'Forecast records and kinds must match the complete fixed candidate roster.'
        raise EvaluationDocumentError(message)
    if any(
        candidate_kinds[identifier] != 'atomic'
        for ensemble in plan.ensembles
        for identifier in (ensemble.left_candidate_id, ensemble.right_candidate_id)
    ):
        message = 'Trainable ensemble members must be declared atomic forecasts.'
        raise EvaluationDocumentError(message)
    identities = {(sample.source_id, sample.sample_id): sample.profile_id for sample in roster}
    for record in records:
        for point in record.comparisons:
            key = (point.source_id, point.sample_id)
            if key not in identities or identities[key] != point.profile_id:
                message = 'Forecast rows must match the declared sample and profile roster.'
                raise EvaluationDocumentError(message)
    return build_retention_cohorts(records)


def _keys(context: _Context, groups: tuple[GroupKey, ...]) -> tuple[SampleKey, ...]:
    return tuple(
        sorted(
            sample
            for group in context.splits.groups
            if group.group_id in groups
            for sample in group.samples
        )
    )


def _partition_points(
    context: _Context, identifier: str, groups: tuple[GroupKey, ...], fit: LearnedFit | None
) -> tuple[RetentionComparison, ...]:
    selected = set(_keys(context, groups))
    if identifier not in context.ensembles:
        return tuple(
            point
            for point in context.points[identifier]
            if (point.source_id, point.sample_id) in selected
        )
    if fit is None or fit.status != 'fitted':
        return ()
    ensemble = context.ensembles[identifier]
    return tuple(
        _fitted_pair_point(left, right, fit)
        for left, right in zip(
            context.points[ensemble.left_candidate_id],
            context.points[ensemble.right_candidate_id],
            strict=True,
        )
        if (left.source_id, left.sample_id) in selected
    )


def _fitted_pair_point(
    left: RetentionComparison, right: RetentionComparison, fit: LearnedFit
) -> RetentionComparison:
    if isinstance(fit, HardSwitchGridFit):
        if fit.switch_suction_kpa is None:
            message = 'Cannot predict with an unfitted hard-switch boundary.'
            raise EvaluationDocumentError(message)
        value = (
            left.predicted
            if hard_switch_uses_left(
                left.suction_kpa, fit.switch_suction_kpa, fit.plan.boundary_member
            )
            else right.predicted
        )
    elif isinstance(fit, SigmoidGridFit):
        if fit.parameters is None:
            message = 'Cannot predict with an unfitted sigmoid gate.'
            raise EvaluationDocumentError(message)
        weight = sigmoid_left_weight(left.suction_kpa, fit.parameters)
        value = weight * left.predicted + (1 - weight) * right.predicted
    elif isinstance(fit, BlendGridFit):
        if fit.interval_kpa is None:
            message = 'Cannot predict with an unfitted blend interval.'
            raise EvaluationDocumentError(message)
        weight = blend_left_weight(left.suction_kpa, fit.interval_kpa, fit.plan)
        value = weight * left.predicted + (1 - weight) * right.predicted
    else:
        if fit.left_weight is None:
            message = 'Cannot predict with an unfitted convex weight.'
            raise EvaluationDocumentError(message)
        value = fit.left_weight * left.predicted + (1 - fit.left_weight) * right.predicted
    return replace(left, predicted=value)


def _fit(context: _Context, identifier: str, groups: tuple[GroupKey, ...]) -> LearnedFit | None:
    if identifier not in context.ensembles:
        return None
    ensemble = context.ensembles[identifier]
    if isinstance(ensemble, (HardSwitchGridPlan, BlendGridPlan, SigmoidGridPlan)):
        return _fit_grid(context, ensemble, groups)
    left = _partition_points(context, ensemble.left_candidate_id, groups, None)
    right = _partition_points(context, ensemble.right_candidate_id, groups, None)
    losses = evaluate_log_pressure_loss(left, plan=context.plan.fixed.loss)
    valid = {(sample.source_id, sample.sample_id) for sample in losses if sample.loss is not None}
    sample_count = len(_keys(context, groups))
    coverage = len(valid) / sample_count if sample_count else 0.0
    group_count = sum(
        any(sample in valid for sample in group.samples)
        for group in context.splits.groups
        if group.group_id in groups
    )
    reason = None
    if group_count < ensemble.minimum_training_groups:
        reason = 'too_few_training_groups'
    elif coverage < context.plan.fixed.minimum_coverage:
        reason = 'insufficient_training_coverage'
    if reason is not None:
        return ConvexPairFit(
            ensemble,
            groups,
            sample_count,
            tuple(sorted(valid)),
            group_count,
            coverage,
            None,
            None,
            None,
            reason,
        )
    try:
        coefficients = _coefficients(context, left, right, valid)
        contrast = math.fsum(a for a, _ in coefficients) / len(coefficients)
        linear = math.fsum(b for _, b in coefficients) / len(coefficients)
    except (ArithmeticError, ValueError):
        contrast = linear = math.nan
    if not math.isfinite(contrast) or not math.isfinite(linear):
        return ConvexPairFit(
            ensemble,
            groups,
            sample_count,
            tuple(sorted(valid)),
            group_count,
            coverage,
            None,
            None,
            None,
            'nonfinite_training_objective',
        )
    if contrast <= ensemble.minimum_mean_squared_contrast:
        return ConvexPairFit(
            ensemble,
            groups,
            sample_count,
            tuple(sorted(valid)),
            group_count,
            coverage,
            contrast,
            None,
            None,
            'unidentifiable_weight',
        )
    weight = min(1.0, max(0.0, -linear / contrast))
    fitted = ConvexPairFit(
        ensemble,
        groups,
        sample_count,
        tuple(sorted(valid)),
        group_count,
        coverage,
        contrast,
        weight,
        None,
        None,
    )
    fitted_points = _partition_points(context, identifier, groups, fitted)
    fitted_losses = evaluate_log_pressure_loss(fitted_points, plan=context.plan.fixed.loss)
    objective = mean_finite_losses(
        [sample.loss for sample in fitted_losses if sample.loss is not None]
    )
    return replace(fitted, training_loss=objective)


def _fit_grid(
    context: _Context,
    ensemble: HardSwitchGridPlan | BlendGridPlan | SigmoidGridPlan,
    groups: tuple[GroupKey, ...],
) -> HardSwitchGridFit | BlendGridFit | SigmoidGridFit:
    left = _partition_points(context, ensemble.left_candidate_id, groups, None)
    right = _partition_points(context, ensemble.right_candidate_id, groups, None)
    losses = evaluate_log_pressure_loss(left, plan=context.plan.fixed.loss)
    valid = {(sample.source_id, sample.sample_id) for sample in losses if sample.loss is not None}
    sample_count = len(_keys(context, groups))
    coverage = len(valid) / sample_count if sample_count else 0.0
    group_count = sum(
        any(sample in valid for sample in group.samples)
        for group in context.splits.groups
        if group.group_id in groups
    )
    reason = (
        'too_few_training_groups'
        if group_count < ensemble.minimum_training_groups
        else 'insufficient_training_coverage'
        if coverage < context.plan.fixed.minimum_coverage
        else None
    )
    shared = (groups, sample_count, tuple(sorted(valid)), group_count, coverage)
    fit = (
        HardSwitchGridFit(ensemble, *shared, (), None, None, None, reason)
        if isinstance(ensemble, HardSwitchGridPlan)
        else SigmoidGridFit(ensemble, *shared, (), None, None, None, reason)
        if isinstance(ensemble, SigmoidGridPlan)
        else BlendGridFit(ensemble, *shared, (), None, None, None, reason)
    )
    if reason is not None:
        return fit
    choices = (
        tuple((value, value) for value in ensemble.boundary_grid_kpa)
        if isinstance(ensemble, HardSwitchGridPlan)
        else ensemble.parameter_grid
        if isinstance(ensemble, SigmoidGridPlan)
        else ensemble.interval_grid_kpa
    )
    scores = []
    for choice in choices:
        prediction = tuple(
            replace(one, predicted=_grid_prediction(one, two, ensemble, choice))
            for one, two in zip(left, right, strict=True)
            if (one.source_id, one.sample_id) in valid
        )
        evaluated = evaluate_log_pressure_loss(prediction, plan=context.plan.fixed.loss)
        objective = mean_finite_losses(
            [sample.loss for sample in evaluated if sample.loss is not None]
        )
        scores.append((choice, objective))
    ordered = sorted(scores, key=lambda item: (item[1], item[0]))
    winner, runner_up = ordered[:2]
    gap = runner_up[1] - winner[1]
    identified = gap > ensemble.minimum_loss_gap
    if isinstance(fit, HardSwitchGridFit):
        return replace(
            fit,
            scores=tuple(
                HardSwitchBoundaryScore(choice[0], objective) for choice, objective in scores
            ),
            loss_gap=gap,
            switch_suction_kpa=winner[0][0] if identified else None,
            training_loss=winner[1] if identified else None,
            reason=None if identified else 'unidentifiable_boundary',
        )
    if isinstance(fit, SigmoidGridFit):
        return replace(
            fit,
            scores=tuple(SigmoidParameterScore(choice, objective) for choice, objective in scores),
            loss_gap=gap,
            parameters=winner[0] if identified else None,
            training_loss=winner[1] if identified else None,
            reason=None if identified else 'unidentifiable_sigmoid_parameters',
        )
    return replace(
        fit,
        scores=tuple(BlendIntervalScore(choice, objective) for choice, objective in scores),
        loss_gap=gap,
        interval_kpa=winner[0] if identified else None,
        training_loss=winner[1] if identified else None,
        reason=None if identified else 'unidentifiable_blend_interval',
    )


def _grid_prediction(
    left: RetentionComparison,
    right: RetentionComparison,
    plan: HardSwitchGridPlan | BlendGridPlan | SigmoidGridPlan,
    choice: tuple[float, float],
) -> float:
    if isinstance(plan, HardSwitchGridPlan):
        return (
            left.predicted
            if hard_switch_uses_left(left.suction_kpa, choice[0], plan.boundary_member)
            else right.predicted
        )
    weight = (
        sigmoid_left_weight(left.suction_kpa, choice)
        if isinstance(plan, SigmoidGridPlan)
        else blend_left_weight(left.suction_kpa, choice, plan)
    )
    return weight * left.predicted + (1 - weight) * right.predicted


def _coefficients(
    context: _Context,
    left: tuple[RetentionComparison, ...],
    right: tuple[RetentionComparison, ...],
    valid: set[SampleKey],
) -> list[tuple[float, float]]:
    loss = context.plan.fixed.loss
    span = log10_pressure_span(loss.lower_suction_kpa, loss.upper_suction_kpa)
    samples: dict[SampleKey, list[tuple[float, float, float]]] = defaultdict(list)
    for one, two in zip(left, right, strict=True):
        key = (one.source_id, one.sample_id)
        if key in valid and loss.lower_suction_kpa <= one.suction_kpa <= loss.upper_suction_kpa:
            samples[key].append(
                (one.suction_kpa, one.predicted - two.predicted, two.predicted - two.observed)
            )
    coefficients = []
    for key in sorted(samples):
        pairs = tuple(pairwise(samples[key]))
        coefficients.append(
            tuple(
                math.fsum(
                    log10_pressure_span(p[0], q[0]) / (2 * span) * (term(p) + term(q))
                    for p, q in pairs
                )
                for term in (
                    lambda row: row[1] ** 2,
                    lambda row: row[1] * row[2],
                )
            )
        )
    return [cast('tuple[float, float]', row) for row in coefficients]


def _assess(
    context: _Context,
    identifier: str,
    groups: tuple[GroupKey, ...],
    fold_id: int,
    fit: LearnedFit | None,
) -> ValidationLoss:
    keys = _keys(context, groups)
    losses = {
        (sample.source_id, sample.sample_id): sample
        for sample in evaluate_log_pressure_loss(
            _partition_points(context, identifier, groups, fit),
            plan=context.plan.fixed.loss,
        )
    }
    samples = tuple(
        losses.get(key, SampleCurveLoss(*key, 0, None, 'insufficient_points')) for key in keys
    )
    values = [sample.loss for sample in samples if sample.loss is not None]
    coverage = len(values) / len(keys) if keys else 0.0
    mean = (
        mean_finite_losses(values)
        if values and coverage >= context.plan.fixed.minimum_coverage
        else None
    )
    return ValidationLoss(
        fold_id,
        len(keys),
        len(values),
        coverage,
        mean,
        samples,
        'insufficient_coverage' if mean is None else None,
    )


def _inner(
    context: _Context, identifier: str, folds: tuple[InnerGroupFold, ...]
) -> LearnedCandidateScore:
    evidence = []
    for fold in folds:
        fit = _fit(context, identifier, fold.training_groups)
        evidence.append(
            LearnedInnerEvidence(
                fold.fold_id,
                fit,
                _assess(context, identifier, fold.validation_groups, fold.fold_id, fit),
                _partition_points(context, identifier, fold.validation_groups, fit),
            )
        )
    values = [
        sample.loss
        for item in evidence
        for sample in item.assessment.samples
        if sample.loss is not None
    ]
    mean = (
        None
        if any(item.assessment.mean_loss is None for item in evidence)
        else mean_finite_losses(values)
    )
    return LearnedCandidateScore(identifier, tuple(evidence), mean)


def _outer(
    context: _Context, outer: OuterGroupFold, kind: Literal['atomic', 'ensemble']
) -> LearnedOuterAssessment:
    scores = tuple(
        _inner(context, identifier, outer.inner)
        for identifier in sorted(context.kinds)
        if context.kinds[identifier] == kind
    )
    valid = [score for score in scores if score.mean_loss is not None]
    if not valid:
        return LearnedOuterAssessment(kind, None, scores, None, None, 'insufficient_inner_evidence')
    selected = min(valid, key=lambda score: (cast('float', score.mean_loss), score.candidate_id))
    fit = _fit(context, selected.candidate_id, outer.training_groups)
    assessment = _assess(context, selected.candidate_id, outer.test_groups, outer.fold_id, fit)
    return LearnedOuterAssessment(
        kind,
        selected.candidate_id,
        scores,
        fit,
        assessment,
        fit.reason if fit is not None and fit.reason else assessment.reason,
        _partition_points(context, selected.candidate_id, outer.test_groups, fit),
    )


def _strategy(
    folds: tuple[LearnedOuterFold, ...], kind: Literal['atomic', 'ensemble'], total: int
) -> SelectionProtocolAssessment:
    records = [fold.atomic if kind == 'atomic' else fold.ensemble for fold in folds]
    failed = sum(item.assessment is None or item.assessment.mean_loss is None for item in records)
    values = [
        sample.loss
        for item in records
        if item.assessment is not None
        for sample in item.assessment.samples
        if sample.loss is not None
    ]
    mean = mean_finite_losses(values) if values and not failed else None
    counts = Counter(item.candidate_id for item in records if item.candidate_id is not None)
    return SelectionProtocolAssessment(
        kind, mean, total, len(values), tuple(sorted(counts.items())), failed
    )


def validate_learned_selection_candidates(
    plan: LearnedSelectionPlan, evaluation: EvaluationPlan
) -> None:
    """Validate member types and provenance at both loading and execution boundaries."""
    candidates = {candidate.id: candidate for candidate in evaluation.candidates}
    if set(plan.fixed.candidate_ids) - set(candidates):
        message = 'Learned selection references absent fixed candidates.'
        raise EvaluationDocumentError(message)
    for ensemble in plan.ensembles:
        for identifier in (ensemble.left_candidate_id, ensemble.right_candidate_id):
            candidate = candidates[identifier]
            if not isinstance(candidate, FunctionCurveCandidate) or isinstance(
                candidate.curve.prediction, FixedPointPrediction
            ):
                message = 'Trainable ensemble members must be registered atomic candidates.'
                raise EvaluationDocumentError(message)
    for identifier in plan.fixed.candidate_ids:
        candidate = candidates[identifier]
        if isinstance(candidate, RangeGatedCurveCandidate) and candidate.provenance.kind != 'fixed':
            message = 'Fixed competitors must have fixed, untrained composite provenance.'
            raise EvaluationDocumentError(message)
