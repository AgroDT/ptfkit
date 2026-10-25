"""Simultaneous conditional outer-rule risk bounds under explicit group assumptions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .documents import EvaluationDocumentError
from .losses import SelectionLossPlan, mean_finite_losses


if TYPE_CHECKING:
    from .folds import GroupKey


_MAXIMUM_EXACT_INTEGER = 2**53
_MINIMUM_FOLDS = 2


@dataclass(frozen=True, kw_only=True)
class ConditionalOuterRiskPlan:
    """Population assertions supplied before inspecting held-out losses.

    Groups must be IID from the named nonempty-group population. Fold assignment
    must be independent of group contents. Each rule, including preprocessing,
    selection and tuning, must use only its declared training groups. Population
    sample loss and group-size bounds are assumptions, never sample estimates.
    """

    population_id: str
    grouping: Literal['source', 'profile']
    loss: SelectionLossPlan
    maximum_sample_loss: float
    maximum_group_size: int
    minimum_group_size: int = 1
    confidence_level: float = 0.95
    simultaneous_policy_count: int = 1
    assumptions: Literal['iid_groups_value_independent_partition_population_bounds'] = (
        'iid_groups_value_independent_partition_population_bounds'
    )
    method: Literal['simultaneous_group_hoeffding_conditional_outer_risk_v1'] = (
        'simultaneous_group_hoeffding_conditional_outer_risk_v1'
    )

    def __post_init__(self) -> None:
        """Reject implicit populations, inferred bounds and unsupported policies."""
        if (
            not self.population_id.strip()
            or self.grouping not in ('source', 'profile')
            or self.assumptions != 'iid_groups_value_independent_partition_population_bounds'
            or self.method != 'simultaneous_group_hoeffding_conditional_outer_risk_v1'
            or not isinstance(self.maximum_sample_loss, (int, float))
            or isinstance(self.maximum_sample_loss, bool)
            or not math.isfinite(self.maximum_sample_loss)
            or self.maximum_sample_loss <= 0
            or not isinstance(self.confidence_level, (int, float))
            or isinstance(self.confidence_level, bool)
            or not math.isfinite(self.confidence_level)
            or not 0 < self.confidence_level < 1
            or any(
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 1 <= value <= _MAXIMUM_EXACT_INTEGER
                for value in (
                    self.minimum_group_size,
                    self.maximum_group_size,
                    self.simultaneous_policy_count,
                )
            )
            or self.minimum_group_size > self.maximum_group_size
        ):
            message = (
                'Conditional risk bounds require explicit valid population assumptions and bounds.'
            )
            raise EvaluationDocumentError(message)


@dataclass(frozen=True)
class BoundedGroupLoss:
    """Complete sample losses for one untouched independent test group."""

    group_id: GroupKey
    sample_losses: tuple[float, ...]


@dataclass(frozen=True)
class ConditionalOuterFoldLoss:
    """One fitted rule's complete test losses and disjoint training identity."""

    fold_id: int
    training_groups: tuple[GroupKey, ...]
    test_groups: tuple[BoundedGroupLoss, ...]


@dataclass(frozen=True)
class BoundedRiskInterval:
    """A population-risk or normalization interval, not a prediction interval."""

    lower: float
    upper: float


@dataclass(frozen=True)
class ConditionalOuterFoldBound:
    """Simultaneous conditional sample-risk bound for one trained outer rule."""

    fold_id: int
    training_groups: tuple[GroupKey, ...]
    test_groups: tuple[GroupKey, ...]
    group_count: int
    sample_count: int
    normalized_mean_group_loss_sum: float
    normalized_numerator_radius: float
    risk_interval: BoundedRiskInterval


@dataclass(frozen=True)
class ConditionalOuterRiskBound:
    """Joint bands and an equal-fold mixture; no training-law average-risk CI.

    Coverage is simultaneous over original IID group draws under the declared
    assumptions. It is not conditional on all fits or observations succeeding.
    Data-dependent changes to the target population or method are not covered.
    """

    plan: ConditionalOuterRiskPlan
    group_count: int
    sample_count: int
    normalized_mean_group_size: float
    normalized_denominator_radius: float
    normalized_expected_group_size_interval: BoundedRiskInterval
    folds: tuple[ConditionalOuterFoldBound, ...]
    equal_fold_mean_risk_interval: BoundedRiskInterval
    target: str = 'equal_fold_mean_conditional_sample_risk'
    coverage_scope: str = 'simultaneous_over_original_iid_group_draws'


