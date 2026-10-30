"""Same-record E5 predictor recovery without numerical imputation."""

# ruff: noqa: INP001, C901, PLR0912, PLR0915, PLR2004 - Explicit evidence branches.

from __future__ import annotations

import math
import re

from ptfkit_eval.execution import convert_value
from ptfkit_eval.harmonization import _usda_class

from evaluation.experiments.meta_v3_3 import campaign_contracts as contracts
from evaluation.experiments.meta_v3_3 import campaign_inputs as inputs
from evaluation.experiments.meta_v3_3 import workbook_semantic as semantic
from evaluation.experiments.meta_v3_3.source_domains import within_named_domain


def psd_fraction(bins: dict, low: float, high: float) -> tuple[float, list[str]]:
    """Integrate complete observed bins; split positive bins in log diameter."""
    contributions, sources, intervals = [], [], []
    for (left, right), value, cells in zip(
        bins['intervals_um'], bins['values'], bins['sources'], strict=True
    ):
        a, b = max(low, left), min(high, right)
        if a >= b:
            continue
        if not semantic.numeric(value) or not 0 <= value <= 100:
            message = 'Required PSD bin is unobserved or physically invalid.'
            raise ValueError(message)
        if a == left and b == right:
            fraction = 1
        elif left > 0:
            fraction = math.log(b / a) / math.log(right / left)
        else:
            message = (
                'Cannot interpolate an unobserved positive lower tail within a zero-ended PSD bin.'
            )
            raise ValueError(message)
        contributions.append(value * fraction)
        intervals.append((a, b))
        sources.extend(cells)
    cursor = low
    for a, b in sorted(intervals):
        if not math.isclose(cursor, a, abs_tol=1e-10):
            message = 'Requested PSD interval has an unobserved gap.'
            raise ValueError(message)
        cursor = b
    if not math.isclose(cursor, high, abs_tol=1e-10):
        message = 'Requested PSD interval extends beyond observed bins.'
        raise ValueError(message)
    return math.fsum(contributions), sorted(set(sources))


def recovered_texture(row: dict) -> dict:
    """Preserve reported fractions; close only one missing component."""
    values = {}
    for name, column in (('sand', 'P'), ('silt', 'O'), ('clay', 'N')):
        value = row['values'].get(column)
        if semantic.numeric(value) and 0 <= value <= 100:
            values[name] = (
                float(value),
                list(row['value_cells'][column]),
                {'original_column': column, 'original_clay_upper_um': row['clay_upper_um']},
            )
    if 'clay' not in values:
        physical = row['values'].get('M')
        if semantic.numeric(physical) and 0 <= physical <= 100:
            values['clay'] = (
                float(physical),
                list(row['value_cells']['M']),
                {
                    'original_interval_um': [0, 10],
                    'requested_interval_um': [0, 2],
                    'cutoff_mismatch_approximation': True,
                },
            )
    if len(values) == 2:
        remainder = 100 - math.fsum(v[0] for v in values.values())
        if remainder >= 0:
            missing = next(iter({'sand', 'silt', 'clay'} - values.keys()))
            values[missing] = (
                remainder,
                sorted({c for v in values.values() for c in v[1]}),
                {
                    'formula': '100 - other two observed/proxy fractions',
                    'parents': {k: v[2] for k, v in values.items()},
                    'approximation': True,
                },
            )
    if len(values) == 3:
        total = math.fsum(v[0] for v in values.values())
        if total > 0 and abs(total - 100) <= 1 and total != 100:
            values = {
                k: (v[0] * 100 / total, v[1], {**v[2], 'closure_scale': 100 / total})
                for k, v in values.items()
            }
    return values


