"""Post-selection input envelopes and common-cohort errors within nested folds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .applicability import EmpiricalDomainPlan, RunEmpiricalDomain, assess_retention_applicability
from .cohorts import build_retention_cohorts, run_candidate_comparisons
from .documents import EvaluationDocumentError
from .losses import SampleCurveLoss, evaluate_selection_loss, mean_finite_losses
from .uncertainty import RetentionBootstrapResult, bootstrap_retention_errors


if TYPE_CHECKING:
    from .folds import GroupKey, NestedGroupFolds, SampleKey
    from .losses import SelectionLossPlan
    from .metrics import RetentionComparison
    from .runner import RetentionRunResult
    from .selection import FixedNestedSelection


DomainStatus = Literal['inside', 'outside', 'excluded_input', 'insufficient_evidence']
_STATUSES: tuple[DomainStatus, ...] = (
    'inside',
    'outside',
    'excluded_input',
    'insufficient_evidence',
)


@dataclass(frozen=True, kw_only=True)
class NestedDomainPlan:
    """Diagnostic-only evidence gate; grouping follows the resolved nested split."""

    minimum_training_groups: int
    method: Literal['nested_training_input_envelope_v1'] = 'nested_training_input_envelope_v1'
    composite_rule: Literal['all_registered_members'] = 'all_registered_members'

    def __post_init__(self) -> None:
        """Reject unsupported rules without inspecting target or input values."""
        if (
            isinstance(self.minimum_training_groups, bool)
            or not isinstance(self.minimum_training_groups, int)
            or self.minimum_training_groups < 1
            or self.method != 'nested_training_input_envelope_v1'
            or self.composite_rule != 'all_registered_members'
        ):
            message = 'Nested input domains require a positive group gate and supported rules.'
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class NestedDomainSample:
    """Conservative all-member input status, with no target-dependent decision."""

    source_id: str
    sample_id: str
    status: DomainStatus
    member_statuses: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class NestedDomainStratum:
    """Common-cohort descriptive errors and exact-grid loss for one input stratum."""

    status: DomainStatus
    samples: tuple[SampleKey, ...]
    confidence: RetentionBootstrapResult
    loss_samples: tuple[SampleCurveLoss, ...]
    mean_log_pressure_loss: float | None

    @property
    def total_sample_count(self) -> int:
        """Keep missing targets and excluded inputs in coverage denominators."""
        return len(self.samples)

    @property
    def eligible_loss_sample_count(self) -> int:
        """Count only complete registered pressure-domain losses."""
        return sum(sample.loss is not None for sample in self.loss_samples)


@dataclass(frozen=True)
class NestedFoldDomain:
    """One candidate's envelope and diagnostics in one inner/outer holdout."""

    outer_fold_id: int
    inner_fold_id: int | None
    partition: Literal['inner_validation', 'outer_test']
    domain: RunEmpiricalDomain
    samples: tuple[NestedDomainSample, ...]
    strata: tuple[NestedDomainStratum, ...]
    selected_by_inner_validation: bool


@dataclass(frozen=True)
class NestedApplicabilityResult:
    """Post-selection diagnostics; no evidence feeds back into candidate choice."""

    plan: NestedDomainPlan
    folds: tuple[NestedFoldDomain, ...]
    reason: str | None
    method: str = 'nested_training_input_envelope_v1'

    @property
    def status(self) -> str:
        """Report missing split evidence separately from domain evidence failures."""
        return 'computed' if self.reason is None else 'insufficient_evidence'


@dataclass(frozen=True)
class _FoldRequest:
    outer_id: int
    inner_id: int | None
    training: tuple[GroupKey, ...]
    held_out: tuple[GroupKey, ...]


def diagnose_nested_applicability(
    result: RetentionRunResult, *, policy: NestedDomainPlan
) -> NestedApplicabilityResult:
    """Fit only each fold's training inputs after nested choices are locked.

    Every registered candidate uses its own member envelopes, with a complete
    common comparison grid across the selection roster. All registered members
    must be inside to label a sample inside; input failures and insufficient
    training evidence have priority over outside/inside. This conservative
    sample-level rule does not depend on which pressures have observed targets.
    Metric confidence intervals are conditional descriptive cluster intervals;
    they do not refit envelopes or repeat model selection within a replicate.
    """
    selection = result.selection
    if selection is None:
        message = 'Nested applicability requires completed nested selection evidence.'
        raise EvaluationDocumentError(message)
    if selection.splits.status != 'computed':
        return NestedApplicabilityResult(policy, (), selection.splits.reason)
    comparisons = _common_comparisons(result, selection)
    folds = tuple(
        _diagnose_fold(
            result,
            selection=selection,
            policy=policy,
            request=request,
            identifier=identifier,
            comparisons=comparisons[identifier],
        )
        for request in _fold_requests(selection.splits)
        for identifier in sorted(selection.plan.candidate_ids)
    )
    return NestedApplicabilityResult(policy, folds, None)


