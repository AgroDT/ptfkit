"""Catalog-wide exploratory predictors from explicit same-sample evidence."""

# ruff: noqa: INP001, RUF001 - Source intervals contain Unicode dashes.

from __future__ import annotations

import math
import re
from functools import cache

from ptfkit_eval.eligibility import assess_computational_domain
from ptfkit_eval.execution import convert_value
from ptfkit_eval.harmonization import EvidenceTier, EvidenceValue, _usda_class, psd_fraction

from evaluation.experiments.meta_v3_3 import exploratory_inputs as previous
from evaluation.experiments.meta_v3_3.campaign_contracts import (
    canonical_input_unit,
)
from evaluation.experiments.meta_v3_3.source_domains import within_named_domain


_TEXTURE = ('sand', 'silt', 'clay')
_CARBON = {'carbon', 'organic_carbon', 'soil_organic_carbon', 'soc'}
_MATTER = {'organic_matter', 'soil_organic_matter'}
_CLASS_MATCH_TOLERANCE = 0.5
_PERCENT = 100


def evidence(
    value: float | str, policy: str, parents: tuple[EvidenceValue, ...], **details: object
) -> EvidenceValue:
    return EvidenceValue(
        value,
        EvidenceTier.APPROXIMATE,
        policy,
        tuple(sorted({s for p in parents for s in p.sources})),
        tuple(details.items()),
        parents,
    )


def reported_class(sample: dict) -> EvidenceValue | None:
    matches = [
        f
        for f in sample['features']
        if f.get('kind') == 'categorical'
        and f.get('review_status') == 'confirmed'
        and f.get('origin') == 'measured'
        and f.get('category_system', '').endswith('.UsdaTextureClass')
    ]
    if len(matches) != 1:
        return None
    feature = matches[0]
    return EvidenceValue(
        feature['value'],
        EvidenceTier.STRICT,
        'reviewed_usda_class_v1',
        tuple(feature['source_cells']),
    )


@cache
def _lattice() -> tuple[tuple[str, tuple[int, int, int]], ...]:
    return tuple(
        (_usda_class(sand, silt, 100 - sand - silt), (sand, silt, 100 - sand - silt))
        for sand in range(101)
        for silt in range(101 - sand)
    )


def class_psd(sample: dict, known: dict[str, EvidenceValue]) -> dict[str, EvidenceValue]:
    """Impute only missing fractions using a uniform 1%-lattice inside the reported USDA class.

    Available fractions remain unchanged. The distribution within a class is
    assumed, never measured, and no Russian-to-USDA label crosswalk is invented.
    """
    texture = reported_class(sample)
    if texture is None or len(known) == len(_TEXTURE):
        return known
    points = [
        point
        for label, point in _lattice()
        if label == texture.value
        and all(
            abs(point[_TEXTURE.index(name)] - previous.numeric(value)) <= _CLASS_MATCH_TOLERANCE
            for name, value in known.items()
        )
    ]
    if not points:
        return known
    missing = [name for name in _TEXTURE if name not in known]
    means = {
        name: math.fsum(p[_TEXTURE.index(name)] for p in points) / len(points) for name in missing
    }
    remainder = 100 - math.fsum(previous.numeric(value) for value in known.values())
    scale = math.fsum(means.values())
    if scale <= 0 or remainder < 0:
        return known
    result = dict(known)
    parents = (texture, *known.values())
    for name in missing:
        result[name] = evidence(
            means[name] * remainder / scale,
            'usda_class_conditional_psd_v1',
            parents,
            grid_step_percent=1,
            matching_tolerance_percent=0.5,
            lattice_point_count=len(points),
            imputed_component=name,
            formula='conditional class lattice mean, rescaled over missing fractions only',
        )
    if _usda_class(*(previous.numeric(result[name]) for name in _TEXTURE)) != texture.value:
        return known
    return result