def bound_conditional_outer_risks(
    folds: tuple[ConditionalOuterFoldLoss, ...],
    *,
    plan: ConditionalOuterRiskPlan,
) -> ConditionalOuterRiskBound:
    """Bound all locked-rule risks jointly, including arbitrary training-only tuning.

    For each rule j the target is E[S_j | training_j] / E[N], with S_j the
    complete fresh-group loss sum and N its population size. Per-fold Hoeffding
    bounds on S_j and one all-group bound on N share alpha/[q(K+1)] failure
    budgets, where q is the preregistered simultaneous_policy_count.
    Their union needs no independence between folds. Equal-fold averaging gives
    an interval for the mean of these conditional risks, not E over new training
    sets, the observed sample-weighted CV statistic, or a final all-data model.

    Callers own fitted-rule provenance, complete outcome observation and IID/
    bounded-population assertions. Incomplete fits or sample losses cannot enter
    this function. Bounds are on the declared loss; values are never clipped.
    """
    groups = _validate_folds(folds, plan)
    group_count = len(groups)
    sample_count = sum(len(group.sample_losses) for group in groups)
    size_floor = plan.minimum_group_size / plan.maximum_group_size
    size_mean = (
        math.fsum(len(group.sample_losses) / plan.maximum_group_size for group in groups)
        / group_count
    )
    log_budget = math.log(2 * (len(folds) + 1) * plan.simultaneous_policy_count) - math.log1p(
        -plan.confidence_level
    )
    size_radius = (1 - size_floor) * math.sqrt(log_budget / (2 * group_count))
    denominator = BoundedRiskInterval(
        max(size_floor, size_mean - size_radius), min(1, size_mean + size_radius)
    )
    bounded_folds = tuple(_bound_fold(fold, plan, log_budget, denominator) for fold in folds)
    mixture = BoundedRiskInterval(
        mean_finite_losses([fold.risk_interval.lower for fold in bounded_folds]),
        mean_finite_losses([fold.risk_interval.upper for fold in bounded_folds]),
    )
    return ConditionalOuterRiskBound(
        plan,
        group_count,
        sample_count,
        size_mean,
        size_radius,
        denominator,
        bounded_folds,
        mixture,
    )


def _validate_folds(
    folds: tuple[ConditionalOuterFoldLoss, ...],
    plan: ConditionalOuterRiskPlan,
) -> tuple[BoundedGroupLoss, ...]:
    groups = tuple(group for fold in folds for group in fold.test_groups)
    identifiers = {group.group_id for group in groups}
    if (
        len(folds) < _MINIMUM_FOLDS
        or len({fold.fold_id for fold in folds}) != len(folds)
        or len(identifiers) != len(groups)
        or any(not fold.test_groups for fold in folds)
        or any(
            not group.group_id[0].strip()
            or (plan.grouping == 'profile' and not group.group_id[1].strip())
            or (plan.grouping == 'source' and group.group_id[1] != '')
            or not plan.minimum_group_size <= len(group.sample_losses) <= plan.maximum_group_size
            for group in groups
        )
    ):
        message = (
            'Conditional risk folds require a complete disjoint nonempty bounded group roster.'
        )
        raise EvaluationDocumentError(message)
    for fold in folds:
        test = {group.group_id for group in fold.test_groups}
        if (
            len(set(fold.training_groups)) != len(fold.training_groups)
            or set(fold.training_groups) != identifiers - test
        ):
            message = 'Each conditional risk rule must train on exactly the other folds groups.'
            raise EvaluationDocumentError(message)
    if any(
        not isinstance(loss, (int, float))
        or isinstance(loss, bool)
        or not math.isfinite(loss)
        or not 0 <= loss <= plan.maximum_sample_loss
        for group in groups
        for loss in group.sample_losses
    ):
        message = 'Observed sample losses violate the declared population loss bound.'
        raise EvaluationDocumentError(message)
    return groups


def _bound_fold(
    fold: ConditionalOuterFoldLoss,
    plan: ConditionalOuterRiskPlan,
    log_budget: float,
    denominator: BoundedRiskInterval,
) -> ConditionalOuterFoldBound:
    count = len(fold.test_groups)
    mean = math.fsum(
        math.fsum(
            loss / plan.maximum_sample_loss / plan.maximum_group_size
            for loss in group.sample_losses
        )
        / count
        for group in fold.test_groups
    )
    radius = math.sqrt(log_budget / (2 * count))
    lower = min(1, max(0, mean - radius) / denominator.upper)
    upper = min(1, (mean + radius) / denominator.lower)
    interval = BoundedRiskInterval(
        plan.maximum_sample_loss * lower, plan.maximum_sample_loss * upper
    )
    return ConditionalOuterFoldBound(
        fold.fold_id,
        fold.training_groups,
        tuple(group.group_id for group in fold.test_groups),
        count,
        sum(len(group.sample_losses) for group in fold.test_groups),
        mean,
        radius,
        interval,
    )
