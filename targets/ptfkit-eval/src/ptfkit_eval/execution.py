"""Execute resolved curve candidates with unit conversion and provenance traces."""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from numbers import Real
from typing import TYPE_CHECKING, overload

from ptfkit import get_manifest

from .adapters import ModelAdapter, builtin_model_adapters, validate_function_inputs
from .contracts import (
    AdapterPrediction,
    AtomicCurve,
    FunctionCurveCandidate,
    OutputPrediction,
    RangeGatedCurveCandidate,
    fixed_output_predictions,
)
from .unit_conversion import convert_with_units


if TYPE_CHECKING:
    from .contracts import FixedPointPrediction


class CurveExecutionError(ValueError):
    """Raised when a resolved curve cannot be evaluated with the supplied inputs."""


@dataclass(frozen=True)
class PointContribution:
    """One model's value and routing weight at an evaluated axis point."""

    member_id: str
    function: str
    weight: float
    value: float


@dataclass(frozen=True)
class CurvePoint:
    """One predicted value with all model contributions retained."""

    axis_value: float
    value: float
    contributions: tuple[PointContribution, ...]


@dataclass(frozen=True)
class CurveEvaluation:
    """Predicted curve in the candidate's declared axis and target units."""

    candidate_id: str
    points: tuple[CurvePoint, ...]


@overload
def evaluate_candidate(
    candidate: FunctionCurveCandidate,
    axis_values: Sequence[float],
    inputs: Mapping[str, object],
    *,
    manifest: Mapping[str, object] | None = None,
    model_adapters: Mapping[str, ModelAdapter] | None = None,
) -> CurveEvaluation: ...


@overload
def evaluate_candidate(
    candidate: RangeGatedCurveCandidate,
    axis_values: Sequence[float],
    inputs: Mapping[str, Mapping[str, object]],
    *,
    manifest: Mapping[str, object] | None = None,
    model_adapters: Mapping[str, ModelAdapter] | None = None,
) -> CurveEvaluation: ...


def evaluate_candidate(
    candidate: FunctionCurveCandidate | RangeGatedCurveCandidate,
    axis_values: Sequence[float],
    inputs: Mapping[str, object] | Mapping[str, Mapping[str, object]],
    *,
    manifest: Mapping[str, object] | None = None,
    model_adapters: Mapping[str, ModelAdapter] | None = None,
) -> CurveEvaluation:
    """Evaluate one function or range-gated curve candidate at declared axis values."""
    manifest_document = get_manifest() if manifest is None else manifest
    adapters = builtin_model_adapters() if model_adapters is None else model_adapters
    functions = _functions_by_id(manifest_document)

    if isinstance(candidate, FunctionCurveCandidate):
        evaluator = _atomic_evaluator(
            candidate.curve,
            axis_unit=candidate.axis.unit,
            target_unit=candidate.target.unit,
            inputs=_flat_inputs(inputs),
            functions=functions,
            manifest=manifest_document,
            adapters=adapters,
        )
        points = tuple(
            _function_point(candidate.id, candidate.curve.function, axis_value, evaluator)
            for axis_value in axis_values
        )
        return CurveEvaluation(candidate.id, points)

    routed_points = [
        (
            float(value),
            tuple(item for item in candidate.router.route(float(value)) if item.weight > 0),
        )
        for value in axis_values
    ]
    active_members = {item.member_id for _, routed in routed_points for item in routed}
    member_evaluators: dict[str, Callable[[float], float]] = {}
    for member in candidate.members:
        if member.id not in active_members:
            continue
        member_inputs = inputs.get(member.id)
        if not isinstance(member_inputs, Mapping):
            message = f'Missing input mapping for composite member {member.id!r}.'
            raise CurveExecutionError(message)
        member_evaluators[member.id] = _atomic_evaluator(
            member.curve,
            axis_unit=candidate.axis.unit,
            target_unit=candidate.target.unit,
            inputs=member_inputs,
            functions=functions,
            manifest=manifest_document,
            adapters=adapters,
        )

    member_index = {member.id: member for member in candidate.members}
    points: list[CurvePoint] = []
    for axis_value, routed in routed_points:
        contributions = tuple(
            PointContribution(
                contribution.member_id,
                member_index[contribution.member_id].curve.function,
                contribution.weight,
                member_evaluators[contribution.member_id](axis_value),
            )
            for contribution in routed
        )
        value = math.fsum(item.weight * item.value for item in contributions)
        points.append(CurvePoint(axis_value, value, contributions))
    return CurveEvaluation(candidate.id, tuple(points))


