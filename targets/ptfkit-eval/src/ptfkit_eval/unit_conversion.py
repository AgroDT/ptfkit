"""Shared affine conversions for plan resolution and numeric execution."""

from __future__ import annotations

import math
from collections.abc import Mapping
from decimal import Decimal, localcontext


class UnitConversionError(ValueError):
    """Raised when registry definitions cannot establish an affine conversion."""


def convert_with_units(
    value: float, source_unit: str, target_unit: str, units: Mapping[str, object]
) -> float:
    """Preserve decimal registry scales before rounding a converted value to float."""
    numeric = float(value)
    if source_unit == target_unit:
        return numeric
    source = _conversion(units, source_unit)
    target = _conversion(units, target_unit)
    if source[0] != target[0]:
        message = f'Units {source_unit!r} and {target_unit!r} are not convertible.'
        raise UnitConversionError(message)
    with localcontext() as context:
        context.prec = 40
        si_value = Decimal(str(numeric)) * Decimal(str(source[1])) + Decimal(str(source[2]))
        return float((si_value - Decimal(str(target[2]))) / Decimal(str(target[1])))


def _conversion(units: Mapping[str, object], unit: str) -> tuple[str, float, float]:
    definition = units.get(unit)
    conversion = definition.get('conversion') if isinstance(definition, Mapping) else None
    if not isinstance(conversion, Mapping):
        message = f'Unit {unit!r} has no affine conversion.'
        raise UnitConversionError(message)
    dimension, scale, offset = (
        conversion.get('dimension'),
        conversion.get('scale_to_si'),
        conversion.get('offset_to_si'),
    )
    if (
        not isinstance(dimension, str)
        or not isinstance(scale, (int, float))
        or not isinstance(offset, (int, float))
    ):
        message = f'Unit {unit!r} has an invalid affine conversion.'
        raise UnitConversionError(message)
    if scale == 0 or not math.isfinite(scale) or not math.isfinite(offset):
        message = f'Unit {unit!r} has a zero or nonfinite affine conversion.'
        raise UnitConversionError(message)
    return dimension, float(scale), float(offset)
