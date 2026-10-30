"""Explicit approximate interpretations of raw META predictors for sensitivity only."""

# ruff: noqa: INP001 - Standalone experiment helpers.

from __future__ import annotations

import math
from bisect import bisect_left
from itertools import pairwise
from typing import TYPE_CHECKING, cast

from ptfkit_eval.eligibility import assess_computational_domain
from ptfkit_eval.execution import convert_value
from ptfkit_eval.harmonization import EvidenceTier, EvidenceValue, usda_texture
from ptfkit_eval.water import within_water_bounds


if TYPE_CHECKING:
    from collections.abc import Sequence


_PERCENT = 100.0
_USDA_CLAY_UM = 2
_TEXTURE_COLUMNS = {'clay': 'N', 'silt': 'O', 'sand': 'P'}


def assumed(
    value: float | str,
    policy: str,
    registration: dict,
    *,
    sources: tuple[str, ...],
    parents: Sequence[EvidenceValue] = (),
    **details: object,
) -> EvidenceValue:
    """Attach the complete registered assumption text to every approximate value."""
    if policy not in registration['policies']:
        message = f'Unregistered exploratory policy: {policy}'
        raise ValueError(message)
    return EvidenceValue(
        value,
        EvidenceTier.APPROXIMATE,
        policy,
        sources,
        (('assumptions', tuple(registration['policies'][policy])), *tuple(details.items())),
        tuple(parents),
    )


def raw_number(row: dict, column: str) -> float | None:
    value = row['values'].get(column)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return None
    return float(value)


def numeric(value: EvidenceValue) -> float:
    if not isinstance(value.value, (int, float)):
        message = 'Exploratory numeric transformations require numeric evidence.'
        raise TypeError(message)
    return float(value.value)


def _cell(row: dict, column: str) -> tuple[str, ...]:
    return (f'{row["worksheet"]}!{column}{row["row"]}',)


def _texture_raw(row: dict, registration: dict) -> dict[str, EvidenceValue]:
    values = {}
    for component, column in _TEXTURE_COLUMNS.items():
        value = raw_number(row, column)
        if value is not None and 0 <= value <= _PERCENT:
            values[component] = assumed(
                value,
                'meta_texture_basis_v1',
                registration,
                sources=_cell(row, column),
                reported_column=column,
                reported_clay_upper_um=row['clay_upper_um'],
                unit='mass_percent',
            )
    return values


def _closure(values: dict[str, EvidenceValue], registration: dict) -> dict[str, EvidenceValue]:
    if len(values) == len(_TEXTURE_COLUMNS) - 1:
        remaining = _PERCENT - math.fsum(numeric(v) for v in values.values())
        if remaining < 0:
            return {}
        missing = next(iter(_TEXTURE_COLUMNS.keys() - values.keys()))
        sources = tuple(sorted({s for value in values.values() for s in value.sources}))
        return {
            **values,
            missing: assumed(
                remaining,
                'meta_texture_closure_v1',
                registration,
                sources=sources,
                parents=tuple(values.values()),
                formula='missing_percent = 100 - other_fractions',
            ),
        }
    if len(values) < len(_TEXTURE_COLUMNS):
        return values
    total = math.fsum(numeric(v) for v in values.values())
    residual = total - _PERCENT
    if total <= 0 or abs(residual) > registration['maximum_texture_closure_residual_percent']:
        return {}
    if total == _PERCENT:
        return values
    sources = tuple(sorted({s for v in values.values() for s in v.sources}))
    return {
        name: assumed(
            numeric(v) * _PERCENT / total,
            'meta_texture_closure_v1',
            registration,
            sources=sources,
            parents=tuple(values.values()),
            closure_residual_percent=residual,
            formula='normalized_percent = raw_percent * 100 / total_percent',
        )
        for name, v in values.items()
    }


