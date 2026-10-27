"""Explicit E5 WRC routes and within-publication discrete family registration."""

# ruff: noqa: INP001, E501, PLR2004, C901 - Scientific adapter contracts.

from __future__ import annotations

import math
import re
from itertools import pairwise

from evaluation.experiments.meta_v3_3 import campaign_contracts as contracts
from evaluation.experiments.meta_v3_3 import workbook_semantic as semantic
from evaluation.experiments.meta_v3_3.pressure_semantics import coordinates


HEAD_PER_KPA = 1 / 0.0980665
PARAMETER_ADAPTERS = {
    'calc_ptf_vereecken1989_detailed': {
        'formula': 'theta_r + (theta_s-theta_r)/(1+(alpha*h_cm)^n)',
        'parameters': {
            'theta_r': 'volume_fraction',
            'theta_s': 'volume_fraction',
            'alpha': '1/cm',
            'n': '1',
        },
        'required_terms': 'All four terms predicted by this function; m=1 in source specification.',
    },
    'calc_ptf_saxton1986_calcptf_parameters': {
        'formula': 'theta_s if alpha*h_cm<=1 else theta_r+(theta_s-theta_r)*(alpha*h_cm)^(-lambda)',
        'parameters': {
            'theta_r': 'volume_fraction',
            'theta_s': 'volume_fraction',
            'alpha': '1/cm',
            'conductivity_lambda': '1',
        },
        'required_terms': 'All terms predicted; theta_r=0 is explicit in the source parameterization.',
    },
    'calc_ptf_saxton2006_tension_dry': {
        'formula': 'theta_33*(pressure_kpa/33)^(-1/B); B=ln(1500/33)/ln(theta_33/theta_1500)',
        'parameters': {'theta_33': 'volume_fraction', 'theta_1500': 'volume_fraction'},
        'required_terms': 'Anchors predicted by calc_ptf_saxton2006, never taken from measured WRC.',
        'pressure_domain_kpa': [33, 1500],
        'parent_function': 'calc_ptf_saxton2006',
    },
    'calc_ptf_saxton2006_tension_wet': {
        'formula': 'theta_s at p<=air_entry; otherwise theta_33+(33-p)*(theta_s-theta_33)/(33-air_entry)',
        'parameters': {
            'theta_33': 'volume_fraction',
            'theta_s': 'volume_fraction',
            'air_entry_tension': 'kPa',
        },
        'required_terms': 'All anchors predicted by calc_ptf_saxton2006; theta_s=1-normal_density/2.65 per its source.',
        'pressure_domain_kpa': [0, 33],
        'parent_function': 'calc_ptf_saxton2006',
    },
}
UNRESOLVED = {
    **{
        f'calc_ptf_dharumarajan2019_{variant}': 'needs_user_decision: source warnings explicitly leave gravimetric versus volumetric percentages unresolved; the provisional field quantity cannot override that physical ambiguity.'
        for variant in ('nkp', 'nkp_clay', 'skp', 'skp_clay')
    },
    'calc_ptf_li2007': 'needs_user_decision: zero residual is explicit, but the encoded metadata does not identify m=1 versus m=1-1/n.',
    'calc_ptf_wang2022_h2': 'needs_user_decision: alpha/n/m/theta_s alone do not specify the corrected residual-water convention noted in the source metadata.',
    'calc_ptf_wang2022_h3': 'needs_user_decision: alpha/n/m/theta_s alone do not specify the corrected residual-water convention noted in the source metadata.',
    'calc_ptf_weber2020': 'still_missing_predictor: six VGM input parameters are unavailable independently; fitted experimental parameters would leak targets. Full Brunswick noncapillary formula is also absent from the encoded regression metadata.',
    'calc_ptf_williams1992_table5': 'still_missing_predictor: Northcote structure/field-texture group and saturated water term are not supplied; no USDA-to-Northcote crosswalk or assumed saturation.',
}


def native_targets(function: dict, context: dict) -> list[dict]:
    """Find fixed pressures, including signed kPa prose in resolved shared fields."""
    result = [
        t
        for t in semantic.target_list(function, context)
        if t['kind'] == 'fixed_pressure'
        and 'axis_input' not in t
        and 'field' in t
        and t['adapter'].startswith('native_spec')
    ]
    if result:
        return result
    if contracts.unknown_water_basis(function):
        return []
    for field in function['fields']:
        if field.get('quantity') not in contracts.WATER:
            continue
        description = field.get('description', '')
        if any(word in description.lower() for word in ('available', 'difference', 'minus')):
            continue
        pressures = coordinates(description)
        if len(pressures) == 1:
            result.append(
                {
                    'kind': 'fixed_pressure',
                    'quantity': field['quantity'],
                    'pressure_kpa': pressures[0],
                    'field': field['name'],
                    'unit': field['unit'],
                    'adapter': 'native_spec_fixed_pressure_v1',
                }
            )
    return result


def family_variant(function: dict) -> str:
    """Remove pressure coordinates only; preserve equation sets and predictor variants."""
    name = function['id'].removeprefix('calc_ptf_')
    if function['source'] == 'gunarathna2019':
        name = re.sub(r'_vwc(?:1500|33|10)_', '_', name)
    elif function['source'] == 'kalumba2021':
        name = re.sub(r'_pf\d+$', '', name)
    elif function['source'] == 'lal1979':
        name = re.sub(r'_water_\d+bar_', '_', name)
    elif function['source'] == 'rawls2003':
        name = re.sub(r'_theta(?:1500|33)_', '_', name)
    elif function['source'] == 'rawls1982':
        name = re.sub(r'_theta_(?:1500|33)$', '', name)
    elif function['source'] == 'myeni2021':
        name = re.sub(r'_(?:fc|pwp)$', '', name)
    return 'family_' + name + '_WRC'


