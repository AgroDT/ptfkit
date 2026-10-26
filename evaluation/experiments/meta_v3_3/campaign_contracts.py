"""Versioned exploratory adapters for physically explicit source-specification outputs."""

# ruff: noqa: INP001, RUF001 - Source descriptions include Unicode pressure signs.

from __future__ import annotations

import importlib
import math
import re
from typing import TYPE_CHECKING

import yaml
from ptfkit_eval import evaluate_candidate, load_evaluation_plan
from ptfkit_eval.adapters import validate_function_inputs
from ptfkit_eval.execution import convert_value


if TYPE_CHECKING:
    from pathlib import Path


WATER = {'volumetric_water_content', 'gravimetric_water_content'}
_PRESSURE = re.compile(
    r'(?<![\w.])[-−]?(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*kPa\b', re.IGNORECASE
)
_UNITS = {
    '%': 'mass_percent',
    '% mass': 'mass_percent',
    'g/g': 'mass_fraction',
    'g/cm^3': 'gram_per_cubic_centimeter',
    'g/cm3': 'gram_per_cubic_centimeter',
    'Mg/m^3': 'gram_per_cubic_centimeter',
    'cm': 'centimeter',
    'kPa': 'kilopascal',
    'cm^3/cm^3': 'volume_fraction',
    'm^3/m^3': 'volume_fraction',
    'fraction': 'mass_fraction',
    'dimensionless': 'dimensionless',
}


def load_catalog(root: Path) -> list[dict]:  # noqa: C901 - Resolve a complete reference graph.
    """Resolve local references and retain the exact prose and native public API binding."""
    specs = (root / 'specs').resolve()
    documents = {}

    def read(path: Path) -> dict:
        path = path.resolve()
        if not path.is_relative_to(specs):
            message = 'Exploratory source references must remain within specs.'
            raise ValueError(message)
        if path not in documents:
            documents[path] = yaml.safe_load(path.read_bytes())
        return documents[path]

    def resolve(node: dict, path: Path, trail: tuple = ()) -> dict:
        if '$ref' not in node:
            return dict(node)
        reference = node['$ref']
        identity = (str(path), reference)
        if identity in trail:
            message = 'Cyclic exploratory source reference.'
            raise ValueError(message)
        filename, _, fragment = reference.partition('#')
        target_path = (path.parent / filename).resolve() if filename else path
        target = read(target_path)
        for part in fragment.lstrip('/').split('/') if fragment else []:
            target = target[part.replace('~1', '/').replace('~0', '~')]
        return {
            **resolve(target, target_path, (*trail, identity)),
            '_ref_module': target_path.stem,
            '_ref_type': fragment.rsplit('/', 1)[-1],
            **{key: value for key, value in node.items() if key != '$ref'},
        }

    result = []
    for path in sorted((specs / 'functions').glob('*.yaml')):
        document = read(path)
        for function in document['functions']:
            if function['status'] != 'implemented':
                continue
            outputs = resolve(function['outputs'], path)
            fields = (
                [resolve(f, path) for f in outputs['fields']]
                if outputs['type'] == 'record'
                else [outputs]
            )
            result.append(
                {
                    **function,
                    'id': function['name'],
                    'source': path.stem,
                    'inputs': [resolve(i, path) for i in function['inputs']],
                    'fields': fields,
                    'scalar_output': outputs['type'] != 'record',
                    'source_notes': document.get('scientific_notes', ''),
                    'specification': path.relative_to(root).as_posix(),
                }
            )
    return sorted(result, key=lambda item: item['id'])


def canonical_input_unit(binding: dict) -> str | None:
    measurement = binding.get('measurement')
    return measurement['unit'] if measurement else _UNITS.get(binding.get('unit'))


def explicit_pressure(description: str) -> float | None:
    """Require a single explicitly stated kPa coordinate; never infer FC/PWP by name."""
    if re.search(r'\d\s*(?:[-−–]|,\s+|\s+(?:and|or|to)\s+)[-−]?\d', description):
        return None
    values = {float(value.replace(',', '')) for value in _PRESSURE.findall(description)}
    return next(iter(values)) if len(values) == 1 else None


def unknown_water_basis(function: dict) -> bool:
    text = ' '.join(function.get('documentation', {}).get('warnings', []))
    return bool(re.search(r'whether.+gravimetric.+volumetric', text, re.IGNORECASE))


