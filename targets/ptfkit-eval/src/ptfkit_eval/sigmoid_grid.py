"""Finite-grid nonlinear pressure gates with training-only identification."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from .documents import EvaluationDocumentError


if TYPE_CHECKING:
    from .folds import GroupKey, SampleKey


MINIMUM_CHOICES = 2
PARAMETER_COUNT = 2
DISTINCT_IDENTITIES = 3


@dataclass(frozen=True, kw_only=True)
class SigmoidGridPlan:
    """A positive log-pressure sigmoid with registered (center kPa, steepness) pairs.

    The left member has weight sigmoid(-s * log10(pressure / center)). Both
    members remain required on the complete common domain, including numerical
    saturation. This is a pressure-only gate, with no learned soil covariates.
    """

    id: str
    left_candidate_id: str
    right_candidate_id: str
    parameter_grid: tuple[tuple[float, float], ...]
    minimum_training_groups: int
    minimum_loss_gap: float
    method: Literal['training_grid_log_pressure_sigmoid_v1'] = (
        'training_grid_log_pressure_sigmoid_v1'
    )

    def __post_init__(self) -> None:
        """Freeze finite positive choices and explicit identification gates."""
        if (
            any(
                not value.strip()
                for value in (self.id, self.left_candidate_id, self.right_candidate_id)
            )
            or len({self.id, self.left_candidate_id, self.right_candidate_id})
            != DISTINCT_IDENTITIES
            or isinstance(self.minimum_training_groups, bool)
            or not isinstance(self.minimum_training_groups, int)
            or self.minimum_training_groups < 1
            or isinstance(self.minimum_loss_gap, bool)
            or not math.isfinite(self.minimum_loss_gap)
            or self.minimum_loss_gap <= 0
            or self.method != 'training_grid_log_pressure_sigmoid_v1'
        ):
            message = 'Sigmoid training requires distinct identities and explicit positive gates.'
            raise EvaluationDocumentError(message)
        if len(self.parameter_grid) < MINIMUM_CHOICES or any(
            len(pair) != PARAMETER_COUNT
            or any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
                or v <= 0
                for v in pair
            )
            for pair in self.parameter_grid
        ):
            message = (
                'Sigmoid training requires at least two finite positive center/steepness pairs.'
            )
            raise EvaluationDocumentError(message)
        choices = tuple(sorted(tuple(pair) for pair in self.parameter_grid))
        if len(set(choices)) != len(choices):
            message = 'Sigmoid training cannot repeat a center/steepness pair.'
            raise EvaluationDocumentError(message)
        object.__setattr__(self, 'parameter_grid', choices)


@dataclass(frozen=True)
class SigmoidParameterScore:
    """One registered nonlinear gate objective on the same training samples."""

    parameters: tuple[float, float]
    mean_training_loss: float


@dataclass(frozen=True)
class SigmoidGridFit:
    """Full grid evidence; a tied or unsupported gate never receives default parameters."""

    plan: SigmoidGridPlan
    training_groups: tuple[GroupKey, ...]
    training_sample_count: int
    usable_samples: tuple[SampleKey, ...]
    usable_group_count: int
    coverage: float
    scores: tuple[SigmoidParameterScore, ...]
    loss_gap: float | None
    parameters: tuple[float, float] | None
    training_loss: float | None
    reason: str | None

    @property
    def status(self) -> str:
        """Expose identification separately from best observed objective."""
        return 'fitted' if self.parameters is not None else 'insufficient_evidence'


def sigmoid_left_weight(pressure: float, parameters: tuple[float, float]) -> float:
    """Compute a convex gate without overflow in pressure ratios or exponentials."""
    center, steepness = parameters
    if any(isinstance(v, bool) or not math.isfinite(v) for v in (pressure, center, steepness)) or (
        pressure < 0 or center <= 0 or steepness <= 0
    ):
        message = 'A pressure sigmoid needs finite nonnegative pressure and positive parameters.'
        raise EvaluationDocumentError(message)
    if pressure == 0:
        return 1.0
    offset = (
        math.log1p((pressure - center) / center) / math.log(10)
        if center / 2 <= pressure <= 2 * center
        else math.log10(pressure) - math.log10(center)
    )
    z = steepness * offset
    if z >= 0:
        tail = math.exp(-z)
        return tail / (1 + tail)
    return 1 / (1 + math.exp(z))
