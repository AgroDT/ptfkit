"""Identity-only allocation of original groups to independent training blocks."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .documents import EvaluationDocumentError
from .folds import GroupMembership


if TYPE_CHECKING:
    from collections.abc import Iterable

    from .folds import GroupedSample
    from .training_risk import IndependentTrainingRiskPlan


@dataclass(frozen=True)
class TrainingBlockRoles:
    """Original memberships for one preallocated learner invocation."""

    block_id: str
    training_groups: tuple[GroupMembership, ...]
    test_groups: tuple[GroupMembership, ...]


@dataclass(frozen=True)
class IndependentTrainingAllocation:
    """Complete allocation; no groups are discarded or copied between roles."""

    plan: IndependentTrainingRiskPlan
    seed: int
    blocks: tuple[TrainingBlockRoles, ...]
    method: Literal['sha256_original_group_disjoint_blocks_v1'] = (
        'sha256_original_group_disjoint_blocks_v1'
    )


def allocate_independent_training_blocks(
    samples: Iterable[GroupedSample],
    *,
    plan: IndependentTrainingRiskPlan,
    seed: int,
) -> IndependentTrainingAllocation:
    """Assign exact original group counts without targets, predictions or retries.

    Grouping must already be resolved for the complete original roster. Missing
    profiles are rejected rather than triggering block-local regrouping. IDs
    must be value-independent administrative labels for the sampling guarantee;
    this allocator cannot verify their scientific origin or IID sampling.
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        message = 'Independent training allocation requires an integer seed.'
        raise EvaluationDocumentError(message)
    groups: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
    seen: set[tuple[str, str]] = set()
    for sample in samples:
        if (
            not sample.source_id.strip()
            or not sample.sample_id.strip()
            or (sample.profile_id is not None and not sample.profile_id.strip())
        ):
            message = 'Training allocation requires nonempty original identities.'
            raise EvaluationDocumentError(message)
        key = (sample.source_id, sample.sample_id)
        if key in seen:
            message = 'Training allocation cannot repeat an original sample.'
            raise EvaluationDocumentError(message)
        seen.add(key)
        profile = ''
        if plan.grouping == 'profile':
            if sample.profile_id is None:
                message = 'Resolve missing profile identities before block allocation.'
                raise EvaluationDocumentError(message)
            profile = sample.profile_id
        groups[(sample.source_id, profile)].append(key)
    width = plan.training_groups_per_block + plan.test_groups_per_block
    if len(groups) != plan.n_blocks * width:
        message = (
            'Independent training allocation requires exactly the registered original group count.'
        )
        raise EvaluationDocumentError(message)

    def rank(group_id: tuple[str, str]) -> tuple[bytes, tuple[str, str]]:
        payload = json.dumps([seed, *group_id], ensure_ascii=True, separators=(',', ':'))
        return hashlib.sha256(payload.encode('ascii')).digest(), group_id

    ordered = tuple(
        GroupMembership(group_id, tuple(sorted(groups[group_id])))
        for group_id in sorted(groups, key=rank)
    )
    blocks = tuple(
        TrainingBlockRoles(
            block_id=f'block_{index}',
            training_groups=ordered[start : start + plan.training_groups_per_block],
            test_groups=ordered[start + plan.training_groups_per_block : start + width],
        )
        for index in range(plan.n_blocks)
        for start in (index * width,)
    )
    return IndependentTrainingAllocation(plan, seed, blocks)
