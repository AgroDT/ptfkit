"""Whole-group bootstrap retraining trajectories, without inferential intervals."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from random import Random
from typing import TYPE_CHECKING, Literal, cast

from .applicability import domain_group
from .canonical import load_retention_dataset
from .cohorts import build_retention_cohorts
from .documents import EvaluationDocumentError, object_records, plain
from .learned import select_learned_retention_candidates
from .selection import FixedNestedSelection, select_fixed_retention_candidates


if TYPE_CHECKING:
    from .cohorts import RetentionCandidateComparisons
    from .folds import GroupedSample, GroupKey, GroupMembership, SampleKey
    from .learned import LearnedNestedSelection
    from .metrics import RetentionComparison
    from .runner import RetentionRunResult, RunPointDecision


_MINIMUM_RESAMPLING_COUNT = 2


@dataclass(frozen=True, kw_only=True)
class SelectionResamplingPlan:
    """Predeclared draws of the original resolved independent selection groups."""

    protocol: Literal['fixed', 'learned']
    seed: int
    n_resamples: int
    minimum_groups: int
    method: Literal['whole_group_bootstrap_retraining_sensitivity_v1'] = (
        'whole_group_bootstrap_retraining_sensitivity_v1'
    )

    def __post_init__(self) -> None:
        """Reject unsupported or implicit choices; this plan has no confidence level."""
        if (
            self.protocol not in ('fixed', 'learned')
            or self.method != 'whole_group_bootstrap_retraining_sensitivity_v1'
            or isinstance(self.seed, bool)
            or not isinstance(self.seed, int)
            or any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < _MINIMUM_RESAMPLING_COUNT
                for value in (self.n_resamples, self.minimum_groups)
            )
        ):
            message = (
                'Selection resampling requires an explicit supported protocol, '
                'seed and group/draw gates.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class GroupMultiplicity:
    """One original independent group and its bootstrap count, including zero."""

    group_id: GroupKey
    count: int


@dataclass(frozen=True)
class ResampledSample:
    """A sample occurrence, with its original group identity unchanged."""

    group_id: GroupKey
    source_id: str
    original_sample_id: str
    sample_id: str
    group_occurrence: int


@dataclass(frozen=True)
class GroupedForecastResample:
    """Supplied forecasts repeated with an auditable original-group sample map."""

    samples: tuple[GroupedSample, ...]
    candidates: tuple[RetentionCandidateComparisons, ...]
    sample_map: tuple[ResampledSample, ...]


def resample_grouped_forecasts(
    candidates: tuple[RetentionCandidateComparisons, ...],
    *,
    samples: tuple[GroupedSample, ...],
    groups: tuple[GroupMembership, ...],
    multiplicities: tuple[GroupMultiplicity, ...],
    grouping: Literal['source', 'profile'],
) -> GroupedForecastResample:
    """Materialize explicit group counts without fitting or defining a draw law.

    Resolve any missing-profile fallback before calling. Counts may include
    zeros; missing forecasts remain missing while their samples are repeated.
    Source/profile identities remain unchanged across all sample occurrences.
    This operation alone supplies neither a bootstrap law nor an interval.
    """
    if grouping not in ('source', 'profile'):
        message = 'Forecast resampling requires an explicit resolved grouping.'
        raise EvaluationDocumentError(message)
    build_retention_cohorts(candidates)
    original = {(sample.source_id, sample.sample_id): sample for sample in samples}
    members = [key for group in groups for key in group.samples]
    if (
        len(original) != len(samples)
        or len(members) != len(set(members))
        or set(members) != set(original)
    ):
        message = 'Forecast resampling groups must cover the unique sample roster exactly once.'
        raise EvaluationDocumentError(message)
    for group in groups:
        for key in group.samples:
            sample = original[key]
            if (
                domain_group(
                    {'source_id': sample.source_id, 'profile_id': sample.profile_id}, grouping
                )
                != group.group_id
            ):
                message = 'Forecast resampling must preserve original source/profile membership.'
                raise EvaluationDocumentError(message)
    indexes = []
    for candidate in candidates:
        index: dict[SampleKey, list[RetentionComparison]] = defaultdict(list)
        for point in candidate.comparisons:
            key = (point.source_id, point.sample_id)
            if key not in original or point.profile_id != original[key].profile_id:
                message = 'Forecast resampling rows must match the sample/profile roster.'
                raise EvaluationDocumentError(message)
            index[key].append(point)
        indexes.append(index)
    occurrences = _sample_occurrences(groups, multiplicities)
    return GroupedForecastResample(
        tuple(
            replace(original[item.source_id, item.original_sample_id], sample_id=item.sample_id)
            for item in occurrences
        ),
        tuple(
            replace(
                candidate,
                comparisons=tuple(
                    replace(point, sample_id=item.sample_id)
                    for item in occurrences
                    for point in index[item.source_id, item.original_sample_id]
                ),
            )
            for candidate, index in zip(candidates, indexes, strict=True)
        ),
        occurrences,
    )


def _sample_occurrences(
    groups: tuple[GroupMembership, ...], multiplicities: tuple[GroupMultiplicity, ...]
) -> tuple[ResampledSample, ...]:
    if (
        len(groups) != len(multiplicities)
        or any(not group.samples for group in groups)
        or len({group.group_id for group in groups}) != len(groups)
        or any(
            group.group_id != count.group_id
            or isinstance(count.count, bool)
            or not isinstance(count.count, int)
            or count.count < 0
            for group, count in zip(groups, multiplicities, strict=True)
        )
    ):
        message = 'Group multiplicities must match each original group with a nonnegative integer.'
        raise EvaluationDocumentError(message)
    occurrences = []
    for group, count in zip(groups, multiplicities, strict=True):
        for occurrence in range(count.count):
            for source, original_id in sorted(group.samples):
                occurrences.append(
                    ResampledSample(
                        group.group_id,
                        source,
                        original_id,
                        f'resample_sample_{len(occurrences)}',
                        occurrence,
                    )
                )
    return tuple(occurrences)


@dataclass(frozen=True)
class ResampledObservation:
    """A repeated observation's link back to the original canonical record."""

    original_observation_id: str
    observation_id: str
    source_id: str
    sample_id: str