def texture_predictors(  # noqa: C901 - Distinct preregistered boundary and closure scenarios.
    row: dict, scenario: str, registration: dict
) -> dict[str, EvidenceValue]:
    """Return independent sand/clay/silt evidence under one preregistered PSD scenario."""
    if scenario not in registration['scenarios']:
        message = 'Unknown exploratory PSD scenario.'
        raise ValueError(message)
    values = _closure(_texture_raw(row, registration), registration)
    if not values:
        return {}
    sources = tuple(sorted({s for v in values.values() for s in v.sources}))
    if scenario == 'reported_boundary_proxy' or row['clay_upper_um'] == _USDA_CLAY_UM:
        result = {
            name: assumed(
                numeric(v),
                'meta_reported_boundary_proxy_v1',
                registration,
                sources=v.sources,
                parents=(v,),
                reported_clay_upper_um=row['clay_upper_um'],
                requested_clay_upper_um=2,
            )
            for name, v in values.items()
        }
    else:
        result = {name: v for name, v in values.items() if name == 'sand'}
        clay = values.get('clay')
        if clay is None:
            return result
        cumulative = [(float(row['clay_upper_um']), numeric(clay))]
        physical_clay = raw_number(row, 'M')
        if physical_clay is not None and 0 <= physical_clay <= _PERCENT:
            residual = dict(clay.details).get('closure_residual_percent', 0)
            physical_clay *= _PERCENT / (_PERCENT + cast('float', residual))
            cumulative.append((10.0, physical_clay))
            sources = (*sources, *_cell(row, 'M'))
        if 'silt' in values:
            cumulative.append((50.0, numeric(clay) + numeric(values['silt'])))
        elif 'sand' in values:
            cumulative.append((50.0, _PERCENT - numeric(values['sand'])))
        if any(a[1] > b[1] for a, b in pairwise(cumulative)):
            return {}
        index = bisect_left([p[0] for p in cumulative], 2)
        if 0 < index < len(cumulative):
            (lower, left), (upper, right) = cumulative[index - 1 : index + 1]
            value = left + (right - left) * math.log10(2 / lower) / math.log10(upper / lower)
            result['clay'] = assumed(
                value,
                'meta_log_psd_boundary_v1',
                registration,
                sources=sources,
                parents=tuple(values.values()),
                neighboring_diameters_um=(lower, upper),
                cumulative_percent=(left, right),
                requested_boundary_um=2,
                formula='CDF linear in log10 diameter',
                physical_clay_reported_percent=raw_number(row, 'M'),
            )
    if len(result) == len(_TEXTURE_COLUMNS) - 1:
        missing = next(iter(_TEXTURE_COLUMNS.keys() - result.keys()))
        remaining = _PERCENT - math.fsum(numeric(v) for v in result.values())
        if remaining >= 0:
            result[missing] = assumed(
                remaining,
                'meta_texture_closure_v1',
                registration,
                sources=tuple(sorted({s for v in result.values() for s in v.sources})),
                parents=tuple(result.values()),
                formula='missing_percent = 100 - other_fractions',
            )
    return result


def density(row: dict, registration: dict) -> EvidenceValue | None:
    value = raw_number(row, 'Q')
    if value is None or value <= 0:
        return None
    return assumed(
        value,
        'meta_density_v1',
        registration,
        sources=_cell(row, 'Q'),
        assumed_unit='gram_per_cubic_centimeter',
    )


def organic(row: dict, component: str, registration: dict) -> EvidenceValue | None:
    column = 'R' if component == 'carbon' else 'S'
    source_column = column
    value = raw_number(row, column)
    factor = 1.0
    if value is None:
        source_column = 'S' if column == 'R' else 'R'
        value = raw_number(row, source_column)
        factor = registration['organic_carbon_to_matter_factor'] ** (-1 if column == 'R' else 1)
    if value is None or value < 0 or not 0 <= value * factor <= _PERCENT:
        return None
    return assumed(
        value * factor,
        'meta_organic_v1',
        registration,
        sources=_cell(row, source_column),
        source_value=value,
        source_column=source_column,
        requested_component=component,
        factor=factor,
        formula='requested_percent = reported_percent * factor',
    )