def interval(binding: dict) -> tuple[float, float] | None:
    measurement = binding.get('measurement')
    particle = measurement.get('particle_size') if measurement else None
    if particle:
        return (
            float(particle['lower']['value']) if particle.get('lower') else 0.0,
            float(particle['upper']['value']) if particle.get('upper') else 2000.0,
        )
    description = binding.get('description', '').replace('−', '-').replace('–', '-')
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(mm|[µμ]m)', description)
    if match:
        factor = 1000 if match[3] == 'mm' else 1
        bounds = (float(match[1]) * factor, float(match[2]) * factor)
        return min(bounds), max(bounds)
    match = re.search(
        r'(?:below|smaller than|<)\s*(\d+(?:\.\d+)?)\s*(mm|[µμ]m|micrometres|micrometers)',
        description,
    )
    if match:
        return 0.0, float(match[1]) * (1000 if match[2] == 'mm' else 1)
    return {'sand': (50.0, 2000.0), 'silt': (2.0, 50.0), 'clay': (0.0, 2.0)}.get(binding['name'])


def texture_input(binding: dict, texture: dict[str, EvidenceValue]) -> EvidenceValue | None:
    boundaries = interval(binding)
    if boundaries is None:
        return None
    standard = {(50, 2000): 'sand', (2, 50): 'silt', (0, 2): 'clay'}
    component = standard.get(boundaries)
    if component in texture:
        return texture[component]
    if len(texture) != len(_TEXTURE):
        return None
    clay, silt = texture['clay'], texture['silt']
    parents = tuple(texture.values())
    cdf = [
        (0, evidence(0, 'closed_psd_cdf_v1', parents)),
        (2, clay),
        (
            50,
            evidence(previous.numeric(clay) + previous.numeric(silt), 'closed_psd_cdf_v1', parents),
        ),
        (2000, evidence(100, 'closed_psd_cdf_v1', parents)),
    ]
    return psd_fraction(cdf, *boundaries, basis='dry_mass_fine_earth', allow_approximate=True)


def density(row: dict, registration: dict) -> EvidenceValue | None:
    if 'Q' in row.get('formulas', {}):
        return None  # A cached mean or undocumented density derivation is not a reported density.
    return row.get('linked_density') or previous.density(row, registration)


def legacy_domain(value: float, binding: dict) -> bool:
    if binding.get('measurement'):
        return assess_computational_domain(value, binding['measurement']).within
    text = binding.get('domain') or ''
    number = r'(-?\d+(?:\.\d+)?)'
    operations = {
        '<': lambda a, b: a < b,
        '<=': lambda a, b: a <= b,
        '>': lambda a, b: a > b,
        '>=': lambda a, b: a >= b,
    }
    return all(
        operations[op](float(bound), value)
        for bound, op in re.findall(number + r'\s*(<=|>=|<|>)\s*value', text)
    ) and all(
        operations[op](value, float(bound))
        for op, bound in re.findall(r'value\s*(<=|>=|<|>)\s*' + number, text)
    )


