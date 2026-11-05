"""Canonical water-content contracts; mass ratios are not volume fractions."""

from __future__ import annotations

from types import MappingProxyType


_CONTRACTS = MappingProxyType(
    {
        'volumetric_water_content': ('volume_fraction', 'bulk_volume'),
        'gravimetric_water_content': ('mass_fraction', 'dry_soil_mass'),
    }
)


def canonical_water_contract(quantity: str) -> tuple[str, str]:
    """Return the canonical unit and denominator for an explicitly named quantity."""
    try:
        return _CONTRACTS[quantity]
    except KeyError as error:
        message = f'Unsupported retention water quantity {quantity!r}.'
        raise ValueError(message) from error


def within_water_bounds(value: float, quantity: str) -> bool:
    """Dry-soil mass ratios have no universal upper bound of one."""
    canonical_water_contract(quantity)
    return value >= 0 and (quantity == 'gravimetric_water_content' or value <= 1)
