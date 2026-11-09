"""Average training-law risk and failure bounds from independent train/test blocks."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .documents import EvaluationDocumentError
from .risk_bounds import BoundedRiskInterval


if TYPE_CHECKING:
    from .folds import GroupMembership
    from .losses import SelectionLossPlan
    from .point_losses import PointErrorLossPlan


_MINIMUM_BLOCKS = 2
_MAXIMUM_EXACT_INTEGER = 2**53


@dataclass(frozen=True, kw_only=True)
class IndependentTrainingRiskPlan:
    """Predeclared independent block law, population bounds and learner totality.

    All original groups are IID from the named population. Allocation into
    equal-size training/test group roles must be independent
    of group contents. Every block repeats the entire training-only learner.
    A training failure is determined without inspecting that block's test data.
    Totality is a population assertion, not inferred from observed successes.
    """

    population_id: str
    learner_id: str
    grouping: Literal['source', 'profile']
    loss: SelectionLossPlan | PointErrorLossPlan
    maximum_sample_loss: float
    minimum_group_size: int
    maximum_group_size: int
    training_groups_per_block: int
    test_groups_per_block: int
    n_blocks: int
    total_learner: bool = False
    confidence_level: float = 0.95
    simultaneous_policy_count: int = 1
    assumptions: Literal['iid_groups_disjoint_blocks_training_only_failure_population_bounds'] = (
        'iid_groups_disjoint_blocks_training_only_failure_population_bounds'
    )
    method: Literal['independent_blocks_group_hoeffding_training_law_v1'] = (
        'independent_blocks_group_hoeffding_training_law_v1'
    )

    def __post_init__(self) -> None:
        """Reject unsupported sampling laws, bounds and inferred learner totality."""
        integers = (
            self.minimum_group_size,
            self.maximum_group_size,
            self.training_groups_per_block,
            self.test_groups_per_block,
            self.n_blocks,
            self.simultaneous_policy_count,
        )
        if (
            not self.population_id.strip()
            or not self.learner_id.strip()
            or self.grouping not in ('source', 'profile')
            or self.assumptions
            != 'iid_groups_disjoint_blocks_training_only_failure_population_bounds'
            or self.method != 'independent_blocks_group_hoeffding_training_law_v1'
            or not isinstance(self.total_learner, bool)
            or isinstance(self.maximum_sample_loss, bool)
            or not math.isfinite(self.maximum_sample_loss)
            or self.maximum_sample_loss <= 0
            or isinstance(self.confidence_level, bool)
            or not math.isfinite(self.confidence_level)
            or not 0 < self.confidence_level < 1
            or any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 1 <= value <= _MAXIMUM_EXACT_INTEGER
                for value in integers
            )
            or self.minimum_group_size > self.maximum_group_size
            or self.n_blocks < _MINIMUM_BLOCKS
        ):
            message = (
                'Training-law risk requires explicit independent blocks '
                'and valid population assertions.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class TrainingRiskTestGroup:
    """A complete test-group roster; losses are unavailable for a failed learner."""

    group: GroupMembership
    sample_losses: tuple[float, ...] | None


@dataclass(frozen=True)
class IndependentTrainingBlock:
    """Disjoint training/test roles with an explicit training-only failure flag."""

    block_id: str
    training_groups: tuple[GroupMembership, ...]
    test_groups: tuple[TrainingRiskTestGroup, ...]
    training_failure_reason: str | None = None


@dataclass(frozen=True)
class TrainingLawMoments:
    """Normalized independent-block means and their concentration radii."""

    normalized_mean_successful_loss_sum: float
    normalized_mean_test_group_size: float
    mean_training_success: float
    normalized_successful_loss_radius: float
    normalized_group_size_radius: float
    training_success_radius: float


@dataclass(frozen=True)
class IndependentTrainingRiskBound:
    """Joint failure/mass bounds, with total and successful-training risks separate."""

    plan: IndependentTrainingRiskPlan
    training_failure_count: int
    test_sample_count: int
    moments: TrainingLawMoments | None
    training_success_probability_interval: BoundedRiskInterval | None
    training_failure_probability_interval: BoundedRiskInterval | None
    risk_mass_on_success_interval: BoundedRiskInterval | None
    successful_training_mean_risk_interval: BoundedRiskInterval | None
    unconditional_model_risk_interval: BoundedRiskInterval | None
    successful_training_risk_reason: str | None
    reason: str | None
    target: str = 'independent_training_law_failure_and_sample_risk_mass'

    @property
    def status(self) -> str:
        """A successful-training interval may be unavailable while mass/failure compute."""
        return 'computed' if self.reason is None else 'insufficient_evidence'


def bound_independent_training_risk(
    blocks: tuple[IndependentTrainingBlock, ...],
    *,
    plan: IndependentTrainingRiskPlan,
) -> IndependentTrainingRiskBound:
    """Infer over new training datasets without treating cross-fit rows as IID.

    All original groups are disjoint across every block and role. The entire
    learner, including candidate selection/tuning, is repeated per training
    block. Three concentration events bound normalized successful loss sums,
    test-group size and training success. Failed training contributes zero to
    the explicitly defined risk mass, never a zero model error or a dropped draw.
    An unconditional model-risk interval requires a prior total-learner assertion.
    """
    _validate_roles(blocks, plan)
    failed = sum(block.training_failure_reason is not None for block in blocks)
    samples = sum(len(item.group.samples) for block in blocks for item in block.test_groups)
    reason = _evidence_reason(blocks, plan)
    if reason is not None:
        return IndependentTrainingRiskBound(
            plan, failed, samples, None, None, None, None, None, None, None, reason
        )
    scale = plan.maximum_group_size * plan.test_groups_per_block
    mean_size = math.fsum(
        len(item.group.samples) / scale / plan.n_blocks
        for block in blocks
        for item in block.test_groups
    )
    mean_mass = math.fsum(
        loss / plan.maximum_sample_loss / scale / plan.n_blocks
        for block in blocks
        for item in block.test_groups
        for loss in (item.sample_losses or ())
    )
    mean_success = (plan.n_blocks - failed) / plan.n_blocks
    log_budget = math.log(6 * plan.simultaneous_policy_count) - math.log1p(-plan.confidence_level)
    radius = math.sqrt(log_budget / (2 * plan.n_blocks))
    size_floor = plan.minimum_group_size / plan.maximum_group_size
    size_radius = (1 - size_floor) * math.sqrt(
        log_budget / (2 * plan.n_blocks * plan.test_groups_per_block)
    )
    success = BoundedRiskInterval(max(0, mean_success - radius), min(1, mean_success + radius))
    if plan.total_learner:
        success = BoundedRiskInterval(1, 1)
    failure = BoundedRiskInterval(1 - success.upper, 1 - success.lower)
    mass_upper = plan.maximum_sample_loss * min(
        success.upper, (mean_mass + radius) / max(size_floor, mean_size - size_radius)
    )
    mass_lower = min(
        mass_upper,
        plan.maximum_sample_loss
        * min(1, max(0, mean_mass - radius) / min(1, mean_size + size_radius)),
    )
    mass = BoundedRiskInterval(mass_lower, mass_upper)
    conditional = (
        BoundedRiskInterval(
            min(plan.maximum_sample_loss, mass.lower / success.upper),
            min(plan.maximum_sample_loss, mass.upper / success.lower),
        )
        if success.lower > 0
        else None
    )
    moments = TrainingLawMoments(mean_mass, mean_size, mean_success, radius, size_radius, radius)
    return IndependentTrainingRiskBound(
        plan,
        failed,
        samples,
        moments,
        success,
        failure,
        mass,
        conditional,
        mass if plan.total_learner else None,
        None if conditional is not None else 'success_probability_not_separated_from_zero',
        None,
    )


def _validate_roles(
    blocks: tuple[IndependentTrainingBlock, ...], plan: IndependentTrainingRiskPlan
) -> None:
    if (
        len(blocks) != plan.n_blocks
        or len({block.block_id for block in blocks}) != len(blocks)
        or any(not block.block_id.strip() for block in blocks)
    ):
        message = 'Training-law risk must retain exactly the preregistered unique blocks.'
        raise EvaluationDocumentError(message)
    groups = tuple(
        group
        for block in blocks
        for group in (*block.training_groups, *(item.group for item in block.test_groups))
    )
    members = [key for group in groups for key in group.samples]
    if (
        len({group.group_id for group in groups}) != len(groups)
        or len(members) != len(set(members))
        or any(
            len(block.training_groups) != plan.training_groups_per_block
            or len(block.test_groups) != plan.test_groups_per_block
            for block in blocks
        )
        or any(
            not group.group_id[0].strip()
            or not group.samples
            or (plan.grouping == 'source' and group.group_id[1] != '')
            or (plan.grouping == 'profile' and not group.group_id[1].strip())
            or any(key[0] != group.group_id[0] for key in group.samples)
            for group in groups
        )
    ):
        message = (
            'Independent training blocks must use disjoint original groups '
            'and complete group roles.'
        )
        raise EvaluationDocumentError(message)
    if any(
        block.training_failure_reason is not None
        and (
            not block.training_failure_reason.strip()
            or any(item.sample_losses is not None for item in block.test_groups)
        )
        for block in blocks
    ):
        message = (
            'Failed training must retain a reason and unavailable test losses, not zero errors.'
        )
        raise EvaluationDocumentError(message)


def _evidence_reason(
    blocks: tuple[IndependentTrainingBlock, ...], plan: IndependentTrainingRiskPlan
) -> str | None:
    if plan.total_learner and any(block.training_failure_reason is not None for block in blocks):
        return 'total_learner_assertion_violated'
    for block in blocks:
        groups = (*block.training_groups, *(item.group for item in block.test_groups))
        if any(
            not plan.minimum_group_size <= len(group.samples) <= plan.maximum_group_size
            for group in groups
        ):
            return 'observed_group_size_bound_violation'
        if block.training_failure_reason is not None:
            continue
        for item in block.test_groups:
            if item.sample_losses is None or len(item.sample_losses) != len(item.group.samples):
                return 'incomplete_successful_block_test_losses'
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 <= value <= plan.maximum_sample_loss
                for value in item.sample_losses
            ):
                return 'observed_sample_loss_bound_violation'
    return None