def resolve_inputs(  # noqa: C901, PLR0912, PLR0915 - Explicit predictor types and rejection branches.
    function: dict,
    sample: dict,
    row: dict | None,
    scenario: str,
    registration: dict,
    *,
    representative: bool,
    water_inputs: dict[str, EvidenceValue],
    organic_conversion: bool = True,
    depth_derivation: bool = True,
    derive_texture_class: bool = True,
    organic_aliases: bool = True,
    axis_inputs: set[str] | None = None,
) -> tuple[dict, dict, list[str]]:
    values, proofs, reasons = {}, {}, []
    texture = previous.texture_predictors(row, scenario, registration) if row else {}
    if representative:
        texture = class_psd(sample, texture)
    for binding in function['inputs']:
        name = binding['name']
        if name in (axis_inputs or set()):
            continue
        unit = canonical_input_unit(binding)
        proof = water_inputs.get(name)
        source_unit = 'mass_percent'
        if proof is not None:
            source_unit = unit
        elif binding.get('type') == 'enum':
            if binding.get('_ref_type') == 'UsdaTextureClass':
                proof = reported_class(sample)
                if proof is None and derive_texture_class and len(texture) == len(_TEXTURE):
                    label = _usda_class(*(previous.numeric(texture[n]) for n in _TEXTURE))
                    proof = evidence(
                        label, 'exploratory_derived_texture_class', tuple(texture.values())
                    )
        elif name in _TEXTURE or name in (
            'fine_sand',
            'coarse_sand',
            'fine_fraction',
            'fine_sand_fraction',
            'clay_content',
            'sand_content',
            'silt_content',
        ):
            proof = texture_input(binding, texture)
        elif name == 'bulk_density' and row:
            proof, source_unit = density(row, registration), 'gram_per_cubic_centimeter'
        elif (
            name in _CARBON | _MATTER
            and row
            and (organic_aliases or name not in ('soc', 'soil_organic_carbon'))
        ):
            component = 'carbon' if name in _CARBON else 'organic_matter'
            column = 'R' if component == 'carbon' else 'S'
            if organic_conversion or (
                previous.raw_number(row, column) is not None
                and column not in row.get('formulas', {})
            ):
                proof = previous.organic(row, component, registration)
                if proof:
                    details = dict(proof.details)
                    proof = evidence(
                        previous.numeric(proof),
                        'catalog_oc_om_v1',
                        (proof,),
                        origin=(
                            'derived'
                            if details['factor'] != 1 or column in row.get('formulas', {})
                            else 'reported'
                        ),
                        source_formula=row.get('formulas', {}).get(column),
                        factor=details['factor'],
                        requested_component=component,
                    )
        elif (
            depth_derivation
            and name in ('mean_depth', 'depth')
            and row
            and row['values'].get('J') is not None
        ):
            raw = str(row['values']['J']).strip()
            match = re.fullmatch(r'(\d+(?:[.,]\d+)?)\s*[-–—]\s*(\d+(?:[.,]\d+)?)', raw)
            if match:
                low, high = (float(s.replace(',', '.')) for s in match.groups())
                if 0 <= low < high:
                    proof = EvidenceValue(
                        (low + high) / 2,
                        EvidenceTier.APPROXIMATE,
                        'depth_interval_midpoint_cm_v1',
                        (f'{row["worksheet"]}!J{row["row"]}',),
                        (
                            ('reported_interval', raw),
                            ('assumed_unit', 'centimeter'),
                            ('formula', '(lower + upper) / 2'),
                        ),
                    )
                    source_unit = 'centimeter'
        elif name in ('porosity', 'total_porosity') and row:
            porosity = previous.raw_number(row, 'U')
            if porosity is not None and 0 < porosity < _PERCENT:
                proof = EvidenceValue(
                    porosity / 100,
                    EvidenceTier.APPROXIMATE,
                    'reported_porosity_percent_v1',
                    (f'{row["worksheet"]}!U{row["row"]}',),
                    (('reported_percent', porosity),),
                )
                source_unit = 'volume_fraction'
        if function['id'] == 'calc_ptf_cosby1984_univariate':
            features = {f['id']: f for f in sample['features']}
            feature = features.get(name)
            if (
                not feature
                or feature.get('derivation', {}).get('method')
                != 'cosby1984_table2_class_midpoint_v1'
            ):
                reasons.append('cosby_requires_reviewed_class_midpoint_coordinates')
                continue
            proof = EvidenceValue(
                feature['value'],
                EvidenceTier.DERIVED,
                feature['derivation']['method'],
                tuple(feature['source_cells']),
            )
        if proof is None:
            reasons.append('missing_predictor:' + name)
            continue
        if binding.get('type') == 'enum':
            value = proof.value
        elif unit is None or source_unit is None:
            reasons.append('unresolved_predictor_unit:' + name)
            continue
        else:
            value = convert_value(previous.numeric(proof), source_unit, unit)
            if not legacy_domain(value, binding):
                reasons.append('computational_domain:' + name)
                continue
        values[name] = value
        proofs[name] = proof.document()
        proofs[name]['native_unit'] = binding.get('unit')
        proofs[name]['canonical_input_unit'] = unit
    for binding in function['inputs']:
        name = binding['name']
        if name in values and not within_named_domain(
            binding.get('domain') or '', {**values, 'value': values[name]}
        ):
            reasons.append('computational_domain:' + name)
    return values, proofs, reasons
