"""Executable hydraulic-model adapters for parameter-producing PTFs."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import TypeAlias

from .contracts import ModelAdapterSpec, default_model_adapter_specs


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
_ROUNDING_TOLERANCE = 1e-12


def evaluate_clapp1978_h_theta(parameters: ParameterValues, suction: float) -> float:
    """Evaluate the Clapp-Hornberger retention curve for a suction magnitude in cm."""
    b = _positive_parameter(parameters, 'b')
    saturation_suction = _positive_parameter(parameters, 'saturation_suction')
    saturated_water_content = _parameter(parameters, 'saturated_water_content')
    if not 0.0 < saturated_water_content < 1.0:
        message = 'saturated_water_content must be between zero and one.'
        raise ModelEvaluationError(message)
    if not math.isfinite(suction) or suction < 0.0:
        message = 'Clapp-Hornberger suction must be a finite nonnegative magnitude.'
        raise ModelEvaluationError(message)

    inflection_wetness = _CLAPP1978_INFLECTION_WETNESS
    inflection_suction = saturation_suction * inflection_wetness ** (-b)
    if suction >= inflection_suction:
        wetness = (saturation_suction / suction) ** (1.0 / b)
        return saturated_water_content * wetness

    gap = 1.0 - inflection_wetness
    parabola_scale = inflection_suction / gap**2 - (
        inflection_suction * b / (inflection_wetness * gap)
    )
    if parabola_scale <= 0.0:
        message = 'Clapp-Hornberger parameters do not define the gradual-air-entry parabola.'
        raise ModelEvaluationError(message)
    second_root = (
        2.0 * inflection_wetness
        - inflection_suction * b / (parabola_scale * inflection_wetness)
        - 1.0
    )
    discriminant = (second_root + 1.0) ** 2 - 4.0 * (second_root + suction / parabola_scale)
    if discriminant < 0.0 and discriminant > -_ROUNDING_TOLERANCE:
        discriminant = 0.0
    if discriminant < 0.0:
        message = 'Suction is outside the invertible Clapp-Hornberger parabolic branch.'
        raise ModelEvaluationError(message)
    wetness = (second_root + 1.0 + math.sqrt(discriminant)) / 2.0
    return saturated_water_content * wetness


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

    try:
        scaled_power = (alpha * suction) ** n
    except OverflowError:
        return theta_r
    if not math.isfinite(scaled_power):
        return theta_r
    return theta_r + (theta_s - theta_r) / (1.0 + scaled_power)


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
