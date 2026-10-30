"""Versioned, opt-in evidence transformations, independent of strict eligibility.

An evidence tier describes how a value was obtained. It does not, by itself,
prove that a value matches a particular predictor's measurement contract.
"""

# ruff: noqa: PLR2004 - Registered percent scales and USDA triangle boundaries.

from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise
from types import MappingProxyType
from typing import TYPE_CHECKING

from .documents import document_hash, freeze, plain
from .execution import convert_value
from .input_derivations import COSBY_MIDPOINT_METHOD
from .water import within_water_bounds


if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class EvidenceTier(StrEnum):
    """Distinct provenance categories; approximate evidence never enters the main view."""

    STRICT = 'strict'
    CONVERTED = 'converted'
    DERIVED = 'derived'
    RECONSTRUCTED = 'reconstructed'
    APPROXIMATE = 'approximate'
    UNSUPPORTED = 'unsupported'


@dataclass(frozen=True)
class EvidenceValue:
    """One value with an immutable, recursively retained transformation trace."""

    value: float | str | None
    tier: EvidenceTier
    policy: str
    sources: tuple[str, ...]
    details: tuple[tuple[str, object], ...] = ()
    parents: tuple[EvidenceValue, ...] = ()

    def __post_init__(self) -> None:
        """Reject missing provenance and attempts to launder weaker parent evidence."""
        if not isinstance(self.tier, EvidenceTier) or not self.policy or not self.sources:
            message = 'Evidence requires an enum tier, policy and source identifiers.'
            raise ValueError(message)
        if self.tier != EvidenceTier.UNSUPPORTED and (
            self.value is None
            or isinstance(self.value, bool)
            or (isinstance(self.value, (int, float)) and not math.isfinite(self.value))
        ):
            message = 'Supported evidence requires a finite number or category.'
            raise ValueError(message)
        if self.parents and self.tier != combined_tier(self.tier, self.parents):
            message = 'A transformation cannot upgrade its parent evidence tier.'
            raise ValueError(message)
        object.__setattr__(
            self, 'details', tuple((key, freeze(value)) for key, value in self.details)
        )

    def document(self) -> dict:
        """Return a JSON-compatible trace without dropping intermediate evidence."""
        return {
            'value': self.value,
            'tier': self.tier.value,
            'policy': self.policy,
            'sources': list(self.sources),
            'details': plain(dict(self.details)),
            'parents': [parent.document() for parent in self.parents],
        }


POLICIES = MappingProxyType(
    {
        'unit_conversion_v1': 'Registry affine conversion; physical quantity and basis unchanged.',
        'wrc_log10_adjacent_v1': 'Adjacent positive measured pressures; no extrapolation.',
        'oc_om_factor_v1': 'Explicit source-authorized factor; never assume a universal factor.',
        'density_porosity_v1': '1 - bulk / particle density; common material and units.',
        'texture_closure_v1': (
            '100 - first - second; identical dry-mass fine-earth basis and full closure.'
        ),
        'usda_triangle_v1': 'USDA twelve-class triangle on closed 2/50/2000 micrometre fractions.',
        'psd_exact_rebin_v1': 'Differences of observed cumulative values at exact boundaries.',
        'psd_cumulative_log10_v1': 'Log-diameter interpolation; adjacent boundary ratio at most 5.',
        'psd_broad_bin_log10_v1': 'Exploratory log-uniform within a wide bin; excluded from main.',
        COSBY_MIDPOINT_METHOD: (
            'Existing source-reviewed Cosby Table 2 class coordinates; '
            'verified by the strict binder and restricted to the Cosby function.'
        ),
    }
)

_PERCENT = 100
_MAXIMUM_PSD_BOUNDARY_RATIO = 5


def policy_registry() -> dict:
    """Snapshot registrations before inspecting scores."""
    return {'version': 1, 'policies': dict(POLICIES), 'sha256': document_hash(POLICIES)}


