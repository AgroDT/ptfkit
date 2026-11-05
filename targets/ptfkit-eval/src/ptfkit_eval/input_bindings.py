"""Strict manifest-aware bindings for portable canonical dataset features."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from .documents import object_mapping, object_records
from .eligibility import assess_computational_domain
from .execution import convert_value
from .input_derivations import requires_registered_derivation, verify_input_derivation


if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True)
class RunInputTrace:
    """A feature binding, normalized value, and its complete scientific gate."""

    function: str
    input: str
    feature_id: str
    raw_value: object
    value: object
    source_unit: str | None
    target_unit: str | None
    compatibility: str
    reasons: tuple[str, ...]
    source_cells: tuple[str, ...]
    measurement: Mapping[str, object] | None
    reported_applicability: str = 'not_assessed'
    source_file: str | None = None


def bind_retention_inputs(
    function: Mapping[str, object],
    sample: Mapping[str, object],
    bindings: Mapping[str, object],
    *,
    manifest: Mapping[str, object],
) -> tuple[RunInputTrace, ...]:
    """Bind only reviewed exact or unit-convertible measured/synthetic inputs.

    Derived and estimated features remain excluded until a registered derivation
    can be verified. Null manifest methods impose no method restriction; explicit
    methods, physical bases, conditions, and particle boundaries must agree.
    """
    features = {feature['id']: feature for feature in object_records(sample['features'])}
    traces: list[RunInputTrace] = []
    for binding in object_records(function['inputs']):
        name = cast('str', binding['name'])
        if name not in bindings:
            continue  # The run resolver has already accounted for an explicit axis input.
        feature_id = cast('str', bindings[name])
        feature = features.get(feature_id)
        reasons = _feature_reasons(function, binding, feature, features, bindings)
        value: object = None
        source_unit: str | None = None
        target_unit: str | None = None
        compatibility = 'incompatible'
        measurement = (
            object_mapping(feature['measurement']) if feature and 'measurement' in feature else None
        )
        if not reasons and feature is not None:
            if binding['kind'] == 'categorical':
                value, compatibility = _categorical_value(binding, feature, reasons)
            else:
                value, source_unit, target_unit, compatibility = _numeric_value(
                    binding, feature, manifest, reasons
                )
        traces.append(
            RunInputTrace(
                function=cast('str', function['id']),
                input=name,
                feature_id=feature_id,
                raw_value=feature['value'] if feature else None,
                value=value,
                source_unit=source_unit,
                target_unit=target_unit,
                compatibility=compatibility,
                reasons=tuple(reasons),
                source_cells=cast('tuple[str, ...]', feature['source_cells']) if feature else (),
                measurement=measurement,
                source_file=cast('str | None', feature.get('source_file')) if feature else None,
            )
        )
    return tuple(traces)


def _feature_reasons(
    function: Mapping[str, object],
    binding: Mapping[str, object],
    feature: Mapping[str, object] | None,
    features: Mapping[object, Mapping[str, object]],
    bindings: Mapping[str, object],
) -> list[str]:
    if feature is None or feature['value'] is None:
        return ['missing_input']
    if feature['review_status'] != 'confirmed':
        return ['unreviewed_input']
    if feature['origin'] == 'estimated':
        return ['estimated_input_not_allowed']
    if (feature['origin'] == 'derived' or requires_registered_derivation(binding)) and (
        not verify_input_derivation(function, features, bindings)
    ):
        return ['unverified_derivation']
    if feature['kind'] != binding['kind']:
        return ['input_kind_mismatch']
    return []


def _categorical_value(
    binding: Mapping[str, object], feature: Mapping[str, object], reasons: list[str]
) -> tuple[object, str]:
    enum = object_mapping(binding['enum'])
    allowed = {item['name'] for item in object_records(enum['values'])} | {
        item['value'] for item in object_records(enum['values'])
    }
    if feature['category_system'] != enum['id'] or feature['value'] not in allowed:
        reasons.append('unresolved_category')
        return None, 'incompatible'
    return feature['value'], 'exact'


def _numeric_value(
    binding: Mapping[str, object],
    feature: Mapping[str, object],
    manifest: Mapping[str, object],
    reasons: list[str],
) -> tuple[object, str, str, str]:
    expected = object_mapping(binding['measurement'])
    actual = object_mapping(feature['measurement'])
    source_unit = cast('str', actual['unit'])
    target_unit = cast('str', expected['unit'])
    for key, code in (
        ('quantity', 'quantity_mismatch'),
        ('basis', 'basis_mismatch'),
        ('particle_size', 'particle_boundary_mismatch'),
        ('conditions', 'conditions_mismatch'),
    ):
        if actual[key] != expected[key]:
            reasons.append(code)
    if expected['method'] is not None and actual['method'] != expected['method']:
        reasons.append('method_mismatch')
    if reasons:
        return None, source_unit, target_unit, 'incompatible'
    try:
        value = convert_value(
            cast('float', feature['value']), source_unit, target_unit, manifest=manifest
        )
    except ValueError:
        reasons.append('unit_mismatch')
        return None, source_unit, target_unit, 'incompatible'
    if not assess_computational_domain(value, expected).within:
        reasons.append('outside_computational_domain')
        return value, source_unit, target_unit, 'incompatible'
    return (
        value,
        source_unit,
        target_unit,
        'exact' if source_unit == target_unit else 'unit_converted',
    )
