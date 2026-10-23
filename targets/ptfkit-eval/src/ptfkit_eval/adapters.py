"""Executable hydraulic-model adapters for parameter-producing PTFs."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import TypeAlias

from .contracts import ModelAdapterSpec, default_model_adapter_specs
from .numerics import log_positive_product


ParameterValues: TypeAlias = Mapping[str, float]
AdapterEvaluator: TypeAlias = Callable[[ParameterValues, float], float]


class ModelEvaluationError(ValueError):
    """Raised when model parameters or an axis value are outside the adapter domain."""


@dataclass(frozen=True)
class ModelAdapter:
    """Physical adapter contract paired with its scalar evaluator."""

    spec: ModelAdapterSpec
    evaluate: AdapterEvaluator


_CLAPP1978_INFLECTION_WETNESS = 0.92
CLAPP1978_MAXIMUM_B = 11.5
_ROUNDING_TOLERANCE = 1e-12


def evaluate_clapp1978_h_theta(parameters: ParameterValues, suction: float) -> float:
    """Evaluate the homogeneous Clapp curve; the registered adapter uses cm.

    Both suction values must share a pressure/head unit. Their ratio is the
    only dimensional input, so the canonical family can use kPa directly.
    """
    b = _positive_parameter(parameters, 'b')
    saturation_suction = _positive_parameter(parameters, 'saturation_suction')
    saturated_water_content = _parameter(parameters, 'saturated_water_content')
    if not 0.0 < saturated_water_content < 1.0:
        message = 'saturated_water_content must be between zero and one.'
        raise ModelEvaluationError(message)
    if not math.isfinite(suction) or suction < 0.0:
        message = 'Clapp-Hornberger suction must be a finite nonnegative magnitude.'
        raise ModelEvaluationError(message)

    if b >= CLAPP1978_MAXIMUM_B:
        message = 'Clapp-Hornberger gradual air entry requires b < 11.5 at fixed wetness 0.92.'
        raise ModelEvaluationError(message)
    inflection_wetness = _CLAPP1978_INFLECTION_WETNESS
    log_inflection_ratio = -b * math.log(inflection_wetness)
    if suction > saturation_suction:
        log_ratio = (
            math.log1p((suction - saturation_suction) / saturation_suction)
            if suction <= 2 * saturation_suction
            else math.log(suction) - math.log(saturation_suction)
        )
        if log_ratio >= log_inflection_ratio:
            return saturated_water_content * math.exp(-log_ratio / b)

    # Normalize pressure by psi_s before constructing the parabola. With
    # u=1-W, equation (3) becomes q=D*u-A*u**2. Rationalizing its smaller
    # root avoids subtraction near saturation and near the b=11.5 limit.
    ratio = suction / saturation_suction
    gap = 1 - inflection_wetness
    inflection_ratio = math.exp(log_inflection_ratio)
    scale = inflection_ratio * (CLAPP1978_MAXIMUM_B - b) / (inflection_wetness * gap)
    derivative = 2 * scale * gap + inflection_ratio * b / inflection_wetness
    discriminant = derivative**2 - 4 * scale * ratio
    if discriminant < 0 and discriminant > -_ROUNDING_TOLERANCE * derivative**2:
        discriminant = 0.0
    if discriminant < 0:
        message = 'Suction is outside the invertible Clapp-Hornberger parabolic branch.'
        raise ModelEvaluationError(message)
    deficit = 2 * ratio / (derivative + math.sqrt(discriminant))
    return saturated_water_content * (1 - deficit)


def evaluate_vereecken1989_h_theta(parameters: ParameterValues, suction: float) -> float:
    """Evaluate the Vereecken reduced van Genuchten curve for suction in cm."""
    theta_r = _parameter(parameters, 'theta_r')
    theta_s = _parameter(parameters, 'theta_s')
    alpha = _positive_parameter(parameters, 'alpha')
    n = _positive_parameter(parameters, 'n')
    if not 0.0 <= theta_r < theta_s <= 1.0:
        message = 'Vereecken water contents must satisfy 0 <= theta_r < theta_s <= 1.'
        raise ModelEvaluationError(message)
    if not math.isfinite(suction) or suction < 0.0:
        message = 'Vereecken suction must be a finite nonnegative magnitude.'
        raise ModelEvaluationError(message)

    if suction == 0:
        return theta_s
    log_power = n * log_positive_product(alpha, suction)
    if log_power >= 0:
        tail = math.exp(-log_power)
        effective = tail / (1 + tail)
    else:
        effective = 1 / (1 + math.exp(log_power))
    return theta_r + (theta_s - theta_r) * effective


@cache
def builtin_model_adapters() -> Mapping[str, ModelAdapter]:
    """Return the immutable registry of executable adapters shipped with ptfkit-eval."""
    specs = model_adapter_specs()
    clapp = specs['clapp1978_h_theta']
    vereecken = specs['vereecken1989_h_theta']
    return MappingProxyType(
        {
            clapp.id: ModelAdapter(clapp, evaluate_clapp1978_h_theta),
            vereecken.id: ModelAdapter(vereecken, evaluate_vereecken1989_h_theta),
        }
    )


def model_adapter_specs() -> Mapping[str, ModelAdapterSpec]:
    """Return adapter contracts suitable for evaluation-plan resolution."""
    return default_model_adapter_specs()


def _positive_parameter(parameters: ParameterValues, name: str) -> float:
    value = _parameter(parameters, name)
    if value <= 0.0:
        message = f'{name} must be positive.'
        raise ModelEvaluationError(message)
    return value


def _parameter(parameters: ParameterValues, name: str) -> float:
    try:
        value = float(parameters[name])
    except (KeyError, TypeError, ValueError) as error:
        message = f'Missing or nonnumeric model parameter {name!r}.'
        raise ModelEvaluationError(message) from error
    if not math.isfinite(value):
        message = f'Model parameter {name!r} must be finite.'
        raise ModelEvaluationError(message)
    return value