@dataclass(frozen=True)
class SelectionResample:
    """One attempted draw and the entire repeated selection/refitting evidence."""

    replicate_id: int
    multiplicities: tuple[GroupMultiplicity, ...]
    unique_group_count: int
    samples: tuple[ResampledSample, ...]
    observations: tuple[ResampledObservation, ...]
    derived_dataset_sha256: str
    selection: FixedNestedSelection | LearnedNestedSelection

    @property
    def status(self) -> str:
        """Failed strategies/folds remain part of the draw law rather than being retried."""
        return (
            'computed'
            if self.selection.protocols
            and all(strategy.status == 'computed' for strategy in self.selection.protocols)
            else 'insufficient_evidence'
        )


@dataclass(frozen=True)
class SelectionResamplingResult:
    """Reproducible retraining sensitivity; not a population confidence interval."""

    plan: SelectionResamplingPlan
    source_dataset_sha256: str
    grouping: Literal['source', 'profile']
    original_groups: tuple[GroupMembership, ...]
    replicates: tuple[SelectionResample, ...]
    reason: str | None
    uncertainty_status: str = 'not_estimated_retraining_sensitivity_only'

    @property
    def status(self) -> str:
        """Completion concerns accounting for all draws, not a coverage guarantee."""
        return 'completed' if self.reason is None else 'insufficient_evidence'

    @property
    def complete_replicate_count(self) -> int:
        """Report evidence failures without silently conditioning them away."""
        return sum(replicate.status == 'computed' for replicate in self.replicates)


def resample_selection_procedure(
    result: RetentionRunResult, *, plan: SelectionResamplingPlan
) -> SelectionResamplingResult:
    """Resample whole original groups and rerun selection and ensemble fitting.

    Group occurrences duplicate samples/points, not source/profile identities.
    Thus every copy stays in the same fold and counts as one independent group
    for evidence gates. Sample occurrence weights preserve unequal group sizes.
    Grouping/fallback is resolved once on the original roster and frozen for
    all draws. Fold assignment is rebuilt using its original registered seed.
    Fixed PTF predictions/eligibility are reused because they contain no learned
    preprocessing; every registered target-dependent choice/ensemble fit reruns.
    """
    baseline = result.selection if plan.protocol == 'fixed' else result.learned_selection
    if baseline is None:
        message = 'Selection resampling references an unexecuted selection protocol.'
        raise EvaluationDocumentError(message)
    splits = baseline.splits
    groups = tuple(sorted(splits.groups, key=lambda group: group.group_id))
    reason = splits.reason or (
        'too_few_original_groups' if len(groups) < plan.minimum_groups else None
    )
    if reason is not None:
        return SelectionResamplingResult(
            plan, result.plan.dataset.sha256, splits.effective_grouping, groups, (), reason
        )
    _validate_groups(result, groups, splits.effective_grouping)
    generator = Random(plan.seed)  # noqa: S311 - Registered statistical resampling.
    replicates = []
    for index in range(plan.n_resamples):
        counts = [0] * len(groups)
        for _ in groups:
            counts[generator.randrange(len(groups))] += 1
        multiplicities = tuple(
            GroupMultiplicity(group.group_id, count)
            for group, count in zip(groups, counts, strict=True)
        )
        derived, samples, observations = _materialize_draw(result, groups, multiplicities, index)
        if isinstance(baseline, FixedNestedSelection):
            policy = baseline.plan
            fixed = replace(
                policy,
                folds=replace(
                    policy.folds, grouping=splits.effective_grouping, missing_profiles='reject'
                ),
            )
            selection = select_fixed_retention_candidates(derived, plan=fixed)
        else:
            policy_learned = baseline.plan
            fixed = policy_learned.fixed
            selection = select_learned_retention_candidates(
                derived,
                plan=replace(
                    policy_learned,
                    fixed=replace(
                        fixed,
                        folds=replace(
                            fixed.folds,
                            grouping=splits.effective_grouping,
                            missing_profiles='reject',
                        ),
                    ),
                ),
            )
        replicates.append(
            SelectionResample(
                index,
                multiplicities,
                sum(count > 0 for count in counts),
                samples,
                observations,
                derived.plan.dataset.sha256,
                selection,
            )
        )
    return SelectionResamplingResult(
        plan, result.plan.dataset.sha256, splits.effective_grouping, groups, tuple(replicates), None
    )