def targets(function: dict, public_support: dict) -> list[dict]:  # noqa: C901, PLR0912 - Distinct physical adapters.
    """Recognize structured/prose fixed points, direct density and explicit scalar water axes."""
    result = []
    for field in function['fields']:
        quantity = field.get('quantity')
        if quantity not in WATER | {'dry_bulk_density'}:
            continue
        if quantity in WATER and unknown_water_basis(function):
            continue
        if quantity in WATER and any(
            word in field.get('description', '').lower()
            for word in ('difference', ' minus ', 'available water', 'available moisture')
        ):
            continue
        measurement = field.get('measurement')
        conditions = measurement.get('conditions', []) if measurement else []
        pressure = None
        if (
            len(conditions) == 1
            and conditions[0]['quantity'] == 'matric_potential'
            and conditions[0]['convention'] == 'magnitude'
        ):
            pressure = convert_value(conditions[0]['value'], conditions[0]['unit'], 'kilopascal')
        elif not measurement:
            pressure = explicit_pressure(field.get('description', ''))
            description = field.get('description', '').lower()
            if pressure is None and (
                'at saturation' in description or bool(re.search(r'\bsaturated\b', description))
            ):
                pressure = 0.0
        if quantity == 'dry_bulk_density':
            result.append(
                {
                    'kind': 'direct_property',
                    'quantity': quantity,
                    'field': field['name'],
                    'unit': field['unit'],
                    'adapter': 'native_direct_property_v1',
                }
            )
        elif pressure is not None:
            if (
                field['name'] in {i['name'] for i in function['inputs']}
                and 'input' in field.get('description', '').lower()
            ):
                continue  # Copied water anchors are diagnostics, not predictive comparisons.
            result.append(
                {
                    'kind': 'fixed_pressure',
                    'quantity': quantity,
                    'pressure_kpa': pressure,
                    'field': field['name'],
                    'unit': field['unit'],
                    'adapter': 'native_spec_fixed_pressure_v1',
                }
            )
    if any(field.get('quantity') in WATER for field in function['fields']):
        axis = [
            i
            for i in function['inputs']
            if canonical_input_unit(i) in ('kilopascal', 'centimeter', 'centimeter_water_head')
            and any(word in i.get('description', '').lower() for word in ('tension', 'pressure'))
        ]
        axis_fields = [
            f
            for f in function['fields']
            if f.get('quantity') in WATER
            and (
                function['scalar_output']
                or any(
                    word in f.get('description', '').lower()
                    for word in ('pressure', 'head', 'tension')
                )
            )
        ]
        if len(axis) == 1 and len(axis_fields) == 1:
            field = axis_fields[0]
            axis_unit = canonical_input_unit(axis[0])
            result.extend(
                {
                    'kind': 'fixed_pressure',
                    'quantity': field['quantity'],
                    'pressure_kpa': p,
                    'field': field['name'],
                    'unit': field['unit'],
                    'axis_input': axis[0]['name'],
                    'axis_unit': 'centimeter_water_head'
                    if axis_unit == 'centimeter'
                    else axis_unit,
                    'adapter': 'native_scalar_water_axis_v1',
                }
                for p in (10, 33, 100, 500, 1500)
            )
    available = public_support.get(function['id'], {}).get('curves', [])
    if len(available) == 1:
        curve = available[0]
        result.extend(
            {
                'kind': 'fixed_pressure',
                'quantity': curve['target']['quantity'],
                'pressure_kpa': p,
                'adapter': 'existing_model_adapter_v1',
                'curve': curve,
            }
            for p in (10, 33, 100, 500, 1500)
            if not any(r.get('pressure_kpa') == p for r in result)
        )
    fields = {f['quantity']: f for f in function['fields'] if 'quantity' in f}
    if {'hutson_cass_b', 'matric_potential', 'volumetric_water_content'} <= fields.keys():
        result.extend(
            {
                'kind': 'fixed_pressure',
                'quantity': 'volumetric_water_content',
                'pressure_kpa': p,
                'adapter': 'hutson_cass_dry_v1',
            }
            for p in (10, 33, 100, 500, 1500)
        )
    if {'varallyai_m', 'varallyai_pf_star', 'volumetric_water_content'} <= fields.keys():
        result.extend(
            {
                'kind': 'fixed_pressure',
                'quantity': 'volumetric_water_content',
                'pressure_kpa': p,
                'adapter': 'logistic_pressure_scale_v1',
            }
            for p in (10, 33, 100, 500, 1500)
        )
    unique = {
        (r['quantity'], r.get('pressure_kpa'), r['adapter'], r.get('field')): r for r in result
    }
    return sorted(
        unique.values(), key=lambda r: (r['quantity'], r.get('pressure_kpa', -1), r['adapter'])
    )


