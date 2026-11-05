"""Noncorrecting support diagnostics for local retention fit intervals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal


if TYPE_CHECKING:
    from .fitting import RetentionFitResult


@dataclass(frozen=True)
class FitUncertaintySupport:
    """Support checks do not qualify local linearity or residual assumptions."""

    status: Literal['diagnosed', 'fit_failed']
    parameter_intervals_outside_bounds: tuple[str, ...]
    unavailable_parameter_intervals: tuple[str, ...]
    mean_intervals_outside_physical_bounds: tuple[str, ...]
    prediction_intervals_outside_physical_bounds: tuple[str, ...]


def diagnose_fit_uncertainty_support(result: RetentionFitResult) -> FitUncertaintySupport:
    """Retain identifiers of intervals exceeding declared support, without clipping.

    Exact endpoint contact is allowed. Parameter support is the declared fit box;
    volumetric water-content support is [0, 1]. A clear result only establishes
    interval containment, not statistical coverage or scientific validity.
    """
    if result.status != 'fitted':
        return FitUncertaintySupport('fit_failed', (), (), (), ())
    parameters = {parameter.name: parameter for parameter in result.parameters}
    outside = []
    unavailable = []
    for bounds in result.plan.parameters:
        parameter = parameters.get(bounds.name)
        interval = None if parameter is None else parameter.parameter_interval
        if interval is None:
            unavailable.append(bounds.name)
        elif interval.lower < bounds.lower or interval.upper > bounds.upper:
            outside.append(bounds.name)
    return FitUncertaintySupport(
        'diagnosed',
        tuple(outside),
        tuple(unavailable),
        tuple(
            point.observation.reference
            for point in result.points
            if point.mean_curve_confidence_interval.lower < 0
            or point.mean_curve_confidence_interval.upper > 1
        ),
        tuple(
            point.observation.reference
            for point in result.points
            if point.conditional_prediction_interval.lower < 0
            or point.conditional_prediction_interval.upper > 1
        ),
    )
