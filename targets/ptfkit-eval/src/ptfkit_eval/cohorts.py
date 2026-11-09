"""Explicit maximal and common cohorts for compatible retention candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .documents import object_mapping
from .metrics import RetentionComparison, RetentionErrorSummary, summarize_retention_errors
from .water import canonical_water_contract


if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from .contracts import TargetSpec
    from .runner import RetentionRunResult


class RetentionCohortError(ValueError):
    """Raised when candidate cohorts do not share one scientific protocol."""


@dataclass(frozen=True, kw_only=True)
class RetentionCandidateComparisons:
    """Eligible predictions for one dataset, target contract, and protocol.

    The protocol identifier must identify the reviewed operational definition
    and comparison policy. A matching name cannot prove compatibility by itself;
    upstream eligibility remains required. Empty candidates must be included.
    """

    candidate_id: str
    dataset_id: str
    protocol_id: str
    target: TargetSpec
    comparisons: tuple[RetentionComparison, ...]


@dataclass(frozen=True)
class CohortPointExclusion:
    """One eligible prediction omitted from the common comparison grid."""

    comparison: RetentionComparison
    code: Literal['point_not_shared_by_all_candidates'] = 'point_not_shared_by_all_candidates'


@dataclass(frozen=True)
class RetentionCohort:
    """One candidate's immutable comparisons and descriptive summary."""

    candidate_id: str
    kind: Literal['maximal', 'common']
    comparisons: tuple[RetentionComparison, ...]
    exclusions: tuple[CohortPointExclusion, ...]
    summary: RetentionErrorSummary | None

    @property
    def status(self) -> Literal['ready', 'empty_cohort']:
        """Distinguish an empty cohort from a zero-error result."""
        return 'empty_cohort' if self.summary is None else 'ready'


@dataclass(frozen=True)
class RetentionCohortSet:
    """Comparable maximal and common cohorts in sorted candidate order."""

    dataset_id: str
    protocol_id: str
    target: TargetSpec
    maximal: tuple[RetentionCohort, ...]
    common: tuple[RetentionCohort, ...]


def run_candidate_comparisons(
    result: RetentionRunResult, candidate_ids: Iterable[str]
) -> tuple[RetentionCandidateComparisons, ...]:
    """Recover an explicit candidate roster from already eligible run decisions."""
    identifiers = tuple(candidate_ids)
    known = {candidate.id for candidate in result.plan.evaluation.candidates}
    if not identifiers or len(set(identifiers)) != len(identifiers) or set(identifiers) - known:
        message = 'Run comparison records require a nonempty unique roster of known candidates.'
        raise RetentionCohortError(message)
    return tuple(
        RetentionCandidateComparisons(
            candidate_id=identifier,
            dataset_id=result.plan.dataset.dataset_id,
            protocol_id=str(object_mapping(result.plan.document['protocol'])['id']),
            target=result.plan.dataset.target,
            comparisons=tuple(
                point.comparison
                for point in result.points
                if point.candidate_id == identifier and point.comparison is not None
            ),
        )
        for identifier in sorted(identifiers)
    )


def build_retention_cohorts(
    candidates: Iterable[RetentionCandidateComparisons],
) -> RetentionCohortSet:
    """Retain all eligible points maximally, and their exact intersection commonly.

    Common points share source, sample, and suction in kPa across every declared
    candidate. All candidates must have the same dataset, target, and protocol.
    Observed values and profile identity must agree wherever records overlap.
    No prediction value or error participates in membership selection. An empty
    candidate makes every common cohort empty; it is never silently removed.
    """
    ordered = sorted(candidates, key=lambda candidate: candidate.candidate_id)
    if not ordered:
        message = 'At least one retention candidate must be declared.'
        raise RetentionCohortError(message)
    _validate_contracts(ordered)
    indexes = [_point_index(candidate.comparisons) for candidate in ordered]
    _validate_observations(indexes)
    common_keys = set(indexes[0]).intersection(*(set(index) for index in indexes[1:]))
    maximal: list[RetentionCohort] = []
    common: list[RetentionCohort] = []
    for candidate, index in zip(ordered, indexes, strict=True):
        points = tuple(index[key] for key in sorted(index))
        shared = tuple(index[key] for key in sorted(common_keys))
        exclusions = tuple(
            CohortPointExclusion(index[key]) for key in sorted(index) if key not in common_keys
        )
        maximal.append(_cohort(candidate.candidate_id, 'maximal', points, ()))
        common.append(_cohort(candidate.candidate_id, 'common', shared, exclusions))
    reference = ordered[0]
    return RetentionCohortSet(
        reference.dataset_id, reference.protocol_id, reference.target, tuple(maximal), tuple(common)
    )


def _validate_contracts(candidates: list[RetentionCandidateComparisons]) -> None:
    reference = candidates[0]
    seen: set[str] = set()
    for candidate in candidates:
        if any(
            not identifier.strip()
            for identifier in (candidate.candidate_id, candidate.dataset_id, candidate.protocol_id)
        ):
            message = 'Candidate, dataset, and protocol identifiers must be nonempty.'
            raise RetentionCohortError(message)
        if candidate.candidate_id in seen:
            message = f'Duplicate candidate identifier: {candidate.candidate_id!r}.'
            raise RetentionCohortError(message)
        seen.add(candidate.candidate_id)
        if any(
            point.water_quantity != candidate.target.quantity for point in candidate.comparisons
        ):
            message = 'Comparison water quantities must match the candidate target.'
            raise RetentionCohortError(message)
        if (candidate.dataset_id, candidate.protocol_id, candidate.target) != (
            reference.dataset_id,
            reference.protocol_id,
            reference.target,
        ):
            message = 'Retention candidates must share dataset, protocol, and target contracts.'
            raise RetentionCohortError(message)
    target = reference.target
    try:
        unit, denominator = canonical_water_contract(target.quantity)
    except ValueError as error:
        raise RetentionCohortError(str(error)) from error
    if (
        target.unit != unit
        or target.denominator_basis != denominator
        or not target.material_basis.strip()
    ):
        message = 'Retention cohorts require canonical volumetric or gravimetric water contracts.'
        raise RetentionCohortError(message)


def _point_index(
    points: tuple[RetentionComparison, ...],
) -> dict[tuple[str, str, float], RetentionComparison]:
    if points:
        summarize_retention_errors(points)
    return {(point.source_id, point.sample_id, point.suction_kpa): point for point in points}


def _validate_observations(
    indexes: Sequence[Mapping[tuple[str, str, float], RetentionComparison]],
) -> None:
    observations: dict[tuple[str, str, float], float] = {}
    profiles: dict[tuple[str, str], str | None] = {}
    for index in indexes:
        for key, point in index.items():
            if key in observations and observations[key] != point.observed:
                message = f'Observed water content differs between candidates at {key!r}.'
                raise RetentionCohortError(message)
            sample = (point.source_id, point.sample_id)
            if sample in profiles and profiles[sample] != point.profile_id:
                message = f'Profile identity differs between candidates for {sample!r}.'
                raise RetentionCohortError(message)
            observations[key] = point.observed
            profiles[sample] = point.profile_id


def _cohort(
    candidate_id: str,
    kind: Literal['maximal', 'common'],
    points: tuple[RetentionComparison, ...],
    exclusions: tuple[CohortPointExclusion, ...],
) -> RetentionCohort:
    return RetentionCohort(
        candidate_id,
        kind,
        points,
        exclusions,
        summarize_retention_errors(points) if points else None,
    )
