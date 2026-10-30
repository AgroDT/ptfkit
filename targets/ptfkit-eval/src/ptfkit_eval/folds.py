"""Deterministic nested grouped holdouts based solely on declared sample identities."""

from __future__ import annotations

import hashlib
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypeAlias


if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence


GroupKey: TypeAlias = tuple[str, str]
SampleKey: TypeAlias = tuple[str, str]


class GroupValidationError(ValueError):
    """Raised when sample identities or grouped validation policies are ambiguous."""


@dataclass(frozen=True)
class GroupedSample:
    """A source-local sample and optional source-local profile identity."""

    source_id: str
    sample_id: str
    profile_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class NestedGroupPlan:
    """Predeclared split counts, evidence gates, and identity-only seed policy."""

    seed: int
    outer_folds: int
    inner_folds: int
    grouping: Literal['source', 'profile'] = 'source'
    missing_profiles: Literal['reject', 'source'] = 'reject'
    minimum_training_groups: int = 2
    minimum_validation_groups: int = 1

    def __post_init__(self) -> None:
        """Validate split policies before receiving any target values."""
        if isinstance(self.seed, bool) or not isinstance(self.seed, int):
            message = 'A grouped split seed must be an explicit integer.'
            raise GroupValidationError(message)
        for name, minimum in (
            ('outer_folds', 2),
            ('inner_folds', 2),
            ('minimum_training_groups', 1),
            ('minimum_validation_groups', 1),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                message = f'{name} must be an integer of at least {minimum}.'
                raise GroupValidationError(message)
        if self.grouping not in ('source', 'profile') or self.missing_profiles not in (
            'reject',
            'source',
        ):
            message = 'Grouped split policies must declare supported grouping and fallback choices.'
            raise GroupValidationError(message)


@dataclass(frozen=True)
class GroupMembership:
    """All sample identities belonging to one indivisible group."""

    group_id: GroupKey
    samples: tuple[SampleKey, ...]


@dataclass(frozen=True)
class InnerGroupFold:
    """Inner training and validation groups from one outer training partition."""

    fold_id: int
    training_groups: tuple[GroupKey, ...]
    validation_groups: tuple[GroupKey, ...]


@dataclass(frozen=True)
class OuterGroupFold:
    """Untouched outer test groups and complete nested training provenance."""

    fold_id: int
    training_groups: tuple[GroupKey, ...]
    test_groups: tuple[GroupKey, ...]
    inner: tuple[InnerGroupFold, ...]


@dataclass(frozen=True)
class NestedGroupFolds:
    """Identity-only validation assignment or an explicit evidence failure."""

    plan: NestedGroupPlan
    effective_grouping: Literal['source', 'profile']
    groups: tuple[GroupMembership, ...]
    folds: tuple[OuterGroupFold, ...]
    reason: Literal['missing_profile_ids', 'insufficient_groups_for_requested_folds'] | None
    method: Literal[
        'nested_shuffled_group_round_robin_v1', 'explicit_group_holdout_inner_round_robin_v1'
    ] = 'nested_shuffled_group_round_robin_v1'

    @property
    def status(self) -> Literal['computed', 'insufficient_evidence']:
        """Distinguish a validated complete split from an unusable partial split."""
        return 'computed' if self.reason is None else 'insufficient_evidence'


def build_nested_group_folds(
    samples: Iterable[GroupedSample],
    *,
    plan: NestedGroupPlan,
) -> NestedGroupFolds:
    """Shuffle sorted groups, assign round-robin, and nest only inside outer training.

    Folds balance group counts, not sample counts. The function accepts no
    target or prediction values. Group keys are `(source, '')` for sources and
    `(source, profile)` for profiles. If explicitly requested, one missing
    profile regroups the entire roster by source. No partial split is returned
    when any outer or inner fold fails its declared minimum group counts.
    """
    roster = sorted(samples, key=lambda sample: (sample.source_id, sample.sample_id))
    _validate_roster(roster)
    grouping = plan.grouping
    if grouping == 'profile' and any(sample.profile_id is None for sample in roster):
        if plan.missing_profiles == 'reject':
            return NestedGroupFolds(plan, grouping, (), (), 'missing_profile_ids')
        grouping = 'source'
    groups: dict[GroupKey, list[SampleKey]] = defaultdict(list)
    for sample in roster:
        key = (sample.source_id, sample.profile_id if grouping == 'profile' else '')
        if key[1] is None:
            message = 'Profile grouping requires a complete reviewed profile identity.'
            raise GroupValidationError(message)
        groups[(key[0], key[1])].append((sample.source_id, sample.sample_id))
    membership = tuple(GroupMembership(key, tuple(groups[key])) for key in sorted(groups))
    failed = NestedGroupFolds(
        plan, grouping, membership, (), 'insufficient_groups_for_requested_folds'
    )
    if len(groups) < plan.outer_folds:
        return failed
    folds: list[OuterGroupFold] = []
    all_groups = set(groups)
    for index, test in enumerate(_partitions(tuple(sorted(groups)), plan.outer_folds, plan.seed)):
        training = tuple(sorted(all_groups - set(test)))
        if not _valid_counts(training, test, plan) or len(training) < plan.inner_folds:
            return failed
        inner: list[InnerGroupFold] = []
        inner_seed = int.from_bytes(
            hashlib.sha256(f'{plan.seed}:outer:{index}'.encode()).digest()[:16]
        )
        for inner_index, validation in enumerate(
            _partitions(training, plan.inner_folds, inner_seed)
        ):
            inner_training = tuple(sorted(set(training) - set(validation)))
            if not _valid_counts(inner_training, validation, plan):
                return failed
            inner.append(InnerGroupFold(inner_index, inner_training, validation))
        folds.append(OuterGroupFold(index, training, test, tuple(inner)))
    return NestedGroupFolds(plan, grouping, membership, tuple(folds), None)


def _validate_roster(samples: Sequence[GroupedSample]) -> None:
    seen: set[SampleKey] = set()
    for sample in samples:
        if (
            not sample.source_id.strip()
            or not sample.sample_id.strip()
            or (sample.profile_id is not None and not sample.profile_id.strip())
        ):
            message = 'Source, sample, and supplied profile identifiers must be nonempty.'
            raise GroupValidationError(message)
        key = (sample.source_id, sample.sample_id)
        if key in seen:
            message = f'Duplicate grouped sample identity: {key!r}.'
            raise GroupValidationError(message)
        seen.add(key)


def build_group_holdout(
    samples: Iterable[GroupedSample],
    *,
    training_groups: tuple[GroupMembership, ...],
    test_groups: tuple[GroupMembership, ...],
    plan: NestedGroupPlan,
) -> NestedGroupFolds:
    """Nest training-only tuning inside explicit complete original-group roles.

    The caller preallocates the external holdout. Only inner folds are shuffled;
    the plan's outer fold count is not used to reallocate these explicit roles.
    """
    inventory = build_nested_group_folds(samples, plan=plan)
    if inventory.reason == 'missing_profile_ids':
        return NestedGroupFolds(
            plan,
            inventory.effective_grouping,
            (),
            (),
            inventory.reason,
            method='explicit_group_holdout_inner_round_robin_v1',
        )
    roles = (*training_groups, *test_groups)
    if (
        not training_groups
        or not test_groups
        or len({group.group_id for group in roles}) != len(roles)
        or sorted(roles, key=lambda group: group.group_id) != list(inventory.groups)
    ):
        message = 'Explicit holdout roles must partition complete original groups exactly once.'
        raise GroupValidationError(message)
    training = tuple(sorted(group.group_id for group in training_groups))
    test = tuple(sorted(group.group_id for group in test_groups))
    failed = NestedGroupFolds(
        plan,
        inventory.effective_grouping,
        inventory.groups,
        (),
        'insufficient_groups_for_requested_folds',
        method='explicit_group_holdout_inner_round_robin_v1',
    )
    if not _valid_counts(training, test, plan) or len(training) < plan.inner_folds:
        return failed
    inner_seed = int.from_bytes(hashlib.sha256(f'{plan.seed}:outer:0'.encode()).digest()[:16])
    inner = []
    for index, validation in enumerate(_partitions(training, plan.inner_folds, inner_seed)):
        inner_training = tuple(sorted(set(training) - set(validation)))
        if not _valid_counts(inner_training, validation, plan):
            return failed
        inner.append(InnerGroupFold(index, inner_training, validation))
    return NestedGroupFolds(
        plan,
        inventory.effective_grouping,
        inventory.groups,
        (OuterGroupFold(0, training, test, tuple(inner)),),
        None,
        method='explicit_group_holdout_inner_round_robin_v1',
    )


def _partitions(
    groups: Sequence[GroupKey], count: int, seed: int
) -> tuple[tuple[GroupKey, ...], ...]:
    shuffled = list(groups)
    random.Random(seed).shuffle(shuffled)  # noqa: S311 - Registered deterministic statistical splitting.
    return tuple(tuple(sorted(shuffled[index::count])) for index in range(count))


def _valid_counts(
    training: Sequence[GroupKey], validation: Sequence[GroupKey], plan: NestedGroupPlan
) -> bool:
    return (
        len(training) >= plan.minimum_training_groups
        and len(validation) >= plan.minimum_validation_groups
    )
