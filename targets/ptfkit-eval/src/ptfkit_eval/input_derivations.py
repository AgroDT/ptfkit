"""Source-specific verified predictor derivations; no generic imputation permission."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType


COSBY_MIDPOINT_METHOD = 'cosby1984_table2_class_midpoint_v1'
# Cosby et al. (1984), Table 2. Order is sand, silt, clay, mass percent.
COSBY_CLASS_MIDPOINTS = MappingProxyType(
    {
        'sand': (92, 5, 3),
        'loamy sand': (82, 12, 6),
        'sandy loam': (58, 32, 10),
        'loam': (43, 39, 18),
        'silt loam': (17, 70, 13),
        'sandy clay loam': (58, 15, 27),
        'clay loam': (32, 34, 34),
        'silty clay loam': (10, 56, 34),
        'sandy clay': (52, 6, 42),
        'silty clay': (6, 47, 47),
        'clay': (22, 20, 58),
    }
)


def requires_registered_derivation(binding: Mapping[str, object]) -> bool:
    """Identify predictors whose method itself requires a source derivation proof."""
    measurement = binding.get('measurement')
    return isinstance(measurement, Mapping) and measurement.get('method') == COSBY_MIDPOINT_METHOD


def verify_input_derivation(
    function: Mapping[str, object],
    features: Mapping[object, Mapping[str, object]],
    bindings: Mapping[str, object],
) -> bool:
    """Verify one shared reviewed USDA class and all three exact Table-2 coordinates."""
    if function['id'] != 'calc_ptf_cosby1984_univariate':
        return False
    coordinates = []
    source_ids = set()
    for component in ('sand', 'silt', 'clay'):
        feature = features.get(bindings.get(component))
        proof = _coordinate_proof(feature)
        if proof is None:
            return False
        value, source_id = proof
        source_ids.add(source_id)
        coordinates.append(value)
    if len(source_ids) != 1:
        return False
    source = features.get(next(iter(source_ids)))
    if (
        source is None
        or source.get('kind') != 'categorical'
        or source.get('review_status') != 'confirmed'
        or source.get('origin') not in ('measured', 'synthetic')
        or source.get('category_system') != 'clapp1978.UsdaTextureClass'
    ):
        return False
    texture = source.get('value')
    return isinstance(texture, str) and tuple(coordinates) == COSBY_CLASS_MIDPOINTS.get(texture)


def _coordinate_proof(feature: Mapping[str, object] | None) -> tuple[float, str] | None:
    if (
        feature is None
        or feature.get('origin') != 'derived'
        or feature.get('review_status') != 'confirmed'
        or feature.get('kind') != 'numeric'
    ):
        return None
    derivation = feature.get('derivation')
    measurement = feature.get('measurement')
    if (
        not isinstance(derivation, Mapping)
        or derivation.get('method') != COSBY_MIDPOINT_METHOD
        or not isinstance(derivation.get('source_feature'), str)
        or not isinstance(measurement, Mapping)
        or measurement.get('unit') != 'mass_percent'
    ):
        return None
    value = feature.get('value')
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value), derivation['source_feature']
