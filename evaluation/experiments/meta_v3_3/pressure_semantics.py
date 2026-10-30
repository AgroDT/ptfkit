"""Conservative, unit-aware coordinates from registered source descriptions."""

# ruff: noqa: INP001, RUF001 - Scientific source descriptions use Unicode signs.

from __future__ import annotations

import math
import re


NUMBER = r'(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)'
MAX_PF_EXPONENT = 300
COORDINATE = re.compile(
    rf'(?<![\w.])[-−]?({NUMBER})\s*'
    r'(kPa|Pa|bars?|cm\s+(?:(?:water|H2O|of water)(?:\s+head)?|head))\b',
    re.IGNORECASE,
)
PF = re.compile(rf'\bpF\s*([-−]?{NUMBER})\b', re.IGNORECASE)


def coordinates(description: str) -> list[float]:
    """Normalize explicit pressures to positive kPa; pF zero is a 1-cm head."""
    text = description.replace('one-third bar', f'{1 / 3} bar')
    result = []
    for match in COORDINATE.finditer(text):
        value = float(match[1].replace(',', ''))
        unit = match[2].casefold()
        factor = (
            1
            if unit == 'kpa'
            else 0.001
            if unit == 'pa'
            else 100
            if unit.startswith('bar')
            else 0.0980665
        )
        result.append(value * factor)
    for match in PF.finditer(text):
        exponent = float(match[1].replace(',', '').replace('−', '-'))
        result.append(10**exponent * 0.0980665 if exponent < MAX_PF_EXPONENT else math.inf)
    return result


def explicit_pressure(description: str) -> float | None:
    """Accept one coordinate, rejecting lists/ranges and unspecified FC/PWP."""
    if re.search(r'\d\s*(?:[-−–]|,\s+|\s+(?:and|or|to)\s+)[-−]?\d', description):
        return None
    values = coordinates(description)
    if not values or not all(math.isfinite(v) and v >= 0 for v in values):
        return None
    return values[0] if all(math.isclose(v, values[0], rel_tol=1e-10) for v in values) else None
