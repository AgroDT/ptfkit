"""Bounded optimizer coordinates preserving residual/saturated water ordering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

import numpy as np


if TYPE_CHECKING:
    from numpy.typing import NDArray


# A numerical separation in canonical volume fraction, not an empirical soil bound.
WATER_SEPARATION = 1e-10


@dataclass(frozen=True)
class OrderedWaterCoordinates:
    """Use a conditional residual-water fraction when both water parameters vary.

    Physical boxes stay explicit. The residual coordinate covers [0, 1] and
    maps onto [r_lower, min(r_upper, saturation - separation)]. When one water
    parameter is fixed, only the other parameter's feasible box is restricted.
    All reported values and Jacobians remain in physical parameter units.
    """

    names: tuple[str, ...]
    lower: NDArray[np.float64]
    upper: NDArray[np.float64]
    residual_index: int | None
    saturation_index: int | None

    @classmethod
    def create(
        cls,
        names: tuple[str, ...],
        lower: NDArray[np.float64],
        upper: NDArray[np.float64],
        *,
        fixed: dict[str, float] | None = None,
    ) -> OrderedWaterCoordinates:
        """Reject a fixed profile value if it leaves no physically ordered box."""
        fixed = {} if fixed is None else fixed
        lo, hi = lower.copy(), upper.copy()
        r = names.index('theta_r') if 'theta_r' in names else None
        s = names.index('theta_s') if 'theta_s' in names else None
        if r is not None and 'theta_s' in fixed:
            hi[r] = min(hi[r], fixed['theta_s'] - WATER_SEPARATION)
        if s is not None and 'theta_r' in fixed:
            lo[s] = max(lo[s], fixed['theta_r'] + WATER_SEPARATION)
        if np.any(lo >= hi) or (
            r is not None and s is not None and lo[s] <= lo[r] + WATER_SEPARATION
        ):
            message = 'No supported physically ordered water parameter region.'
            raise ValueError(message)
        return cls(names, lo, hi, r, s)

    def _cap(self, saturation: float) -> float:
        return min(
            float(self.upper[cast('int', self.residual_index)]), saturation - WATER_SEPARATION
        )

    def optimizer_bounds(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Return bounds in optimizer coordinates, leaving physical bounds intact."""
        lower, upper = self.lower.copy(), self.upper.copy()
        if self.residual_index is not None and self.saturation_index is not None:
            lower[self.residual_index], upper[self.residual_index] = 0, 1
        return lower, upper

    def feasible(self, values: NDArray[np.float64]) -> NDArray[np.float64]:
        """Project a profile baseline into its new feasible nuisance region."""
        result = np.clip(values, self.lower, self.upper)
        if self.residual_index is not None and self.saturation_index is not None:
            r, s = self.residual_index, self.saturation_index
            result[r] = min(result[r], self._cap(result[s]))
        return result

    def map_box_draw(
        self,
        values: NDArray[np.float64],
        original_lower: NDArray[np.float64],
        original_upper: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Map original uniform draws to conditional feasible ranges, without clipping."""
        fractions = (values - original_lower) / (original_upper - original_lower)
        result = self.lower + fractions * (self.upper - self.lower)
        if self.residual_index is not None and self.saturation_index is not None:
            r, s = self.residual_index, self.saturation_index
            result[r] = self.lower[r] + fractions[r] * (self._cap(result[s]) - self.lower[r])
        return result

    def encode(self, physical: NDArray[np.float64]) -> NDArray[np.float64]:
        """Convert a feasible physical parameter vector into optimizer coordinates."""
        result = physical.copy()
        if self.residual_index is not None and self.saturation_index is not None:
            r, s = self.residual_index, self.saturation_index
            result[r] = (physical[r] - self.lower[r]) / (self._cap(physical[s]) - self.lower[r])
        return result

    def decode(self, coordinates: NDArray[np.float64]) -> NDArray[np.float64]:
        """Convert optimizer coordinates into physically ordered parameters."""
        result = coordinates.copy()
        if self.residual_index is not None and self.saturation_index is not None:
            r, s = self.residual_index, self.saturation_index
            result[r] = self.lower[r] + coordinates[r] * (self._cap(coordinates[s]) - self.lower[r])
        return result

    def physical_jacobian(
        self,
        coordinates: NDArray[np.float64],
        optimizer_jacobian: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Apply the inverse chain rule before rank/covariance calculations."""
        transform = np.eye(len(coordinates))
        if self.residual_index is not None and self.saturation_index is not None:
            r, s = self.residual_index, self.saturation_index
            transform[r, r] = self._cap(coordinates[s]) - self.lower[r]
            transform[r, s] = (
                coordinates[r] if coordinates[s] - WATER_SEPARATION < self.upper[r] else 0
            )
        return np.linalg.solve(transform.T, optimizer_jacobian.T).T