def resolve(
    function: dict, sample: dict, row: dict, context: dict, axis: set[str] | None = None
) -> tuple[dict, dict, list[str]]:
    """Retry missing aliases and cutoffs, preserving explicit same-row provenance."""
    axis = axis or set()
    values, proofs, _ = semantic.semantic_inputs(function, sample, row, context, {}, axis)
    texture = recovered_texture(row)
    for binding in function['inputs']:
        name = binding['name']
        if name in axis:
            continue
        item, unit, detail = None, None, {}
        component = name.removesuffix('_content')
        if component in texture and component in ('sand', 'silt', 'clay'):
            # Replace a fallback from 100-physical_clay only with independent
            # reported fractions or registered closure, never a fitted predictor.
            item, cells, detail = texture[component]
            unit = 'mass_percent'
        elif row.get('psd_bins') and (
            inputs.interval(binding) or re.fullmatch(r'particle_\d+_\d+', name)
        ):
            bounds = inputs.interval(binding)
            if bounds is None:
                bounds = tuple(sorted(float(v) for v in name.split('_')[1:]))
            try:
                item, cells = psd_fraction(row['psd_bins'], *bounds)
                unit = 'mass_percent'
                detail = {
                    'requested_interval_um': bounds,
                    'original_intervals_um': row['psd_bins']['intervals_um'],
                    'original_values': row['psd_bins']['original_values'],
                    'formula': 'observed bin sum with log-diameter subdivision',
                    'approximation': True,
                }
            except ValueError:
                pass
        elif name == 'particle_density' and name not in values:
            bulk, porosity = row['values'].get('Q'), row['properties'].get('porosity')
            if semantic.numeric(bulk) and porosity and 0 < porosity.value < 1:
                item = bulk / (1 - porosity.value)
                cells = [*row['value_cells']['Q'], *porosity.sources]
                unit = 'gram_per_cubic_centimeter'
                detail = {
                    'formula': 'particle_density = bulk_density/(1-porosity)',
                    'observed_porosity': porosity.value,
                }
        elif (
            binding.get('type') == 'enum'
            and binding.get('_ref_type') == 'UsdaTextureClass'
            and len(texture) == 3
        ):
            fractions = [texture[k][0] for k in ('sand', 'silt', 'clay')]
            if math.isclose(sum(fractions), 100, abs_tol=1e-8):
                item = _usda_class(*fractions)
                cells = sorted({c for v in texture.values() for c in v[1]})
                detail = {
                    'formula': 'USDA class from same-record approximate PSD',
                    'cutoff_approximation': True,
                }
        if item is not None:
            try:
                native_unit = contracts.canonical_input_unit(binding)
                if binding.get('type') == 'enum':
                    converted = item
                else:
                    if unit is None or native_unit is None:
                        continue
                    converted = convert_value(float(item), unit, native_unit)
                values[name] = converted
                proofs[name] = {
                    'value': converted,
                    'tier': 'approximate',
                    'policy': 'expanded_same_record_recovery_v1',
                    'sources': cells,
                    'details': detail,
                    'parents': [],
                    'native_unit': binding.get('unit'),
                }
            except (ValueError, TypeError):
                pass
    reasons = []
    for binding in function['inputs']:
        name = binding['name']
        if name in axis:
            continue
        if name not in values:
            reasons.append('missing_predictor:' + name)
        elif not within_named_domain(
            binding.get('domain') or '', {**values, 'value': values[name]}
        ) or not inputs.legacy_domain(values[name], binding):
            reasons.append('computational_domain:' + name)
    return values, proofs, sorted(set(reasons))


def water_convert(
    value: float, original_basis: str, target_basis: str, row: dict
) -> tuple[float, dict | None]:
    """Convert water content only using a positive actual same-record bulk density."""
    if original_basis == target_basis:
        return value, None
    density = row['values'].get('Q')
    if not semantic.numeric(density) or not 0 < density < 10:
        message = 'Water basis conversion requires observed same-record bulk density.'
        raise ValueError(message)
    converted = value / density if target_basis.startswith('gravimetric') else value * density
    return converted, {
        'policy': 'same_sample_water_basis_conversion',
        'bulk_density_g_cm3': density,
        'sources': row['value_cells']['Q'],
        'water_density_g_cm3': 1.0,
        'original_basis': original_basis,
        'target_basis': target_basis,
    }