def combined_tier(tier: EvidenceTier, values: Sequence[EvidenceValue]) -> EvidenceTier:
    """Propagate evidence conservatively while retaining each parent category in its trace."""
    order = list(EvidenceTier)
    return max((tier, *(value.tier for value in values)), key=order.index)


def benchmark_view(values: Sequence[EvidenceValue], *, strict_eligible: bool = False) -> str:
    """Respect the existing strict decision; evidence cannot grant strict permission."""
    tiers = {value.tier for value in values}
    if not values or EvidenceTier.UNSUPPORTED in tiers:
        return 'unsupported'
    if EvidenceTier.APPROXIMATE in tiers:
        return 'exploratory'
    return 'strict' if strict_eligible else 'harmonized'


def _transform(
    value: float | str,
    tier: EvidenceTier,
    policy: str,
    parents: Sequence[EvidenceValue],
    **details: object,
) -> EvidenceValue:
    if policy not in POLICIES:
        message = f'Unregistered harmonization policy: {policy}'
        raise ValueError(message)
    return EvidenceValue(
        value,
        combined_tier(tier, parents),
        policy,
        tuple(sorted({source for parent in parents for source in parent.sources})),
        tuple(details.items()),
        tuple(parents),
    )


def convert_evidence(
    value: EvidenceValue,
    source_unit: str,
    target_unit: str,
    *,
    manifest: Mapping[str, object] | None = None,
) -> EvidenceValue:
    """Convert units without mutating or relabelling the original evidence."""
    if source_unit == target_unit:
        return value
    return _transform(
        convert_value(_number(value), source_unit, target_unit, manifest=manifest),
        EvidenceTier.CONVERTED,
        'unit_conversion_v1',
        [value],
        source_unit=source_unit,
        target_unit=target_unit,
    )


def reconstruct_water(
    points: Sequence[tuple[float, EvidenceValue]],
    requested_kpa: float,
    *,
    fitted_alternative: float | None = None,
    water_quantity: str = 'volumetric_water_content',
) -> EvidenceValue | None:
    """Return an exact observation or adjacent log-pressure interpolation, never a fit target.

    Duplicate pressures are ambiguous even if the values agree. Zero pressure
    can be an exact observation but never an endpoint of log interpolation.
    """
    if not math.isfinite(requested_kpa) or requested_kpa < 0:
        message = 'Requested pressure must be finite and nonnegative.'
        raise ValueError(message)
    ordered = sorted(points, key=lambda point: point[0])
    pressures = [pressure for pressure, _ in ordered]
    if any(not math.isfinite(p) or p < 0 for p in pressures) or len(set(pressures)) != len(
        pressures
    ):
        message = 'Measured pressures must be finite, nonnegative and unique.'
        raise ValueError(message)
    if any(point.tier not in (EvidenceTier.STRICT, EvidenceTier.CONVERTED) for _, point in ordered):
        message = 'WRC reconstruction requires supported experimental observations.'
        raise ValueError(message)
    for _, point in ordered:
        if not within_water_bounds(_number(point), water_quantity):
            message = 'Water observations must satisfy the canonical water-fraction bounds.'
            raise ValueError(message)
    index = bisect_left(pressures, requested_kpa)
    if index < len(ordered) and pressures[index] == requested_kpa:
        return ordered[index][1]
    if index == 0 or index == len(ordered) or pressures[index - 1] <= 0:
        return None
    (lower, left), (upper, right) = ordered[index - 1 : index + 1]
    fraction = math.log10(requested_kpa / lower) / math.log10(upper / lower)
    value = _number(left) + fraction * (_number(right) - _number(left))
    if fitted_alternative is not None and not math.isfinite(fitted_alternative):
        message = 'A fitted diagnostic must be finite.'
        raise ValueError(message)
    return _transform(
        value,
        EvidenceTier.RECONSTRUCTED,
        'wrc_log10_adjacent_v1',
        [left, right],
        requested_pressure_kpa=requested_kpa,
        neighboring_pressures_kpa=(lower, upper),
        interpolation_method='linear_in_log10_pressure',
        interpolation_span_kpa=upper - lower,
        interpolation_span_log10=math.log10(upper / lower),
        exact_observation_existed=False,
        fitted_family_alternative=fitted_alternative,
    )