def approximate_inputs(  # noqa: C901 - Only the requested predictors are interpreted.
    function: dict,
    row: dict,
    scenario: str,
    registration: dict,
    manifest: dict,
    *,
    reviewed_values: dict,
    reviewed_evidence: dict,
) -> tuple[dict, dict, list[str]]:
    """Keep reviewed bindings intact and fill missing inputs with explicit assumptions."""
    values, evidence = dict(reviewed_values), dict(reviewed_evidence)
    reasons = []
    texture = texture_predictors(row, scenario, registration)
    for binding in function['inputs']:
        name = binding['name']
        if name in values:
            continue
        proof = None
        if function['id'] == 'calc_ptf_cosby1984_univariate':
            reasons.append('cosby_requires_reviewed_class_midpoint_coordinates')
            continue
        if name in _TEXTURE_COLUMNS:
            proof = texture.get(name)
        elif name == 'bulk_density':
            proof = density(row, registration)
        elif name in ('organic_carbon', 'carbon'):
            proof = organic(row, 'carbon', registration)
        elif name in ('organic_matter', 'soil_organic_matter'):
            proof = organic(row, 'organic_matter', registration)
        elif name == 'soil_texture' and len(texture) == len(_TEXTURE_COLUMNS):
            proof = usda_texture(
                texture['sand'],
                texture['silt'],
                texture['clay'],
                basis='dry_mass_fine_earth',
                boundaries_um=(2, 50, 2000),
            )
        if proof is None:
            reasons.append(f'missing_or_unsupported_predictor:{name}')
            continue
        measurement = binding.get('measurement')
        if measurement:
            source_unit = 'gram_per_cubic_centimeter' if name == 'bulk_density' else 'mass_percent'
            value = convert_value(
                numeric(proof), source_unit, measurement['unit'], manifest=manifest
            )
            if not assess_computational_domain(value, measurement).within:
                reasons.append(f'outside_computational_domain:{name}')
                continue
            proof = assumed(
                value,
                proof.policy,
                registration,
                sources=proof.sources,
                parents=(proof,),
                source_unit=source_unit,
                target_unit=measurement['unit'],
                required_contract=measurement,
                protocol_comparability='assumed_not_verified',
            )
        values[name], evidence[name] = proof.value, proof.document()
    return values, evidence, reasons


def approximate_target(
    observation: EvidenceValue,
    original: dict,
    required: dict,
    row: dict | None,
    registration: dict,
) -> EvidenceValue | None:
    """Keep the original experimental target as a parent of every basis assumption."""
    result = observation
    if original['quantity'] != required['quantity']:
        bulk = density(row, registration) if row else None
        if bulk is None:
            return None
        volume_to_mass = original['quantity'] == 'volumetric_water_content'
        water_density = registration['water_density_g_cm3']
        value = numeric(observation) * (
            water_density / numeric(bulk) if volume_to_mass else numeric(bulk) / water_density
        )
        result = assumed(
            value,
            'meta_target_density_conversion_v1',
            registration,
            sources=(*observation.sources, *bulk.sources),
            parents=(observation, bulk),
            water_density_g_cm3=water_density,
            original_contract=original,
            required_contract=required,
            formula='mass_ratio = volume_fraction * water_density / bulk_density'
            if volume_to_mass
            else 'volume_fraction = mass_ratio * bulk_density / water_density',
        )
    if original['material_basis'] != required['material_basis']:
        result = assumed(
            numeric(result),
            'meta_target_material_v1',
            registration,
            sources=result.sources,
            parents=(result,),
            original_contract=original,
            required_contract=required,
        )
    if not within_water_bounds(numeric(result), required['quantity']):
        message = 'Density-converted target violates the required water bounds.'
        raise ValueError(message)
    return result
