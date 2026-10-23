"""Load and resolve evaluation plans against the installed ptfkit manifest."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from itertools import combinations
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TypeAlias, TypeGuard, cast

import yaml
from jsonschema import Draft202012Validator
from ptfkit import get_manifest

from .composites import (
    AxisTransform,
    BlendTransition,
    BlendWeighting,
    BoundaryMember,
    HardSwitchTransition,
    Interval,
    RangeGatedRouter,
    Transition,
)


JsonScalar: TypeAlias = bool | int | float | str | None
JsonValue: TypeAlias = JsonScalar | list['JsonValue'] | dict[str, 'JsonValue']
PredictionBinding: TypeAlias = 'OutputPrediction | AdapterPrediction | FixedPointPrediction'
CurveCandidate: TypeAlias = 'FunctionCurveCandidate | RangeGatedCurveCandidate'
ModelKind: TypeAlias = Literal['h_theta', 'k_h']
AxisConvention: TypeAlias = Literal['signed', 'magnitude']
ProvenanceKind: TypeAlias = Literal['fixed', 'learned']


@dataclass(frozen=True)
class PlanDiagnostic:
    """One machine-readable plan validation failure."""

    path: str
    code: str
    message: str


class PlanLoadError(ValueError):
    """Raised when an evaluation-plan document cannot be read as JSON data."""


class PlanValidationError(ValueError):
    """Raised when an evaluation plan violates schema or manifest contracts."""

    diagnostics: tuple[PlanDiagnostic, ...]

    def __init__(self, diagnostics: Sequence[PlanDiagnostic]) -> None:
        """Preserve every independent diagnostic in deterministic order."""
        self.diagnostics = tuple(diagnostics)
        summary = '; '.join(
            f'{diagnostic.path}: {diagnostic.code}' for diagnostic in self.diagnostics
        )
        super().__init__(summary)


@dataclass(frozen=True)
class AxisSpec:
    """Canonical independent variable for a curve candidate."""

    quantity: str
    unit: str
    convention: AxisConvention
    transform: AxisTransform


@dataclass(frozen=True)
class TargetSpec:
    """Canonical predicted measurement for a curve candidate."""

    quantity: str
    unit: str
    material_basis: str
    denominator_basis: str


@dataclass(frozen=True)
class ModelParameterSpec:
    """Manifest output required by a registered model adapter."""

    output: str
    quantity: str
    unit: str
    material_basis: str
    denominator_basis: str


@dataclass(frozen=True)
class ModelAdapterSpec:
    """Physical contract for converting PTF outputs into a curve."""

    id: str
    model_kind: ModelKind
    axis_quantity: str
    axis_unit: str
    axis_convention: AxisConvention
    target_quantity: str
    target_unit: str
    target_material_basis: str
    target_denominator_basis: str
    parameters: tuple[ModelParameterSpec, ...]

    def __post_init__(self) -> None:
        """Reject adapter registrations with ambiguous parameter bindings."""
        outputs = tuple(parameter.output for parameter in self.parameters)
        if not outputs:
            message = 'A model adapter must declare at least one parameter output.'
            raise ValueError(message)
        if len(outputs) != len(set(outputs)):
            message = 'A model adapter cannot bind one output more than once.'
            raise ValueError(message)


@cache
def default_model_adapter_specs() -> Mapping[str, ModelAdapterSpec]:
    """Return contracts for the model adapters shipped with ptfkit-eval."""
    clapp = ModelAdapterSpec(
        id='clapp1978_h_theta',
        model_kind='h_theta',
        axis_quantity='matric_potential',
        axis_unit='centimeter_water_head',
        axis_convention='magnitude',
        target_quantity='volumetric_water_content',
        target_unit='volume_fraction',
        target_material_basis='mineral_soil',
        target_denominator_basis='bulk_volume',
        parameters=(
            ModelParameterSpec(
                'b', 'campbell_b', 'dimensionless', 'mineral_soil', 'not_applicable'
            ),
            ModelParameterSpec(
                'saturation_suction',
                'matric_potential',
                'centimeter_water_head',
                'mineral_soil',
                'not_applicable',
            ),
            ModelParameterSpec(
                'saturated_water_content',
                'volumetric_water_content',
                'volume_fraction',
                'mineral_soil',
                'bulk_volume',
            ),
        ),
    )
    vereecken = ModelAdapterSpec(
        id='vereecken1989_h_theta',
        model_kind='h_theta',
        axis_quantity='matric_potential',
        axis_unit='centimeter_water_head',
        axis_convention='magnitude',
        target_quantity='volumetric_water_content',
        target_unit='volume_fraction',
        target_material_basis='mineral_soil',
        target_denominator_basis='bulk_volume',
        parameters=(
            ModelParameterSpec(
                'theta_r',
                'volumetric_water_content',
                'volume_fraction',
                'mineral_soil',
                'bulk_volume',
            ),
            ModelParameterSpec(
                'theta_s',
                'volumetric_water_content',
                'volume_fraction',
                'mineral_soil',
                'bulk_volume',
            ),
            ModelParameterSpec(
                'alpha',
                'van_genuchten_alpha',
                'inverse_centimeter',
                'mineral_soil',
                'not_applicable',
            ),
            ModelParameterSpec(
                'n',
                'van_genuchten_n',
                'dimensionless',
                'mineral_soil',
                'not_applicable',
            ),
        ),
    )
    return MappingProxyType({clapp.id: clapp, vereecken.id: vereecken})


@dataclass(frozen=True)
class OutputPrediction:
    """Direct curve output selected from a manifest function."""

    output: str
    axis_input: str
    axis_unit: str


@dataclass(frozen=True)
class AdapterPrediction:
    """Registered model adapter selected for a manifest function."""

    adapter: str


@dataclass(frozen=True)
class FixedPointPrediction:
    """Direct output at exactly one manifest-declared pressure condition."""

    output: str
    axis_value: float
    axis_unit: str
    method: str | None


@dataclass(frozen=True)
class AtomicCurve:
    """One manifest function and its resolved prediction binding."""

    function: str
    prediction: PredictionBinding


@dataclass(frozen=True)
class FunctionCurveCandidate:
    """One atomic function evaluated as a curve candidate."""

    id: str
    axis: AxisSpec
    target: TargetSpec
    curve: AtomicCurve


@dataclass(frozen=True)
class FunctionPointCandidate(FunctionCurveCandidate):
    """One function output with fixed pressure support, without interpolation."""


@dataclass(frozen=True)
class CompositeMember:
    """One range-limited member of a composite curve."""

    id: str
    interval: Interval
    curve: AtomicCurve


@dataclass(frozen=True)
class Provenance:
    """Origin of composite boundaries and routing rules."""

    kind: ProvenanceKind
    source: str
    training_protocol: str | None


@dataclass(frozen=True)
class RangeGatedCurveCandidate:
    """Resolved range-gated curve with deterministic routing."""

    id: str
    axis: AxisSpec
    target: TargetSpec
    members: tuple[CompositeMember, ...]
    router: RangeGatedRouter
    provenance: Provenance


@dataclass(frozen=True)
class EvaluationPlan:
    """Validated immutable evaluation-plan contract."""

    schema_version: int
    ptfkit_manifest_schema_version: int
    candidates: tuple[CurveCandidate, ...]


@dataclass(frozen=True)
class _ManifestIndex:
    schema_version: int
    functions: Mapping[str, Mapping[str, object]]
    quantities: Mapping[str, Mapping[str, object]]
    units: Mapping[str, Mapping[str, object]]


@dataclass(frozen=True)
class _ResolutionContext:
    index: _ManifestIndex
    adapters: Mapping[str, ModelAdapterSpec]
    diagnostics: list[PlanDiagnostic]


@dataclass(frozen=True)
class _CandidateContext:
    axis: AxisSpec
    target: TargetSpec
    path: str
    resolution: _ResolutionContext


def load_evaluation_plan(
    source: str | Path | Mapping[str, object],
    *,
    manifest: Mapping[str, object] | None = None,
    model_adapters: Mapping[str, ModelAdapterSpec] | None = None,
) -> EvaluationPlan:
    """Load, validate, and resolve an evaluation plan against a function manifest."""
    document = _load_document(source)
    diagnostics = _schema_diagnostics(document)
    if diagnostics:
        raise PlanValidationError(diagnostics)

    root = _mapping(document)
    manifest_document = get_manifest() if manifest is None else manifest
    index = _index_manifest(manifest_document, diagnostics)
    if index is None:
        raise PlanValidationError(diagnostics)

    required_manifest_version = _integer(root['ptfkit_manifest_schema_version'])
    if required_manifest_version != index.schema_version:
        diagnostics.append(
            PlanDiagnostic(
                '$.ptfkit_manifest_schema_version',
                'manifest.schema_version_mismatch',
                f'Plan requires manifest schema {required_manifest_version}, '
                f'but ptfkit provides {index.schema_version}.',
            )
        )

    adapters = _adapter_registry(model_adapters, diagnostics)
    resolved = _resolve_candidates(root, index, adapters, diagnostics)

    if diagnostics:
        raise PlanValidationError(diagnostics)
    return EvaluationPlan(
        schema_version=_integer(root['schema_version']),
        ptfkit_manifest_schema_version=required_manifest_version,
        candidates=resolved,
    )


def _adapter_registry(
    model_adapters: Mapping[str, ModelAdapterSpec] | None,
    diagnostics: list[PlanDiagnostic],
) -> Mapping[str, ModelAdapterSpec]:
    if model_adapters is None:
        adapters = dict(default_model_adapter_specs())
    else:
        adapters = dict(model_adapters)
    for adapter_id, adapter in adapters.items():
        if adapter_id == adapter.id:
            continue
        diagnostics.append(
            PlanDiagnostic(
                f'$model_adapters.{adapter_id}',
                'adapter.id_mismatch',
                f'Registry key {adapter_id!r} does not match adapter id {adapter.id!r}.',
            )
        )
    return MappingProxyType(adapters)


def _resolve_candidates(
    root: Mapping[str, object],
    index: _ManifestIndex,
    adapters: Mapping[str, ModelAdapterSpec],
    diagnostics: list[PlanDiagnostic],
) -> tuple[CurveCandidate, ...]:
    resolved: list[CurveCandidate] = []
    candidate_ids: set[str] = set()
    for position, value in enumerate(_sequence(root['candidates'])):
        candidate = _mapping(value)
        path = f'$.candidates[{position}]'
        candidate_id = _string(candidate['id'])
        if candidate_id in candidate_ids:
            diagnostics.append(
                PlanDiagnostic(
                    f'{path}.id',
                    'plan.duplicate_candidate',
                    f'Candidate id {candidate_id!r} is already defined.',
                )
            )
        candidate_ids.add(candidate_id)

        before = len(diagnostics)
        axis = _parse_axis(_mapping(candidate['axis']))
        target = _parse_target(_mapping(candidate['target']))
        _validate_quantity_unit(axis.quantity, axis.unit, index, f'{path}.axis', diagnostics)
        _validate_quantity_unit(target.quantity, target.unit, index, f'{path}.target', diagnostics)
        context = _CandidateContext(
            axis,
            target,
            path,
            _ResolutionContext(index, adapters, diagnostics),
        )
        resolved_candidate = _resolve_candidate(candidate, context)
        if resolved_candidate is not None and len(diagnostics) == before:
            resolved.append(resolved_candidate)
    return tuple(resolved)


def _resolve_candidate(
    candidate: Mapping[str, object],
    context: _CandidateContext,
) -> CurveCandidate | None:
    candidate_id = _string(candidate['id'])
    if candidate['kind'] in ('function_curve', 'function_point'):
        curve = _resolve_curve(
            _string(candidate['function']),
            _mapping(candidate['prediction']),
            context,
        )
        if curve is None:
            return None
        candidate_type = (
            FunctionPointCandidate
            if candidate['kind'] == 'function_point'
            else FunctionCurveCandidate
        )
        return candidate_type(candidate_id, context.axis, context.target, curve)
    return _resolve_composite(candidate, context)


def _resolve_composite(
    candidate: Mapping[str, object],
    context: _CandidateContext,
) -> RangeGatedCurveCandidate | None:
    candidate_id = _string(candidate['id'])
    path = context.path
    diagnostics = context.resolution.diagnostics
    before = len(diagnostics)
    members: list[CompositeMember] = []
    member_ids: set[str] = set()
    for position, value in enumerate(_sequence(candidate['members'])):
        member = _mapping(value)
        member_path = f'{path}.members[{position}]'
        member_id = _string(member['id'])
        if member_id in member_ids:
            diagnostics.append(
                PlanDiagnostic(
                    f'{member_path}.id',
                    'composite.duplicate_member',
                    f'Member id {member_id!r} is already defined.',
                )
            )
        member_ids.add(member_id)
        interval = _parse_interval(member['interval'], f'{member_path}.interval', diagnostics)
        curve = _resolve_curve(
            _string(member['function']),
            _mapping(member['prediction']),
            _CandidateContext(
                context.axis,
                context.target,
                member_path,
                context.resolution,
            ),
        )
        if interval is not None and curve is not None:
            members.append(CompositeMember(member_id, interval, curve))

    routing = _mapping(candidate['routing'])
    transitions = _parse_transitions(routing['transitions'], f'{path}.routing', diagnostics)
    router: RangeGatedRouter | None = None
    if len(members) == len(_sequence(candidate['members'])) and transitions is not None:
        member_intervals = {member.id: member.interval for member in members}
        _validate_overlap_routing(members, transitions, f'{path}.routing', diagnostics)
        try:
            router = RangeGatedRouter(member_intervals, transitions, context.axis.transform)
        except ValueError as error:
            diagnostics.append(
                PlanDiagnostic(
                    f'{path}.routing',
                    'composite.invalid_routing',
                    str(error),
                )
            )

    provenance_document = _mapping(candidate['provenance'])
    provenance = Provenance(
        kind=cast('ProvenanceKind', _string(provenance_document['kind'])),
        source=_string(provenance_document['source']),
        training_protocol=(
            _string(provenance_document['training_protocol'])
            if 'training_protocol' in provenance_document
            else None
        ),
    )
    if router is None or len(diagnostics) != before:
        return None
    return RangeGatedCurveCandidate(
        candidate_id,
        context.axis,
        context.target,
        tuple(members),
        router,
        provenance,
    )


def _resolve_curve(  # noqa: PLR0911
    function_id: str,
    prediction: Mapping[str, object],
    context: _CandidateContext,
) -> AtomicCurve | None:
    path = context.path
    resolution = context.resolution
    index = resolution.index
    diagnostics = resolution.diagnostics
    function = index.functions.get(function_id)
    if function is None:
        diagnostics.append(
            PlanDiagnostic(
                f'{path}.function',
                'manifest.unknown_function',
                f'Function {function_id!r} is absent from the installed manifest.',
            )
        )
        return None

    if prediction['kind'] == 'fixed_output':
        return _resolve_fixed_output(function_id, function, prediction, context)
    if prediction['kind'] == 'output':
        output_name = _string(prediction['name'])
        output = _binding_by_name(function['outputs'], output_name)
        if output is None:
            diagnostics.append(
                PlanDiagnostic(
                    f'{path}.prediction.name',
                    'manifest.unknown_output',
                    f'Function {function_id!r} has no output {output_name!r}.',
                )
            )
            return None
        _validate_output_measurement(
            output,
            context.target,
            f'{path}.prediction.name',
            'prediction',
            resolution,
        )
        axis_inputs = _axis_inputs(function, context.axis, index)
        if not axis_inputs:
            diagnostics.append(
                PlanDiagnostic(
                    f'{path}.axis',
                    'curve.axis_input_missing',
                    f'Function {function_id!r} has no compatible numeric input for the curve axis.',
                )
            )
            return None
        if len(axis_inputs) > 1:
            diagnostics.append(
                PlanDiagnostic(
                    f'{path}.axis',
                    'curve.axis_input_ambiguous',
                    f'Function {function_id!r} has multiple compatible numeric axis inputs.',
                )
            )
            return None
        axis_input = axis_inputs[0]
        measurement = _mapping(axis_input['measurement'])
        return AtomicCurve(
            function_id,
            OutputPrediction(
                output_name,
                _string(axis_input['name']),
                _string(measurement['unit']),
            ),
        )

    adapter_id = _string(prediction['id'])
    adapter = resolution.adapters.get(adapter_id)
    if adapter is None:
        diagnostics.append(
            PlanDiagnostic(
                f'{path}.prediction.id',
                'manifest.unknown_adapter',
                f'Model adapter {adapter_id!r} is not registered.',
            )
        )
        return None
    _validate_adapter(adapter, function_id, function, context)
    return AtomicCurve(function_id, AdapterPrediction(adapter_id))


def _resolve_fixed_output(
    function_id: str,
    function: Mapping[str, object],
    prediction: Mapping[str, object],
    context: _CandidateContext,
) -> AtomicCurve | None:
    name = _string(prediction['name'])
    output = _binding_by_name(function['outputs'], name)
    if output is None:
        context.resolution.diagnostics.append(
            PlanDiagnostic(
                f'{context.path}.prediction.name',
                'manifest.unknown_output',
                f'Function {function_id!r} has no output {name!r}.',
            )
        )
        return None
    _validate_output_measurement(
        output, context.target, f'{context.path}.target', 'prediction', context.resolution
    )
    measurement = _mapping(output['measurement'])
    conditions = tuple(_mapping(item) for item in _sequence(measurement['conditions']))
    valid = (
        len(conditions) == 1
        and conditions[0].get('quantity') == 'matric_potential'
        and conditions[0].get('convention') == 'magnitude'
        and context.axis.quantity == 'matric_potential'
        and context.axis.convention == 'magnitude'
        and isinstance(conditions[0].get('unit'), str)
        and _units_compatible(
            _string(conditions[0]['unit']), context.axis.unit, context.resolution.index
        )
        and isinstance(conditions[0].get('value'), (int, float))
        and not isinstance(conditions[0].get('value'), bool)
        and math.isfinite(_number(conditions[0]['value']))
        and _number(conditions[0]['value']) >= 0
    )
    if not valid:
        context.resolution.diagnostics.append(
            PlanDiagnostic(
                f'{context.path}.prediction',
                'point.unsupported_conditions',
                'A fixed output requires one finite nonnegative suction-magnitude condition.',
            )
        )
        return None
    return AtomicCurve(
        function_id,
        FixedPointPrediction(
            name,
            _number(conditions[0]['value']),
            _string(conditions[0]['unit']),
            cast('str | None', measurement['method']),
        ),
    )


def _validate_adapter(
    adapter: ModelAdapterSpec,
    function_id: str,
    function: Mapping[str, object],
    context: _CandidateContext,
) -> None:
    path = context.path
    resolution = context.resolution
    diagnostics = resolution.diagnostics
    models = _mapping(function['models'])
    if models.get(adapter.model_kind) is None:
        diagnostics.append(
            PlanDiagnostic(
                f'{path}.prediction.id',
                'adapter.model_unavailable',
                f'Function {function_id!r} does not declare model {adapter.model_kind!r}.',
            )
        )
    if (
        context.axis.quantity != adapter.axis_quantity
        or context.axis.convention != adapter.axis_convention
    ):
        diagnostics.append(
            PlanDiagnostic(
                f'{path}.axis',
                'adapter.axis_mismatch',
                f'Axis does not match model adapter {adapter.id!r}.',
            )
        )
    elif not _units_compatible(context.axis.unit, adapter.axis_unit, resolution.index):
        diagnostics.append(
            PlanDiagnostic(
                f'{path}.axis.unit',
                'adapter.axis_unit_mismatch',
                f'Axis unit is not convertible to the unit required by adapter {adapter.id!r}.',
            )
        )

    expected_target = TargetSpec(
        adapter.target_quantity,
        adapter.target_unit,
        adapter.target_material_basis,
        adapter.target_denominator_basis,
    )
    _compare_targets(context.target, expected_target, f'{path}.target', resolution)

    for parameter in adapter.parameters:
        output = _binding_by_name(function['outputs'], parameter.output)
        parameter_path = f'{path}.prediction.id'
        if output is None:
            diagnostics.append(
                PlanDiagnostic(
                    parameter_path,
                    'adapter.parameter_missing',
                    f'Function {function_id!r} has no adapter parameter output '
                    f'{parameter.output!r}.',
                )
            )
            continue
        expected = TargetSpec(
            parameter.quantity,
            parameter.unit,
            parameter.material_basis,
            parameter.denominator_basis,
        )
        _validate_output_measurement(
            output,
            expected,
            parameter_path,
            'model_parameter',
            resolution,
        )


def _validate_output_measurement(
    output: Mapping[str, object],
    expected: TargetSpec,
    path: str,
    expected_role: str,
    resolution: _ResolutionContext,
) -> None:
    measurement = _mapping(output['measurement'])
    actual = TargetSpec(
        quantity=_string(measurement['quantity']),
        unit=_string(measurement['unit']),
        material_basis=_string(_mapping(measurement['basis'])['material']),
        denominator_basis=_string(_mapping(measurement['basis'])['denominator']),
    )
    _compare_targets(expected, actual, path, resolution)
    if measurement['role'] != expected_role:
        resolution.diagnostics.append(
            PlanDiagnostic(
                path,
                'measurement.role_mismatch',
                f'Output role is {measurement["role"]!r}, expected {expected_role!r}.',
            )
        )


def _compare_targets(
    selected: TargetSpec,
    required: TargetSpec,
    path: str,
    resolution: _ResolutionContext,
) -> None:
    if selected.quantity != required.quantity:
        resolution.diagnostics.append(
            PlanDiagnostic(
                f'{path}.quantity',
                'measurement.quantity_mismatch',
                f'Quantity {selected.quantity!r} does not match {required.quantity!r}.',
            )
        )
    elif not _units_compatible(selected.unit, required.unit, resolution.index):
        resolution.diagnostics.append(
            PlanDiagnostic(
                f'{path}.unit',
                'measurement.unit_mismatch',
                f'Units {selected.unit!r} and {required.unit!r} are not convertible.',
            )
        )
    if (
        selected.material_basis != required.material_basis
        or selected.denominator_basis != required.denominator_basis
    ):
        resolution.diagnostics.append(
            PlanDiagnostic(
                path,
                'measurement.basis_mismatch',
                'Material and denominator bases must match explicitly.',
            )
        )


def _axis_inputs(
    function: Mapping[str, object],
    axis: AxisSpec,
    index: _ManifestIndex,
) -> tuple[Mapping[str, object], ...]:
    matches: list[Mapping[str, object]] = []
    for value in _sequence(function['inputs']):
        binding = _mapping(value)
        if binding['kind'] != 'numeric':
            continue
        measurement = _mapping(binding['measurement'])
        if measurement['quantity'] == axis.quantity and _units_compatible(
            _string(measurement['unit']), axis.unit, index
        ):
            matches.append(binding)
    return tuple(matches)


def _validate_quantity_unit(
    quantity: str,
    unit: str,
    index: _ManifestIndex,
    path: str,
    diagnostics: list[PlanDiagnostic],
) -> None:
    definition = index.quantities.get(quantity)
    if definition is None:
        diagnostics.append(
            PlanDiagnostic(
                f'{path}.quantity',
                'measurement.unknown_quantity',
                f'Quantity {quantity!r} is absent from the installed manifest.',
            )
        )
        return
    allowed = tuple(_string(value) for value in _sequence(definition['units']))
    if unit not in allowed:
        diagnostics.append(
            PlanDiagnostic(
                f'{path}.unit',
                'measurement.invalid_unit',
                f'Unit {unit!r} is not registered for quantity {quantity!r}.',
            )
        )


def _units_compatible(left: str, right: str, index: _ManifestIndex) -> bool:
    if left == right:
        return True
    left_definition = index.units.get(left)
    right_definition = index.units.get(right)
    if left_definition is None or right_definition is None:
        return False
    left_conversion = left_definition.get('conversion')
    right_conversion = right_definition.get('conversion')
    if not isinstance(left_conversion, Mapping) or not isinstance(right_conversion, Mapping):
        return False
    return left_conversion.get('dimension') == right_conversion.get('dimension')


def _validate_overlap_routing(
    members: Sequence[CompositeMember],
    transitions: Sequence[Transition],
    path: str,
    diagnostics: list[PlanDiagnostic],
) -> None:
    transition_pairs = {
        frozenset((transition.left_member, transition.right_member)) for transition in transitions
    }
    for left, right in combinations(members, 2):
        if _intervals_overlap((left.interval, right.interval)):
            pair = frozenset((left.id, right.id))
            if pair not in transition_pairs:
                diagnostics.append(
                    PlanDiagnostic(
                        f'{path}.transitions',
                        'composite.missing_transition',
                        f'Overlapping members {left.id!r} and {right.id!r} need one transition.',
                    )
                )
    for group in combinations(members, 3):
        if _intervals_overlap(tuple(member.interval for member in group)):
            identifiers = tuple(member.id for member in group)
            diagnostics.append(
                PlanDiagnostic(
                    f'{path}.transitions',
                    'composite.triple_overlap',
                    f'Three-way overlap is unsupported for members {identifiers}.',
                )
            )


def _intervals_overlap(intervals: Sequence[Interval]) -> bool:
    lower = max(interval.lower for interval in intervals)
    upper = min(interval.upper for interval in intervals)
    if lower < upper:
        return True
    return lower == upper and all(interval.contains(lower) for interval in intervals)


def _parse_transitions(
    value: object,
    path: str,
    diagnostics: list[PlanDiagnostic],
) -> tuple[Transition, ...] | None:
    transitions: list[Transition] = []
    for position, item in enumerate(_sequence(value)):
        document = _mapping(item)
        transition_path = f'{path}.transitions[{position}]'
        try:
            if document['kind'] == 'hard_switch':
                transitions.append(
                    HardSwitchTransition(
                        left_member=_string(document['left_member']),
                        right_member=_string(document['right_member']),
                        at=_number(document['at']),
                        boundary_member=cast(
                            'BoundaryMember', _string(document['boundary_member'])
                        ),
                    )
                )
            else:
                interval = _parse_interval(
                    document['interval'], f'{transition_path}.interval', diagnostics
                )
                if interval is None:
                    continue
                transitions.append(
                    BlendTransition(
                        left_member=_string(document['left_member']),
                        right_member=_string(document['right_member']),
                        interval=interval,
                        weighting=cast('BlendWeighting', _string(document['weighting'])),
                    )
                )
        except ValueError as error:
            diagnostics.append(
                PlanDiagnostic(
                    transition_path,
                    'composite.invalid_transition',
                    str(error),
                )
            )
    return tuple(transitions)


def _parse_interval(
    value: object,
    path: str,
    diagnostics: list[PlanDiagnostic],
) -> Interval | None:
    document = _mapping(value)
    lower = _mapping(document['lower'])
    upper = _mapping(document['upper'])
    try:
        return Interval(
            lower=_number(lower['value']),
            upper=_number(upper['value']),
            lower_inclusive=_boolean(lower['inclusive']),
            upper_inclusive=_boolean(upper['inclusive']),
        )
    except ValueError as error:
        diagnostics.append(PlanDiagnostic(path, 'composite.invalid_interval', str(error)))
        return None


def _parse_axis(document: Mapping[str, object]) -> AxisSpec:
    return AxisSpec(
        quantity=_string(document['quantity']),
        unit=_string(document['unit']),
        convention=cast('AxisConvention', _string(document['convention'])),
        transform=cast('AxisTransform', _string(document['transform'])),
    )


def _parse_target(document: Mapping[str, object]) -> TargetSpec:
    return TargetSpec(
        quantity=_string(document['quantity']),
        unit=_string(document['unit']),
        material_basis=_string(document['material_basis']),
        denominator_basis=_string(document['denominator_basis']),
    )


def _binding_by_name(value: object, name: str) -> Mapping[str, object] | None:
    for item in _sequence(value):
        binding = _mapping(item)
        if binding.get('name') == name:
            return binding
    return None


def _index_manifest(
    manifest: Mapping[str, object],
    diagnostics: list[PlanDiagnostic],
) -> _ManifestIndex | None:
    schema_version = manifest.get('schema_version')
    functions = manifest.get('functions')
    quantities = manifest.get('quantities')
    units = manifest.get('units')
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        diagnostics.append(
            PlanDiagnostic(
                '$manifest.schema_version', 'manifest.invalid', 'Missing integer schema version.'
            )
        )
    if not _is_sequence(functions):
        diagnostics.append(
            PlanDiagnostic('$manifest.functions', 'manifest.invalid', 'Missing function list.')
        )
    if not isinstance(quantities, Mapping):
        diagnostics.append(
            PlanDiagnostic('$manifest.quantities', 'manifest.invalid', 'Missing quantity registry.')
        )
    if not isinstance(units, Mapping):
        diagnostics.append(
            PlanDiagnostic('$manifest.units', 'manifest.invalid', 'Missing unit registry.')
        )
    if diagnostics:
        return None

    indexed_functions: dict[str, Mapping[str, object]] = {}
    for item in _sequence(functions):
        function = _mapping(item)
        function_id = _string(function['id'])
        if function_id in indexed_functions:
            diagnostics.append(
                PlanDiagnostic(
                    '$manifest.functions',
                    'manifest.duplicate_function',
                    f'Function id {function_id!r} occurs more than once.',
                )
            )
        indexed_functions[function_id] = function
    if diagnostics:
        return None
    return _ManifestIndex(
        schema_version=cast('int', schema_version),
        functions=MappingProxyType(indexed_functions),
        quantities=MappingProxyType(
            {
                str(key): _mapping(value)
                for key, value in cast('Mapping[object, object]', quantities).items()
            }
        ),
        units=MappingProxyType(
            {
                str(key): _mapping(value)
                for key, value in cast('Mapping[object, object]', units).items()
            }
        ),
    )


def _load_document(source: str | Path | Mapping[str, object]) -> JsonValue:
    if isinstance(source, Mapping):
        return _to_json(source)
    path = Path(source)
    try:
        text = path.read_text(encoding='utf-8')
    except OSError as error:
        message = f'Cannot read evaluation plan {path}: {error}'
        raise PlanLoadError(message) from error
    try:
        suffix = path.suffix.lower()
        if suffix == '.json':
            loaded: object = json.loads(text)
        elif suffix in ('.yaml', '.yml'):
            loaded = yaml.safe_load(text)
        else:
            message = f'Unsupported evaluation-plan extension {suffix!r}; use JSON or YAML.'
            raise PlanLoadError(message)
    except (json.JSONDecodeError, yaml.YAMLError) as error:
        message = f'Cannot parse evaluation plan {path}: {error}'
        raise PlanLoadError(message) from error
    return _to_json(loaded)


def _to_json(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        result: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                message = 'Evaluation-plan object keys must be strings.'
                raise PlanLoadError(message)
            result[key] = _to_json(item)
        return result
    if _is_sequence(value):
        return [_to_json(item) for item in value]
    message = f'Unsupported evaluation-plan value type: {type(value).__name__}.'
    raise PlanLoadError(message)


@cache
def _schema() -> Mapping[str, object]:
    resource = files('ptfkit_eval').joinpath('schemas/evaluation-plan.schema.json')
    loaded: object = json.loads(resource.read_text(encoding='utf-8'))
    return _mapping(_to_json(loaded))


def _schema_diagnostics(document: JsonValue) -> list[PlanDiagnostic]:
    validator = Draft202012Validator(_schema())
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    return [
        PlanDiagnostic(
            _json_path(tuple(error.absolute_path)),
            f'schema.{error.validator}',
            error.message,
        )
        for error in errors
    ]


def _json_path(parts: Sequence[object]) -> str:
    path = '$'
    for part in parts:
        path += f'[{part}]' if isinstance(part, int) else f'.{part}'
    return path


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        message = f'Expected an object after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return cast('Mapping[str, object]', value)


def _sequence(value: object) -> Sequence[object]:
    if not _is_sequence(value):
        message = f'Expected an array after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return value


def _is_sequence(value: object) -> TypeGuard[Sequence[object]]:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _string(value: object) -> str:
    if not isinstance(value, str):
        message = f'Expected a string after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return value


def _integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        message = f'Expected an integer after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return value


def _number(value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        message = f'Expected a number after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return float(value)


def _boolean(value: object) -> bool:
    if not isinstance(value, bool):
        message = f'Expected a Boolean after schema validation, got {type(value).__name__}.'
        raise TypeError(message)
    return value