def carbon_conversion(
    value: EvidenceValue, *, factor: float, direction: str, authorization: str
) -> EvidenceValue:
    """Apply an explicitly authorized OC/OM relation and retain its coefficient."""
    if (
        not authorization
        or not math.isfinite(factor)
        or factor <= 0
        or direction not in ('oc_to_om', 'om_to_oc')
    ):
        message = (
            'Carbon derivation requires a positive factor, direction and source authorization.'
        )
        raise ValueError(message)
    numeric = _number(value)
    if not 0 <= numeric <= _PERCENT:
        message = 'Carbon and organic matter must be mass percentages.'
        raise ValueError(message)
    result = numeric * factor if direction == 'oc_to_om' else numeric / factor
    if result > _PERCENT:
        message = 'Derived organic component exceeds total dry mass.'
        raise ValueError(message)
    return _transform(
        result,
        EvidenceTier.DERIVED,
        'oc_om_factor_v1',
        [value],
        factor=factor,
        direction=direction,
        authorization=authorization,
        formula='OM = factor * OC' if direction == 'oc_to_om' else 'OC = OM / factor',
    )


def derive_porosity(
    bulk: EvidenceValue, particle: EvidenceValue, *, basis: str, unit: str
) -> EvidenceValue:
    """Derive porosity only after the caller establishes a common density contract."""
    if not basis or basis == 'unspecified' or not unit or not 0 < _number(bulk) < _number(particle):
        message = (
            'Porosity requires compatible positive densities and an explicit common basis/unit.'
        )
        raise ValueError(message)
    return _transform(
        1 - _number(bulk) / _number(particle),
        EvidenceTier.DERIVED,
        'density_porosity_v1',
        [bulk, particle],
        basis=basis,
        unit=unit,
        formula='porosity = 1 - dry_bulk_density / particle_density',
    )


def complementary_texture(
    first: EvidenceValue, second: EvidenceValue, *, basis: str, closed: bool
) -> EvidenceValue:
    """Derive the missing percentage only for a declared closed fine-earth partition."""
    if basis != 'dry_mass_fine_earth' or not closed or min(_number(first), _number(second)) < 0:
        message = 'Texture closure requires a common closed dry-mass fine-earth partition.'
        raise ValueError(message)
    remaining = 100 - _number(first) - _number(second)
    if remaining < 0:
        message = 'Texture fractions exceed 100 percent.'
        raise ValueError(message)
    return _transform(
        remaining,
        EvidenceTier.DERIVED,
        'texture_closure_v1',
        [first, second],
        basis=basis,
        formula='missing_percent = 100 - first_percent - second_percent',
    )


def usda_texture(
    sand: EvidenceValue,
    silt: EvidenceValue,
    clay: EvidenceValue,
    *,
    basis: str,
    boundaries_um: tuple[float, float, float],
) -> EvidenceValue:
    """Classify already harmonized USDA mass percentages using the texture triangle."""
    if basis != 'dry_mass_fine_earth' or boundaries_um != (2, 50, 2000):
        message = (
            'USDA classification requires the closed 2/50/2000 micrometre fine-earth partition.'
        )
        raise ValueError(message)
    a, b, c = _number(sand), _number(silt), _number(clay)
    if min(a, b, c) < 0 or not math.isclose(a + b + c, 100, abs_tol=1e-8, rel_tol=0):
        message = 'USDA fractions must be nonnegative and close to exactly 100 percent.'
        raise ValueError(message)
    texture = _usda_class(a, b, c)
    return _transform(
        texture,
        EvidenceTier.DERIVED,
        'usda_triangle_v1',
        [sand, silt, clay],
        boundaries_um=(2, 50, 2000),
        basis=basis,
        formula='USDA texture triangle',
    )