def _fold_requests(splits: NestedGroupFolds) -> tuple[_FoldRequest, ...]:
    return tuple(
        request
        for outer in splits.folds
        for request in (
            _FoldRequest(outer.fold_id, None, outer.training_groups, outer.test_groups),
            *(
                _FoldRequest(
                    outer.fold_id, inner.fold_id, inner.training_groups, inner.validation_groups
                )
                for inner in outer.inner
            ),
        )
    )


def _common_comparisons(
    result: RetentionRunResult, selection: FixedNestedSelection
) -> dict[str, tuple[RetentionComparison, ...]]:
    cohorts = build_retention_cohorts(
        run_candidate_comparisons(result, selection.plan.candidate_ids)
    ).common
    return {cohort.candidate_id: cohort.comparisons for cohort in cohorts}


def _diagnose_fold(
    result: RetentionRunResult,
    *,
    selection: FixedNestedSelection,
    policy: NestedDomainPlan,
    request: _FoldRequest,
    identifier: str,
    comparisons: tuple[RetentionComparison, ...],
) -> NestedFoldDomain:
    domain = assess_retention_applicability(
        result.plan,
        policy=EmpiricalDomainPlan(
            candidate_id=identifier,
            training_groups=request.training,
            test_groups=request.held_out,
            minimum_training_groups=policy.minimum_training_groups,
            grouping=selection.splits.effective_grouping,
        ),
    )
    samples = combine_member_input_statuses(domain)
    strata = summarize_domain_strata(
        result, samples=samples, comparisons=comparisons, loss_plan=selection.plan.loss
    )
    selected = False
    if request.inner_id is None:
        outer = next(fold for fold in selection.folds if fold.fold_id == request.outer_id)
        selected = identifier in (
            outer.atomic.choice.candidate_id,
            outer.ensemble.choice.candidate_id,
        )
    return NestedFoldDomain(
        request.outer_id,
        request.inner_id,
        'outer_test' if request.inner_id is None else 'inner_validation',
        domain,
        samples,
        strata,
        selected,
    )


def combine_member_input_statuses(domain: RunEmpiricalDomain) -> tuple[NestedDomainSample, ...]:
    """Combine only input evidence using the registered conservative all-member rule."""
    members = [
        {(sample.source_id, sample.sample_id): sample.status for sample in member.test_samples}
        for member in domain.members
    ]
    output = []
    for key in sorted(members[0]):
        statuses = tuple(
            (member.member_id, lookup[key])
            for member, lookup in zip(
                domain.members,
                members,
                strict=True,
            )
        )
        values = {status for _, status in statuses}
        status: DomainStatus = (
            'excluded_input'
            if 'excluded_input' in values
            else 'insufficient_evidence'
            if 'insufficient_evidence' in values
            else 'outside'
            if 'outside' in values
            else 'inside'
        )
        output.append(NestedDomainSample(*key, status, statuses))
    return tuple(output)


def summarize_domain_strata(
    result: RetentionRunResult,
    *,
    samples: tuple[NestedDomainSample, ...],
    comparisons: tuple[RetentionComparison, ...],
    loss_plan: SelectionLossPlan,
) -> tuple[NestedDomainStratum, ...]:
    """Summarize all four input strata without changing their sample rosters."""
    return tuple(_stratum(result, loss_plan, status, samples, comparisons) for status in _STATUSES)


def _stratum(
    result: RetentionRunResult,
    loss_plan: SelectionLossPlan,
    status: DomainStatus,
    samples: tuple[NestedDomainSample, ...],
    comparisons: tuple[RetentionComparison, ...],
) -> NestedDomainStratum:
    keys = tuple(
        (sample.source_id, sample.sample_id) for sample in samples if sample.status == status
    )
    selected = set(keys)
    points = tuple(point for point in comparisons if (point.source_id, point.sample_id) in selected)
    losses = {
        (sample.source_id, sample.sample_id): sample
        for sample in evaluate_selection_loss(points, plan=loss_plan)
    }
    records = tuple(
        losses.get(key, SampleCurveLoss(*key, 0, None, 'insufficient_points')) for key in keys
    )
    values = [record.loss for record in records if record.loss is not None]
    mean = mean_finite_losses(values) if values else None
    return NestedDomainStratum(
        status,
        keys,
        bootstrap_retention_errors(points, plan=result.plan.bootstrap),
        records,
        mean,
    )