def registry(catalog: list[dict], eligible: set[str], context: dict) -> dict:
    families = {}
    for function in catalog:
        if function['id'] not in eligible:
            continue
        targets = native_targets(function, context)
        for target in targets:
            key = family_variant(function) + (
                '_mass' if target['quantity'].startswith('gravimetric') else '_volume'
            )
            family = families.setdefault(
                key,
                {
                    'id': key,
                    'source': function['source'],
                    'route_type': 'discrete_family_WRC',
                    'basis': target['quantity'],
                    'members': [],
                    'interpolation': 'linear water content in log10(kPa) between positive native coordinates only',
                    'zero_pressure': 'exact zero coordinate only; no interpolation between zero and first positive point',
                    'minimum_valid_native_coordinates': 3,
                    'extrapolation': 'forbidden',
                },
            )
            family['members'].append({'function': function['id'], 'target': target})
    for family in families.values():
        family['native_pressures_kpa'] = sorted(
            {m['target']['pressure_kpa'] for m in family['members']}
        )
        family['can_form_full_wrc'] = len(family['native_pressures_kpa']) >= 3
    adapters = {
        name: {
            **record,
            'route_type': 'parameter_derived_WRC',
            'basis': 'volumetric_water_content',
            'pressure_convention': 'nonnegative matric suction magnitude; h_cm=p_kpa/0.0980665',
            'pressure_domain_kpa': record.get('pressure_domain_kpa', [0, None]),
            'extrapolation': 'Only the explicit registered model domain; E5 application, no empirical validation claim.',
        }
        for name, record in PARAMETER_ADAPTERS.items()
    }
    return {'families': families, 'adapters': adapters, 'unresolved': UNRESOLVED}


def interpolate_native(native: list[tuple[float, float]], pressure: float) -> float:
    """Never turn zero suction into an arbitrary finite logarithmic coordinate."""
    points = sorted(native)
    if len({p for p, _ in points}) != len(points):
        message = 'Native family pressures must be unique.'
        raise ValueError(message)
    for p, value in points:
        if math.isclose(p, pressure, rel_tol=1e-12, abs_tol=1e-14):
            return value
    for (low, left), (high, right) in pairwise(points):
        if 0 < low < pressure < high:
            return left + (right - left) * math.log(pressure / low) / math.log(high / low)
    message = 'Pressure outside native positive interpolation support.'
    raise ValueError(message)


def supporting_pressures(pressures: list[float], pressure: float) -> list[float]:
    """Identify only native coordinates that actually contribute to a scored value."""
    for p in pressures:
        if math.isclose(p, pressure, rel_tol=1e-12, abs_tol=1e-14):
            return [p]
    for low, high in pairwise(sorted(pressures)):
        if 0 < low < pressure < high:
            return [low, high]
    message = 'Scored pressure has no native support.'
    raise ValueError(message)


def parameter_curve(adapter: str, parameters: dict, pressure: float) -> float:
    """Evaluate only formulas explicitly retained in the repository specifications."""
    if not math.isfinite(pressure) or pressure < 0:
        message = 'Suction must be finite and nonnegative.'
        raise ValueError(message)
    if adapter == 'calc_ptf_vereecken1989_detailed':
        r, s, a, n = (parameters[k] for k in ('theta_r', 'theta_s', 'alpha', 'n'))
        if not 0 <= r < s <= 1 or min(a, n) <= 0:
            message = 'Nonphysical m=1 van Genuchten parameters.'
            raise ValueError(message)
        if pressure == 0:
            return s
        exponent = n * math.log(a * pressure * HEAD_PER_KPA)
        effective = (
            math.exp(-exponent) / (1 + math.exp(-exponent))
            if exponent >= 0
            else 1 / (1 + math.exp(exponent))
        )
        return r + (s - r) * effective
    if adapter == 'calc_ptf_saxton1986_calcptf_parameters':
        r, s, a, shape = (
            parameters[k] for k in ('theta_r', 'theta_s', 'alpha', 'conductivity_lambda')
        )
        if not 0 <= r < s <= 1 or min(a, shape) <= 0:
            message = 'Nonphysical Brooks-Corey parameters.'
            raise ValueError(message)
        return (
            s
            if a * pressure * HEAD_PER_KPA <= 1
            else r + (s - r) * (a * pressure * HEAD_PER_KPA) ** (-shape)
        )
    if adapter == 'calc_ptf_saxton2006_tension_dry':
        low, high = parameters['theta_1500'], parameters['theta_33']
        if not 33 <= pressure <= 1500 or not 0 < low < high < 1:
            message = 'Dry Saxton inversion requires 33<=p<=1500 and ordered predicted anchors.'
            raise ValueError(message)
        exponent = math.log(1500 / 33) / math.log(high / low)
        return high * (pressure / 33) ** (-1 / exponent)
    if adapter == 'calc_ptf_saxton2006_tension_wet':
        entry, high, saturated = (
            parameters[k] for k in ('air_entry_tension', 'theta_33', 'theta_s')
        )
        if not 0 <= pressure <= 33 or not 0 <= entry < 33 or not 0 < high < saturated < 1:
            message = 'Wet Saxton inversion requires p<=33 and physical predicted anchors.'
            raise ValueError(message)
        return (
            saturated
            if pressure <= entry
            else high + (33 - pressure) * (saturated - high) / (33 - entry)
        )
    message = 'No explicit parameter curve is registered.'
    raise ValueError(message)
