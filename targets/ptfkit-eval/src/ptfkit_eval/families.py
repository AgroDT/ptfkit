"""Versioned retention approximation families with explicit parameter conventions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

from .adapters import CLAPP1978_MAXIMUM_B, evaluate_clapp1978_h_theta
from .numerics import log_positive_product


if TYPE_CHECKING:
    from collections.abc import Mapping

    from numpy.typing import ArrayLike, NDArray


class RetentionFamilyError(ValueError):
    """Raised when an approximation family or its physical parameters are invalid."""


@dataclass(frozen=True)
class FamilyParameter:
    """One family-specific parameter name, quantity, and canonical unit."""

    name: str
    quantity: str
    unit: str
    logarithmic_restarts: bool = False


@dataclass(frozen=True)
class RetentionFamily:
    """A fixed equation; numerical fitting choices belong to the fit plan."""

    id: str
    equation: str
    parameters: tuple[FamilyParameter, ...]
    reference: str
    axis_quantity: str = 'matric_potential'
    axis_unit: str = 'kilopascal'
    axis_convention: str = 'magnitude'
    target_quantity: str = 'volumetric_water_content'
    target_unit: str = 'volume_fraction'
    denominator_basis: str = 'bulk_volume'
    material_basis_policy: str = 'inherit_reviewed_observation_contract'

    @property
    def minimum_points(self) -> int:
        """Require positive residual degrees of freedom for local uncertainty."""
        return len(self.parameters) + 1


@cache
def retention_families() -> Mapping[str, RetentionFamily]:
    """Return immutable family variants; stored workbook parameters are not inferred."""
    theta = (
        FamilyParameter('theta_r', 'volumetric_water_content', 'volume_fraction'),
        FamilyParameter('theta_s', 'volumetric_water_content', 'volume_fraction'),
    )
    vg = (
        *theta,
        FamilyParameter(
            'alpha', 'van_genuchten_alpha', 'inverse_kilopascal', logarithmic_restarts=True
        ),
        FamilyParameter('n', 'van_genuchten_n', 'dimensionless'),
    )
    families = (
        RetentionFamily(
            'van_genuchten_mualem_v1',
            'theta_r + (theta_s - theta_r) * (1 + (alpha*h)^n)^(-(1 - 1/n)); n > 1',
            vg,
            'https://doi.org/10.2136/sssaj1980.03615995004400050002x',
        ),
        RetentionFamily(
            'van_genuchten_m1_v1',
            'theta_r + (theta_s - theta_r) / (1 + (alpha*h)^n); n > 0',
            vg,
            'Reviewed Vereecken reduced model; m = 1, distinct from the Mualem constraint.',
        ),
        RetentionFamily(
            'brooks_corey_v1',
            (
                'theta_s for h <= air_entry; otherwise '
                'theta_r + (theta_s - theta_r)*(h/air_entry)^(-lambda)'
            ),
            (
                *theta,
                FamilyParameter(
                    'air_entry', 'matric_potential', 'kilopascal', logarithmic_restarts=True
                ),
                FamilyParameter('lambda', 'pore_size_distribution_index', 'dimensionless'),
            ),
            'https://wipp.energy.gov/library/CRA/CRA-2014/References/Others/Brooks_Corey_1964_Hydraulic_Properties_ERMS241117.pdf',
        ),
        RetentionFamily(
            'clapp1978_gradual_air_entry_v1',
            'Reviewed Clapp-Hornberger power curve and gradual-air-entry parabola; theta_r = 0.',
            (
                FamilyParameter('theta_s', 'volumetric_water_content', 'volume_fraction'),
                FamilyParameter(
                    'saturation_suction',
                    'matric_potential',
                    'kilopascal',
                    logarithmic_restarts=True,
                ),
                FamilyParameter('b', 'campbell_b', 'dimensionless'),
            ),
            'specs/functions/clapp1978.yaml and the reviewed clapp1978_h_theta adapter.',
        ),
    )
    return MappingProxyType({family.id: family for family in families})


def evaluate_retention_family(
    family_id: str,
    parameters: Mapping[str, float],
    suction_kpa: ArrayLike,
) -> NDArray[np.float64]:
    """Evaluate one exact registered convention in canonical kPa and volume fractions."""
    family = retention_families().get(family_id)
    if family is None:
        message = f'Unknown retention family: {family_id!r}.'
        raise RetentionFamilyError(message)
    if set(parameters) != {parameter.name for parameter in family.parameters}:
        message = 'Family parameters must match the registered variant exactly.'
        raise RetentionFamilyError(message)
    if any(not math.isfinite(value) or isinstance(value, bool) for value in parameters.values()):
        message = 'Family parameters must be finite numbers.'
        raise RetentionFamilyError(message)
    axis = np.asarray(suction_kpa, dtype=np.float64)
    if axis.ndim != 1 or not np.all(np.isfinite(axis)) or np.any(axis < 0):
        message = 'Family suction must be a one-dimensional finite nonnegative magnitude.'
        raise RetentionFamilyError(message)
    theta_s = parameters['theta_s']
    theta_r = parameters.get('theta_r', 0.0)
    if not 0 <= theta_r < theta_s <= 1:
        message = 'Family water contents must satisfy 0 <= theta_r < theta_s <= 1.'
        raise RetentionFamilyError(message)
    if family_id == 'clapp1978_gradual_air_entry_v1':
        return _evaluate_clapp_family(parameters, axis)
    if family_id == 'brooks_corey_v1':
        air_entry, shape = parameters['air_entry'], parameters['lambda']
        if air_entry <= 0 or shape <= 0:
            message = 'Brooks-Corey requires positive air-entry suction and lambda.'
            raise RetentionFamilyError(message)
        effective = np.ones_like(axis)
        dry = axis > air_entry
        effective[dry] = np.exp(-shape * (np.log(axis[dry]) - math.log(air_entry)))
    else:
        alpha, n = parameters['alpha'], parameters['n']
        if alpha <= 0 or n <= 0 or (family_id == 'van_genuchten_mualem_v1' and n <= 1):
            message = 'van Genuchten parameters violate the registered alpha/n convention.'
            raise RetentionFamilyError(message)
        m = 1 - 1 / n if family_id == 'van_genuchten_mualem_v1' else 1.0
        effective = np.ones_like(axis)
        positive = axis > 0
        with np.errstate(over='ignore', under='ignore'):
            power_log = n * np.fromiter(
                (log_positive_product(alpha, float(head)) for head in axis[positive]),
                dtype=np.float64,
            )
            effective[positive] = np.exp(-m * np.logaddexp(0.0, power_log))
    return np.asarray(theta_r + (theta_s - theta_r) * effective, dtype=np.float64)


def _evaluate_clapp_family(
    parameters: Mapping[str, float], axis: NDArray[np.float64]
) -> NDArray[np.float64]:
    theta_s = parameters['theta_s']
    if (
        not 0 < parameters['b'] < CLAPP1978_MAXIMUM_B
        or theta_s >= 1
        or parameters['saturation_suction'] <= 0
    ):
        message = (
            'Clapp gradual air entry requires 0 < b < 11.5, 0 < theta_s < 1 '
            'and positive saturation suction.'
        )
        raise RetentionFamilyError(message)
    # The curve is homogeneous in pressure: keeping both values in kPa
    # avoids an unnecessary potentially overflowing conversion to cm.
    return np.array(
        [
            evaluate_clapp1978_h_theta(
                {
                    'b': parameters['b'],
                    'saturated_water_content': theta_s,
                    'saturation_suction': parameters['saturation_suction'],
                },
                float(value),
            )
            for value in axis
        ],
        dtype=np.float64,
    )