def convert_value(
    value: float,
    source_unit: str,
    target_unit: str,
    *,
    manifest: Mapping[str, object] | None = None,
) -> float:
    """Convert one scalar through the manifest's affine SI conversion contract."""
    numeric_value = float(value)
    if source_unit == target_unit:
        return numeric_value
    document = get_manifest() if manifest is None else manifest
    units = document.get('units')
    if not isinstance(units, Mapping):
        message = 'Manifest has no unit registry.'
        raise CurveExecutionError(message)
    try:
        return convert_with_units(numeric_value, source_unit, target_unit, units)
    except ValueError as error:
        raise CurveExecutionError(str(error)) from error


def _function_point(
    candidate_id: str,
    function_id: str,
    raw_axis_value: float,
    evaluator: Callable[[float], float],
) -> CurvePoint:
    axis_value = float(raw_axis_value)
    value = evaluator(axis_value)
    contribution = PointContribution(candidate_id, function_id, 1.0, value)
    return CurvePoint(axis_value, value, (contribution,))


def _atomic_evaluator(
    curve: AtomicCurve,
    *,
    axis_unit: str,
    target_unit: str,
    inputs: Mapping[str, object],
    functions: Mapping[str, Mapping[str, object]],
    manifest: Mapping[str, object],
    adapters: Mapping[str, ModelAdapter],
) -> Callable[[float], float]:
    function = functions.get(curve.function)
    if function is None:
        message = f'Function {curve.function!r} is absent from the execution manifest.'
        raise CurveExecutionError(message)
    callable_ = _load_callable(function)
    outputs = function.get('outputs')
    scalar_output = (
        isinstance(outputs, Sequence)
        and not isinstance(outputs, (str, bytes))
        and len(outputs) == 1
    )

    if isinstance(curve.prediction, AdapterPrediction):
        adapter = adapters.get(curve.prediction.adapter)
        if adapter is None:
            message = f'Model adapter {curve.prediction.adapter!r} has no implementation.'
            raise CurveExecutionError(message)
        if (
            adapter.spec.supported_functions is not None
            and curve.function not in adapter.spec.supported_functions
        ):
            message = (
                f'Function {curve.function!r} is not reviewed for adapter {adapter.spec.id!r}.'
            )
            raise CurveExecutionError(message)
        result = callable_(**_coerce_inputs(function, inputs))
        parameters = {
            parameter.output: convert_value(
                _result_value(result, parameter.output),
                _output_unit(function, parameter.output),
                parameter.unit,
                manifest=manifest,
            )
            for parameter in adapter.spec.parameters
        }

        def evaluate_adapter(axis_value: float) -> float:
            adapter_axis = convert_value(
                axis_value, axis_unit, adapter.spec.axis_unit, manifest=manifest
            )
            prediction = adapter.evaluate(parameters, adapter_axis)
            return convert_value(
                prediction, adapter.spec.target_unit, target_unit, manifest=manifest
            )

        return evaluate_adapter

    fixed_outputs = fixed_output_predictions(curve.prediction)
    if fixed_outputs:
        return _fixed_evaluator(
            fixed_outputs,
            callable_,
            function=function,
            inputs=inputs,
            axis_unit=axis_unit,
            target_unit=target_unit,
            manifest=manifest,
            scalar_output=scalar_output,
        )

    prediction = curve.prediction
    if not isinstance(prediction, OutputPrediction):
        message = 'Unknown prediction binding.'
        raise CurveExecutionError(message)

    def evaluate_output(axis_value: float) -> float:
        function_inputs = dict(inputs)
        function_inputs[prediction.axis_input] = convert_value(
            axis_value, axis_unit, prediction.axis_unit, manifest=manifest
        )
        result = callable_(**_coerce_inputs(function, function_inputs))
        output = _result_value(result, prediction.output, scalar_output=scalar_output)
        output_unit = _output_unit(function, prediction.output)
        return convert_value(output, output_unit, target_unit, manifest=manifest)

    return evaluate_output


def _fixed_evaluator(
    points: tuple[FixedPointPrediction, ...],
    callable_: Callable[..., object],
    *,
    function: Mapping[str, object],
    inputs: Mapping[str, object],
    axis_unit: str,
    target_unit: str,
    manifest: Mapping[str, object],
    scalar_output: bool,
) -> Callable[[float], float]:
    support = {
        convert_value(point.axis_value, point.axis_unit, axis_unit, manifest=manifest): point
        for point in points
    }
    if len(support) != len(points) or any(
        not math.isfinite(value) or value < 0 for value in support
    ):
        message = 'Fixed outputs require distinct finite nonnegative converted pressures.'
        raise CurveExecutionError(message)

    def evaluate(axis_value: float) -> float:
        fixed = support.get(axis_value)
        if fixed is None:
            message = 'Fixed-pressure output cannot be evaluated at another pressure.'
            raise CurveExecutionError(message)
        result = callable_(**_coerce_inputs(function, inputs))
        return convert_value(
            _result_value(result, fixed.output, scalar_output=scalar_output),
            _output_unit(function, fixed.output),
            target_unit,
            manifest=manifest,
        )

    return evaluate


