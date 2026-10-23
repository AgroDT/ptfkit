"""Registered finite-grid training contracts for two-curve hard switches."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .documents import EvaluationDocumentError


if TYPE_CHECKING:
    from .folds import GroupKey, SampleKey


_MINIMUM_BOUNDARIES = 2


@dataclass(frozen=True, kw_only=True)
class HardSwitchGridPlan:
    """Fixed members/grid, exact boundary ownership, and training evidence gates."""

    id: str
    left_candidate_id: str
    right_candidate_id: str
    boundary_grid_kpa: tuple[float, ...]
    boundary_member: Literal['left', 'right']
    minimum_training_groups: int
    minimum_loss_gap: float
    method: Literal['training_grid_hard_switch_v1'] = 'training_grid_hard_switch_v1'

    def __post_init__(self) -> None:
        """Reject unsupported choices and require a unique finite positive grid."""
        if (
            any(
                not value.strip()
                for value in (self.id, self.left_candidate_id, self.right_candidate_id)
            )
            or self.left_candidate_id == self.right_candidate_id
            or self.id in (self.left_candidate_id, self.right_candidate_id)
            or self.boundary_member not in ('left', 'right')
            or isinstance(self.minimum_training_groups, bool)
            or not isinstance(self.minimum_training_groups, int)
            or self.minimum_training_groups < 1
            or isinstance(self.minimum_loss_gap, bool)
            or not math.isfinite(self.minimum_loss_gap)
            or self.minimum_loss_gap <= 0
            or self.method != 'training_grid_hard_switch_v1'
        ):
            message = (
                'Hard-switch training requires distinct IDs, boundary ownership and positive gates.'
            )
            raise EvaluationDocumentError(message)
        if (
            len(self.boundary_grid_kpa) < _MINIMUM_BOUNDARIES
            or len(set(self.boundary_grid_kpa)) != len(self.boundary_grid_kpa)
            or any(
                isinstance(value, bool) or not math.isfinite(value) or value <= 0
                for value in self.boundary_grid_kpa
            )
        ):
            message = (
                'Hard-switch training requires at least two distinct finite positive boundaries.'
            )
            raise EvaluationDocumentError(message)
        object.__setattr__(self, 'boundary_grid_kpa', tuple(sorted(self.boundary_grid_kpa)))


@dataclass(frozen=True)
class HardSwitchBoundaryScore:
    """One registered boundary's mean training loss on the identical usable roster."""

    suction_kpa: float
    mean_training_loss: float


@dataclass(frozen=True)
class HardSwitchGridFit:
    """Training-only grid search with all scores and explicit nonidentifiability."""

    plan: HardSwitchGridPlan
    training_groups: tuple[GroupKey, ...]
    training_sample_count: int
    usable_samples: tuple[SampleKey, ...]
    usable_group_count: int
    coverage: float
    scores: tuple[HardSwitchBoundaryScore, ...]
    loss_gap: float | None
    switch_suction_kpa: float | None
    training_loss: float | None
    reason: str | None

    @property
    def status(self) -> str:
        """Never default a boundary when the evidence gate or loss separation fails."""
        return 'fitted' if self.switch_suction_kpa is not None else 'insufficient_evidence'


def hard_switch_uses_left(pressure: float, boundary: float, boundary_member: str) -> bool:
    """Apply the registered exact boundary owner without tolerances or interpolation."""
    return pressure < boundary or (pressure == boundary and boundary_member == 'left')
