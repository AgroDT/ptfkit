"""Executable hydraulic-model adapters for parameter-producing PTFs."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import TypeAlias, cast

from .contracts import ModelAdapterSpec, default_model_adapter_specs
from .input_derivations import COSBY_CLASS_MIDPOINTS
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
_SAXTON_FIELD_CAPACITY_KPA = 33.0
_SAXTON_MAXIMUM_SUCTION_KPA = 1500.0
_SAXTON_PARTICLE_DENSITY = 2.65
_SAXTON_MAXIMUM_CLAY = 0.60
_SAXTON_MAXIMUM_ORGANIC_MATTER = 8.0


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


def evaluate_cosby1984_dry_h_theta(parameters: ParameterValues, suction: float) -> float:
    """Evaluate the source power curve for a reviewed mineral-soil subset, in cm."""
    b = _positive_parameter(parameters, 'mean_b')
    saturated = _parameter(parameters, 'mean_theta_s')
    log_head = _parameter(parameters, 'mean_log_psi_s')
    if not 0 < saturated < 1 or not math.isfinite(suction) or suction <= 0:
        message = 'Cosby requires positive suction and saturation strictly between zero and one.'
        raise ModelEvaluationError(message)
    try:
        reference_head = 10.0**log_head
    except OverflowError as error:
        message = 'Cosby reference head cannot be represented as a finite positive value.'
        raise ModelEvaluationError(message) from error
    if not math.isfinite(reference_head) or reference_head <= 0:
        message = 'Cosby reference head cannot be represented as a finite positive value.'
        raise ModelEvaluationError(message)
    if suction < reference_head:
        message = 'Cosby dry power curve has no registered wet branch below its reference head.'
        raise ModelEvaluationError(message)
    log_ratio = (
        math.log1p((suction - reference_head) / reference_head)
        if suction <= 2 * reference_head
        else math.log(suction) - math.log(reference_head)
    )
    water = saturated * math.exp(-log_ratio / b)
    if not math.isfinite(water) or water <= 0:
        message = 'Cosby dry power-curve water content is unrepresentable.'
        raise ModelEvaluationError(message)
    return water


@cache
def builtin_model_adapters() -> Mapping[str, ModelAdapter]:
    """Return the immutable registry of executable adapters shipped with ptfkit-eval."""
    specs = model_adapter_specs()
    clapp = specs['clapp1978_h_theta']
    vereecken = specs['vereecken1989_h_theta']
    wosten = specs['wosten2001_h_theta']
    saxton = specs['saxton2006_h_theta']
    cosby = specs['cosby1984_class_midpoint_dry_h_theta']
    return MappingProxyType(
        {
            clapp.id: ModelAdapter(clapp, evaluate_clapp1978_h_theta),
            vereecken.id: ModelAdapter(vereecken, evaluate_vereecken1989_h_theta),
            wosten.id: ModelAdapter(wosten, evaluate_van_genuchten_mualem_h_theta),
            saxton.id: ModelAdapter(saxton, evaluate_saxton2006_h_theta),
            cosby.id: ModelAdapter(cosby, evaluate_cosby1984_dry_h_theta),
        }
    )


def evaluate_van_genuchten_mualem_h_theta(parameters: ParameterValues, suction: float) -> float:
    """Evaluate theta(h) with m = 1 - 1/n; alpha and suction use reciprocal units."""
    theta_r = _parameter(parameters, 'theta_r')
    theta_s = _parameter(parameters, 'theta_s')
    alpha = _positive_parameter(parameters, 'alpha')
    n = _positive_parameter(parameters, 'n')
    if not 0 <= theta_r < theta_s <= 1:
        message = 'van Genuchten water contents must satisfy 0 <= theta_r < theta_s <= 1.'
        raise ModelEvaluationError(message)
    if n <= 1:
        message = 'The Mualem van Genuchten convention requires n > 1.'
        raise ModelEvaluationError(message)
    if not math.isfinite(suction) or suction < 0:
        message = 'van Genuchten suction must be a finite nonnegative magnitude.'
        raise ModelEvaluationError(message)
    if suction == 0:
        return theta_s
    power_log = n * log_positive_product(alpha, suction)
    log_denominator = max(power_log, 0.0) + math.log1p(math.exp(-abs(power_log)))
    m = (n - 1) / n
    effective = math.exp(-m * log_denominator)
    return theta_r + (theta_s - theta_r) * effective


def validate_function_inputs(function: Mapping[str, object], inputs: Mapping[str, object]) -> None:
    """Enforce reviewed joint input constraints for every native execution path."""
    if function.get('id') == 'calc_ptf_saxton2006':
        _validate_saxton2006_inputs(inputs)
    elif function.get('id') == 'calc_ptf_cosby1984_univariate':
        coordinates = tuple(
            _parameter(cast('ParameterValues', inputs), name) for name in ('sand', 'silt', 'clay')
        )
        if coordinates not in COSBY_CLASS_MIDPOINTS.values():
            message = 'Source-faithful Cosby evaluation requires a complete Table 2 class midpoint.'
            raise ModelEvaluationError(message)


def _validate_saxton2006_inputs(inputs: Mapping[str, object]) -> None:
    try:
        sand, clay, organic_matter = (
            _parameter(cast('ParameterValues', inputs), name)
            for name in ('sand', 'clay', 'organic_matter')
        )
    except (KeyError, ValueError, TypeError) as error:
        message = 'Saxton inputs require numeric sand, clay and organic matter.'
        raise ModelEvaluationError(message) from error
    if (
        any(isinstance(inputs[name], bool) for name in ('sand', 'clay', 'organic_matter'))
        or not all(math.isfinite(value) for value in (sand, clay, organic_matter))
        or not 0 <= sand <= 1
        or not 0 <= clay <= _SAXTON_MAXIMUM_CLAY
        or sand + clay > 1
        or not 0 <= organic_matter <= _SAXTON_MAXIMUM_ORGANIC_MATTER
    ):
        message = (
            'Saxton inputs must satisfy texture fractions, sand+clay<=1, clay<=0.60 and OM<=8%.'
        )
        raise ModelEvaluationError(message)


def evaluate_saxton2006_h_theta(parameters: ParameterValues, suction: float) -> float:
    """Invert source Equations 6 and 11-15 at normal density, in kPa and volume fraction."""
    density = _positive_parameter(parameters, 'normal_density')
    entry = _parameter(parameters, 'air_entry_tension')
    coefficient = _positive_parameter(parameters, 'retention_a')
    exponent = _positive_parameter(parameters, 'retention_b')
    theta_s = 1 - density / _SAXTON_PARTICLE_DENSITY
    if not 0 < theta_s < 1 or not 0 < entry < _SAXTON_FIELD_CAPACITY_KPA:
        message = 'Saxton normal-density saturation and air-entry parameters are nonphysical.'
        raise ModelEvaluationError(message)
    if not math.isfinite(suction) or not 0 <= suction <= _SAXTON_MAXIMUM_SUCTION_KPA:
        message = 'Saxton retention is registered only for finite magnitudes from 0 to 1500 kPa.'
        raise ModelEvaluationError(message)
    log_coefficient = math.log(coefficient)
    log_theta_33 = (log_coefficient - math.log(_SAXTON_FIELD_CAPACITY_KPA)) / exponent
    if log_theta_33 >= math.log(theta_s):
        message = 'Saxton water anchors must satisfy theta_33 < theta_s.'
        raise ModelEvaluationError(message)
    theta_33 = math.exp(log_theta_33)
    if theta_33 <= 0:
        message = 'Saxton theta_33 is not representable as a positive volume fraction.'
        raise ModelEvaluationError(message)
    if suction <= entry:
        return theta_s
    if suction < _SAXTON_FIELD_CAPACITY_KPA:
        return theta_33 + (_SAXTON_FIELD_CAPACITY_KPA - suction) * (theta_s - theta_33) / (
            _SAXTON_FIELD_CAPACITY_KPA - entry
        )
    value = math.exp((log_coefficient - math.log(suction)) / exponent)
    if value <= 0:
        message = 'Saxton dry-branch water content underflows its positive domain.'
        raise ModelEvaluationError(message)
    return value


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