def _usda_class(sand: float, silt: float, clay: float) -> str:  # noqa: C901, PLR0911 - USDA triangle regions.
    if silt + 1.5 * clay < 15:
        return 'sand'
    if silt + 2 * clay < 30:
        return 'loamy sand'
    if (clay < 20 and sand > 52 and silt + 2 * clay >= 30) or (clay < 7 and silt < 50):
        return 'sandy loam'
    if 7 <= clay < 27 and 28 <= silt < 50 and sand <= 52:
        return 'loam'
    if silt >= 80 and clay < 12:
        return 'silt'
    if silt >= 50 and clay < 27:
        return 'silt loam'
    if 20 <= clay < 35 and silt < 28 and sand > 45:
        return 'sandy clay loam'
    if 27 <= clay < 40 and 20 < sand <= 45:
        return 'clay loam'
    if 27 <= clay < 40 and sand <= 20:
        return 'silty clay loam'
    if clay >= 35 and sand > 45:
        return 'sandy clay'
    if clay >= 40 and silt >= 40:
        return 'silty clay'
    return 'clay'


def psd_fraction(
    cumulative: Sequence[tuple[float, EvidenceValue]],
    lower_um: float,
    upper_um: float,
    *,
    basis: str,
    allow_approximate: bool = False,
) -> EvidenceValue | None:
    """Rebin a measured cumulative PSD or interpolate sufficiently resolved boundaries.

    Cumulative percentages must refer to the same dry-mass fine-earth basis.
    A missing endpoint is never invented from closure or an assumed upper sieve.
    """
    if (
        basis != 'dry_mass_fine_earth'
        or not 0 <= lower_um < upper_um
        or not math.isfinite(upper_um)
    ):
        message = 'PSD requires ordered finite boundaries and a known common fine-earth basis.'
        raise ValueError(message)
    points = sorted(cumulative, key=lambda point: point[0])
    diameters = [p[0] for p in points]
    values = [_number(p[1]) for p in points]
    if (
        len(set(diameters)) != len(points)
        or any(not math.isfinite(d) or d < 0 for d in diameters)
        or any(not 0 <= v <= _PERCENT for v in values)
        or any(a > b for a, b in pairwise(values))
    ):
        message = 'Cumulative PSD requires unique diameters and monotone mass percentages.'
        raise ValueError(message)

    def boundary(diameter: float) -> EvidenceValue | None:
        index = bisect_left(diameters, diameter)
        if index < len(points) and diameters[index] == diameter:
            return points[index][1]
        if index == 0 or index == len(points) or diameters[index - 1] == 0:
            return None
        (lo, left), (hi, right) = points[index - 1 : index + 1]
        broad = hi / lo > _MAXIMUM_PSD_BOUNDARY_RATIO
        if broad and not allow_approximate:
            return None
        fraction = math.log(diameter / lo) / math.log(hi / lo)
        return _transform(
            _number(left) + fraction * (_number(right) - _number(left)),
            EvidenceTier.APPROXIMATE if broad else EvidenceTier.RECONSTRUCTED,
            'psd_broad_bin_log10_v1' if broad else 'psd_cumulative_log10_v1',
            [left, right],
            requested_diameter_um=diameter,
            neighboring_diameters_um=(lo, hi),
            maximum_main_boundary_ratio=5,
        )

    left, right = boundary(lower_um), boundary(upper_um)
    if left is None or right is None:
        return None
    return _transform(
        _number(right) - _number(left),
        EvidenceTier.DERIVED,
        'psd_exact_rebin_v1',
        [left, right],
        lower_um=lower_um,
        upper_um=upper_um,
        basis=basis,
        formula='CDF(upper) - CDF(lower)',
    )


def _number(value: EvidenceValue) -> float:
    if isinstance(value.value, bool) or not isinstance(value.value, (int, float)):
        message = 'A finite numeric evidence value is required.'
        raise TypeError(message)
    return float(value.value)
