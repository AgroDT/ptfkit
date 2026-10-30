"""Shared scalar arithmetic for validated positive hydraulic-model inputs."""

import math
from sys import float_info


_NEAR_UNITY_LOWER = 0.5
_NEAR_UNITY_UPPER = 2.0


def log_positive_product(one: float, two: float) -> float:
    """Log a positive finite product without premature range loss or cancellation.

    Callers validate positivity and finiteness. Near unity, an exact integer
    product residual protects exponents that magnify errors in log(a)+log(b).
    Subnormal/overflowing products instead use the well-separated operand logs.
    """
    product = one * two
    if product < float_info.min or not math.isfinite(product):
        return math.log(one) + math.log(two)
    if _NEAR_UNITY_LOWER <= product <= _NEAR_UNITY_UPPER:
        a, b = one.as_integer_ratio()
        c, d = two.as_integer_ratio()
        denominator = b * d
        residual = (a * c - denominator) / denominator
        return math.log1p(residual)
    return math.log(product)
