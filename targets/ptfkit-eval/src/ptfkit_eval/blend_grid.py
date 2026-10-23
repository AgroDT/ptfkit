"""Finite-grid training contracts using the existing two-curve blend semantics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .composites import BlendTransition, Interval
from .documents import EvaluationDocumentError


if TYPE_CHECKING:
    from .folds import GroupKey, SampleKey


MINIMUM_INTERVALS = 2
INTERVAL_ENDPOINT_COUNT = 2


@dataclass(frozen=True, kw_only=True)
class BlendGridPlan:
    """Fixed members, interval roster, axis and weighting with training-only search."""

    id: str
    left_candidate_id: str
    right_candidate_id: str
    interval_grid_kpa: tuple[tuple[float, float], ...]
    transform: Literal['linear', 'log10']
    weighting: Literal['linear', 'smoothstep']
    minimum_training_groups: int
    minimum_loss_gap: float
    method: Literal['training_grid_blend_interval_v1'] = 'training_grid_blend_interval_v1'

    def __post_init__(self) -> None:
        """Reject ambiguous identities, duplicate intervals and unsupported interpolation."""
        if (
            any(
                not value.strip()
                for value in (self.id, self.left_candidate_id, self.right_candidate_id)
            )
            or self.left_candidate_id == self.right_candidate_id
            or self.id in (self.left_candidate_id, self.right_candidate_id)
            or self.transform not in ('linear', 'log10')
            or self.weighting not in ('linear', 'smoothstep')
            or isinstance(self.minimum_training_groups, bool)
            or not isinstance(self.minimum_training_groups, int)
            or self.minimum_training_groups < 1
            or isinstance(self.minimum_loss_gap, bool)
            or not math.isfinite(self.minimum_loss_gap)
            or self.minimum_loss_gap <= 0
            or self.method != 'training_grid_blend_interval_v1'
        ):
            message = (
                'Blend-grid training requires distinct identities and explicit valid policies.'
            )
            raise EvaluationDocumentError(message)
        if len(self.interval_grid_kpa) < MINIMUM_INTERVALS or any(
            len(bounds) != INTERVAL_ENDPOINT_COUNT
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
                for value in bounds
            )
            or bounds[0] >= bounds[1]
            for bounds in self.interval_grid_kpa
        ):
            message = 'Blend-grid training requires at least two positive finite ordered intervals.'
            raise EvaluationDocumentError(message)
        grid = tuple(sorted(tuple(bounds) for bounds in self.interval_grid_kpa))
        if len(set(grid)) != len(grid):
            message = 'Blend-grid training cannot repeat a transition interval.'
            raise EvaluationDocumentError(message)
        object.__setattr__(self, 'interval_grid_kpa', grid)


@dataclass(frozen=True)
class BlendIntervalScore:
    """One registered transition interval's objective on the common training roster."""

    interval_kpa: tuple[float, float]
    mean_training_loss: float


@dataclass(frozen=True)
class BlendGridFit:
    """Complete training-only interval search with explicit identification failure."""

    plan: BlendGridPlan
    training_groups: tuple[GroupKey, ...]
    training_sample_count: int
    usable_samples: tuple[SampleKey, ...]
    usable_group_count: int
    coverage: float
    scores: tuple[BlendIntervalScore, ...]
    loss_gap: float | None
    interval_kpa: tuple[float, float] | None
    training_loss: float | None
    reason: str | None

    @property
    def status(self) -> str:
        """Never choose an arbitrary interval when training evidence is insufficient."""
        return 'fitted' if self.interval_kpa is not None else 'insufficient_evidence'


def blend_left_weight(pressure: float, bounds: tuple[float, float], plan: BlendGridPlan) -> float:
    """Use the same routing convention as fixed native composite candidates."""
    transition = BlendTransition('left', 'right', Interval(*bounds), weighting=plan.weighting)
    return next(
        (
            item.weight
            for item in transition.route(pressure, plan.transform)
            if item.member_id == 'left'
        ),
        0.0,
    )