def _load_callable(function: Mapping[str, object]) -> Callable[..., object]:
    module_name = function.get('module')
    callable_name = function.get('callable')
    if not isinstance(module_name, str) or not isinstance(callable_name, str):
        message = 'Manifest function is missing its Python module or callable.'
        raise CurveExecutionError(message)
    loaded = getattr(import_module(module_name), callable_name, None)
    if not callable(loaded):
        message = f'Manifest callable {module_name}.{callable_name} is unavailable.'
        raise CurveExecutionError(message)
    return loaded


def _coerce_inputs(
    function: Mapping[str, object], supplied: Mapping[str, object]
) -> dict[str, object]:
    bindings = function.get('inputs')
    if not isinstance(bindings, Sequence) or isinstance(bindings, (str, bytes)):
        message = 'Manifest function has no valid input bindings.'
        raise CurveExecutionError(message)
    expected_names = {binding.get('name') for binding in bindings if isinstance(binding, Mapping)}
    unknown = set(supplied) - expected_names
    if unknown:
        message = f'Unknown function inputs: {sorted(unknown)!r}.'
        raise CurveExecutionError(message)

    result: dict[str, object] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping) or not isinstance(binding.get('name'), str):
            message = 'Manifest contains an invalid input binding.'
            raise CurveExecutionError(message)
        name = binding['name']
        if name not in supplied:
            message = f'Missing function input {name!r}.'
            raise CurveExecutionError(message)
        value = supplied[name]
        result[name] = (
            float(value)
            if binding.get('kind') == 'numeric'
            and isinstance(value, Real)
            and not isinstance(value, bool)
            else _coerce_categorical(binding, value)
        )
    validate_function_inputs(function, result)
    return result


def _coerce_categorical(  # noqa: PLR0911
    binding: Mapping[str, object], value: object
) -> object:
    if binding.get('kind') != 'categorical' or isinstance(value, Enum):
        return value
    enum_document = binding.get('enum')
    if not isinstance(enum_document, Mapping) or not isinstance(value, str):
        return value
    enum_id = enum_document.get('id')
    values = enum_document.get('values')
    if not isinstance(enum_id, str) or not isinstance(values, Sequence):
        return value
    enum_name = enum_id.rsplit('.', maxsplit=1)[-1]
    module_name = binding.get('_module')
    if not isinstance(module_name, str):
        return value
    enum_type = getattr(import_module(module_name), enum_name, None)
    if not isinstance(enum_type, type) or not issubclass(enum_type, Enum):
        return value
    for item in values:
        if not isinstance(item, Mapping):
            continue
        if value in (item.get('name'), item.get('value')):
            member_name = item.get('name')
            if isinstance(member_name, str):
                return enum_type[member_name.upper()]
    return value


def _functions_by_id(
    manifest: Mapping[str, object],
) -> Mapping[str, Mapping[str, object]]:
    values = manifest.get('functions')
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        message = 'Manifest has no function registry.'
        raise CurveExecutionError(message)
    indexed: dict[str, Mapping[str, object]] = {}
    for value in values:
        if not isinstance(value, Mapping) or not isinstance(value.get('id'), str):
            message = 'Manifest contains an invalid function entry.'
            raise CurveExecutionError(message)
        function = dict(value)
        bindings = function.get('inputs')
        if isinstance(bindings, Sequence) and not isinstance(bindings, (str, bytes)):
            function['inputs'] = [
                {**binding, '_module': function.get('module')}
                if isinstance(binding, Mapping)
                else binding
                for binding in bindings
            ]
        indexed[function['id']] = function
    return indexed


def _result_value(result: object, name: str, *, scalar_output: bool = False) -> float:
    if scalar_output and isinstance(result, Real) and not isinstance(result, bool):
        return float(result)
    try:
        return float(getattr(result, name))
    except (AttributeError, TypeError, ValueError) as error:
        message = f'Function result has no numeric field {name!r}.'
        raise CurveExecutionError(message) from error


def _output_unit(function: Mapping[str, object], output_name: str) -> str:
    outputs = function.get('outputs')
    if isinstance(outputs, Sequence) and not isinstance(outputs, (str, bytes)):
        for output in outputs:
            if not isinstance(output, Mapping) or output.get('name') != output_name:
                continue
            measurement = output.get('measurement')
            if isinstance(measurement, Mapping) and isinstance(measurement.get('unit'), str):
                return measurement['unit']
    message = f'Manifest output {output_name!r} has no unit.'
    raise CurveExecutionError(message)


def _flat_inputs(
    inputs: Mapping[str, object] | Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    return inputs