def _validate_groups(
    result: RetentionRunResult, groups: tuple[GroupMembership, ...], grouping: str
) -> None:
    samples = {
        (str(sample['source_id']), str(sample['sample_id'])): sample
        for sample in object_records(result.plan.dataset.document['samples'])
    }
    members = [sample for group in groups for sample in group.samples]
    if (
        len({group.group_id for group in groups}) != len(groups)
        or len(members) != len(set(members))
        or set(members) != set(samples)
    ):
        message = 'Resampling groups must cover every original sample exactly once.'
        raise EvaluationDocumentError(message)
    if any(
        domain_group(samples[key], grouping) != group.group_id
        for group in groups
        for key in group.samples
    ):
        message = 'Resampling group identities must preserve original source/profile membership.'
        raise EvaluationDocumentError(message)


def _materialize_draw(
    result: RetentionRunResult,
    groups: tuple[GroupMembership, ...],
    multiplicities: tuple[GroupMultiplicity, ...],
    replicate_id: int,
) -> tuple[RetentionRunResult, tuple[ResampledSample, ...], tuple[ResampledObservation, ...]]:
    from .runner import RetentionRunResult  # noqa: PLC0415 - Runtime runner integration.

    document = cast('dict[str, object]', plain(result.plan.dataset.document))
    original_samples = {
        (str(sample['source_id']), str(sample['sample_id'])): sample
        for sample in object_records(document['samples'])
    }
    original_observations: dict[SampleKey, list[dict[str, object]]] = defaultdict(list)
    for observation in object_records(document['observations']):
        key = (str(observation['source_id']), str(observation['sample_id']))
        original_observations[key].append(dict(observation))
    original_points: dict[SampleKey, list[RunPointDecision]] = defaultdict(list)
    for point in result.points:
        original_points[point.source_id, point.sample_id].append(point)
    samples: list[dict[str, object]] = []
    observations: list[dict[str, object]] = []
    points: list[RunPointDecision] = []
    sample_map = _sample_occurrences(groups, multiplicities)
    observation_map = []
    for item in sample_map:
        source, original_id, sample_id = item.source_id, item.original_sample_id, item.sample_id
        key = (source, original_id)
        samples.append({**original_samples[key], 'sample_id': sample_id})
        obs_ids = {}
        for observation in sorted(original_observations[key], key=lambda item: str(item['id'])):
            original_obs = str(observation['id'])
            obs_id = f'resample_observation_{len(observations)}'
            obs_ids[original_obs] = obs_id
            observations.append({**observation, 'id': obs_id, 'sample_id': sample_id})
            observation_map.append(ResampledObservation(original_obs, obs_id, source, sample_id))
        points.extend(
            replace(
                point,
                sample_id=sample_id,
                observation_id=obs_ids[point.observation_id],
                comparison=replace(point.comparison, sample_id=sample_id)
                if point.comparison
                else None,
            )
            for point in sorted(
                original_points[key],
                key=lambda item: (item.candidate_id, item.observation_id),
            )
        )
    document.update(
        dataset_id=f'{result.plan.dataset.dataset_id}__resample_{replicate_id}',
        samples=samples,
        observations=observations,
    )
    dataset = load_retention_dataset(document)
    # This internal view is not a standalone run plan; replay starts from the
    # parent snapshots and registered draw law, with original lineage intact.
    derived = RetentionRunResult(replace(result.plan, dataset=dataset), tuple(points), (), ())
    return derived, tuple(sample_map), tuple(observation_map)
