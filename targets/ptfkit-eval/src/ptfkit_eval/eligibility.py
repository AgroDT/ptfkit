"""Pure eligibility decisions for manifest-declared numeric domains."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real


class ComputationalDomainError(ValueError):
    """Raised when a manifest computational domain is malformed."""


@dataclass(frozen=True)
class DomainBound:
    """One finite boundary of a numeric computational domain."""

    value: float
    inclusive: bool


@dataclass(frozen=True)
class ComputationalDomainDecision:
    """Result of comparing one canonical numeric value with its domain."""

    value: float
    within: bool
    lower: DomainBound | None
    upper: DomainBound | None


def assess_computational_domain(
    value: float,
    measurement: Mapping[str, object],
) -> ComputationalDomainDecision:
    """Assess a finite canonical value against a manifest measurement domain.

    A missing or null ``computational_domain`` is unbounded. Declared domains
    must contain explicit ``lower`` and ``upper`` entries; either boundary may
    be null to represent a one-sided interval.
    """
    numeric_value = _finite_number(value, 'value')
    domain_value = measurement.get('computational_domain')
    if domain_value is None:
        return ComputationalDomainDecision(numeric_value, True, None, None)
    if not isinstance(domain_value, Mapping):
        message = 'A computational domain must be a mapping or null.'
        raise ComputationalDomainError(message)
    if 'lower' not in domain_value or 'upper' not in domain_value:
        message = 'A computational domain must declare lower and upper boundaries.'
        raise ComputationalDomainError(message)

    lower = _parse_bound(domain_value['lower'], 'lower')
    upper = _parse_bound(domain_value['upper'], 'upper')
    _validate_interval(lower, upper)
    within = _above_lower(numeric_value, lower) and _below_upper(numeric_value, upper)
    return ComputationalDomainDecision(numeric_value, within, lower, upper)


def _parse_bound(value: object, name: str) -> DomainBound | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        message = f'The computational-domain {name} boundary must be a mapping or null.'
        raise ComputationalDomainError(message)
    if 'value' not in value or 'inclusive' not in value:
        message = (
            f'The computational-domain {name} boundary must declare value and inclusive.'
        )
        raise ComputationalDomainError(message)
    inclusive = value['inclusive']
    if not isinstance(inclusive, bool):
        message = f'The computational-domain {name} inclusive flag must be boolean.'
        raise ComputationalDomainError(message)
    return DomainBound(_finite_number(value['value'], f'{name} boundary'), inclusive)


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        message = f'The computational-domain {name} must be a finite number.'
        raise ComputationalDomainError(message)
    numeric = float(value)
    if not math.isfinite(numeric):
        message = f'The computational-domain {name} must be a finite number.'
        raise ComputationalDomainError(message)
    return numeric


def _validate_interval(lower: DomainBound | None, upper: DomainBound | None) -> None:
    if lower is None or upper is None:
        return
    if lower.value > upper.value:
        message = 'A computational-domain lower boundary cannot exceed its upper boundary.'
        raise ComputationalDomainError(message)
    if lower.value == upper.value and not (lower.inclusive and upper.inclusive):
        message = 'Equal computational-domain boundaries must both be inclusive.'
        raise ComputationalDomainError(message)


def _above_lower(value: float, lower: DomainBound | None) -> bool:
    if lower is None:
        return True
    return value > lower.value or (lower.inclusive and value == lower.value)


def _below_upper(value: float, upper: DomainBound | None) -> bool:
    if upper is None:
        return True
    return value < upper.value or (upper.inclusive and value == upper.value)