def pool_id(target: dict) -> str:
    return (
        f'{target["quantity"]}:{target["pressure_kpa"]:g}kPa'
        if 'pressure_kpa' in target
        else target['quantity']
    )


def _enum(binding: dict, value: object) -> object:
    module = importlib.import_module('ptfkit.' + binding['_ref_module'])
    enum = getattr(module, binding['_ref_type'])
    label = str(value).replace('_', ' ').casefold()
    matches = [
        member
        for member in enum
        if member.name.replace('_', ' ').casefold() == label
        or str(member.value).replace('_', ' ').casefold() == label
    ]
    if len(matches) != 1:
        message = 'Categorical predictor does not match the source enum.'
        raise ValueError(message)
    return matches[0]


def native_outputs(function: dict, values: dict, target: dict) -> dict:
    """Use the source-declared public wrapper, including public aliases and typed enums."""
    inputs = dict(values)
    if 'axis_input' in target:
        inputs[target['axis_input']] = convert_value(
            target['pressure_kpa'], 'kilopascal', target.get('axis_unit', 'kilopascal')
        )
    validate_function_inputs(function, inputs)
    for binding in function['inputs']:
        if binding.get('type') == 'enum':
            inputs[binding['name']] = _enum(binding, inputs[binding['name']])
    module = importlib.import_module('ptfkit.' + function['source'])
    call = getattr(module, function.get('public_api', {}).get('name', function['id']))
    result = call(**inputs)
    return (
        {function['fields'][0]['name']: float(result)}
        if function['scalar_output']
        else {field['name']: float(getattr(result, field['name'])) for field in function['fields']}
    )


def predicted(function: dict, target: dict, values: dict, manifest: dict) -> float:
    """Translate a defined native output to canonical target units without changing formulas."""
    if target['adapter'] == 'existing_model_adapter_v1':
        plan = load_evaluation_plan(
            {
                'schema_version': 1,
                'ptfkit_manifest_schema_version': 1,
                'candidates': [target['curve']],
            },
            manifest=manifest,
        )
        return (
            evaluate_candidate(
                plan.candidates[0], [target['pressure_kpa']], values, manifest=manifest
            )
            .points[0]
            .value
        )
    output = native_outputs(function, values, target)
    if 'field' in target:
        unit = (
            'gram_per_cubic_centimeter'
            if target['quantity'] == 'dry_bulk_density'
            else (
                'mass_fraction'
                if target['quantity'] == 'gravimetric_water_content'
                else 'volume_fraction'
            )
        )
        return convert_value(output[target['field']], target['unit'], unit, manifest=manifest)
    fields = {field['quantity']: field for field in function['fields']}
    saturation = convert_value(
        output[fields['volumetric_water_content']['name']],
        fields['volumetric_water_content']['unit'],
        'volume_fraction',
        manifest=manifest,
    )
    head = convert_value(
        target['pressure_kpa'], 'kilopascal', 'centimeter_water_head', manifest=manifest
    )
    if target['adapter'] == 'hutson_cass_dry_v1':
        a = output[fields['matric_potential']['name']]
        b = output[fields['hutson_cass_b']['name']]
        if min(a, b, saturation) <= 0 or saturation > 1:
            message = 'Invalid modified Brooks-Corey parameters.'
            raise ValueError(message)
        inflection = a * (2 * b / (1 + 2 * b)) ** (-b)
        if head < inflection:
            message = 'No wet-branch adapter is registered for this modified Brooks-Corey family.'
            raise ValueError(message)
        return saturation * (head / a) ** (-1 / b)
    m = output[fields['varallyai_m']['name']]
    pf = output[fields['varallyai_pf_star']['name']]
    if not 0 < saturation <= 1 or m <= 0:
        message = 'Invalid logistic water-retention parameters.'
        raise ValueError(message)
    exponent = m * (math.log(head) - pf * math.log(10))
    return saturation * (
        math.exp(-exponent) / (1 + math.exp(-exponent))
        if exponent >= 0
        else 1 / (1 + math.exp(exponent))
    )
